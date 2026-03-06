# QA Report #09 — ИНСТРУКЦИИ ДЛЯ ФИКСИНГА v1.7

**Проект:** ResumeCraft
**Дата:** 2026-03-06
**Приоритет:** CRITICAL — выполнять сверху вниз

---

## FIX-001 — 🔴 CRITICAL: Перенести ВСЕ настройки из localStorage в БД

### Проблема
API-ключи LLM-провайдеров (GigaChat, OpenAI, Anthropic, OpenRouter) хранятся в `localStorage` браузера в открытом виде. Любой XSS-вектор, расширение браузера или злоумышленник с физическим доступом может украсть все ключи.

Дополнительно: в localStorage хранятся аватары других пользователей, настройки AI-моделей, субмодели и прочие данные, которые должны быть на сервере.

### Что сделать

#### 1. Создать таблицу `user_settings` в БД

```sql
CREATE TABLE user_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL,         -- 'ai_models', 'profile', 'notifications', 'ui'
    key VARCHAR(100) NOT NULL,             -- 'gigachat_api_key', 'openai_api_key', 'default_model' и т.д.
    value TEXT,                            -- зашифрованное значение для ключей, plain для остального
    is_encrypted BOOLEAN DEFAULT FALSE,     -- TRUE для API-ключей
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, category, key)
);

CREATE INDEX idx_user_settings_user ON user_settings(user_id);
CREATE INDEX idx_user_settings_category ON user_settings(user_id, category);
```

#### 2. Шифрование API-ключей на сервере

```python
# backend/app/core/encryption.py
from cryptography.fernet import Fernet
from app.core.config import settings

# Генерировать один раз и хранить в .env как ENCRYPTION_KEY
fernet = Fernet(settings.ENCRYPTION_KEY)

def encrypt_value(value: str) -> str:
    return fernet.encrypt(value.encode()).decode()

def decrypt_value(encrypted: str) -> str:
    return fernet.decrypt(encrypted.encode()).decode()
```

#### 3. API-эндпоинты для настроек

```python
# backend/app/api/v1/settings.py

@router.get("/settings/ai-keys")
async def get_ai_keys(current_user: User = Depends(get_current_user)):
    """Возвращает ТОЛЬКО маски ключей, никогда полные значения"""
    keys = await get_user_settings(current_user.id, category="ai_models")
    return {
        "gigachat": mask_key(decrypt(keys.get("gigachat_api_key", ""))),
        "openai": mask_key(decrypt(keys.get("openai_api_key", ""))),
        "anthropic": mask_key(decrypt(keys.get("anthropic_api_key", ""))),
        "openrouter": mask_key(decrypt(keys.get("openrouter_api_key", "")))
    }

def mask_key(key: str) -> str:
    """sk-proj-abc123xyz → ●●●●●●●●xyz"""
    if not key or len(key) < 8:
        return ""
    return "●" * (len(key) - 4) + key[-4:]

@router.put("/settings/ai-keys/{provider}")
async def update_ai_key(
    provider: str,
    body: AIKeyUpdate,
    current_user: User = Depends(get_current_user)
):
    """Сохраняет ключ ТОЛЬКО в БД в зашифрованном виде"""
    encrypted = encrypt_value(body.api_key)
    await upsert_user_setting(
        user_id=current_user.id,
        category="ai_models",
        key=f"{provider}_api_key",
        value=encrypted,
        is_encrypted=True
    )
    return {"status": "saved", "masked": mask_key(body.api_key)}
```

#### 4. Фронтенд — убрать ВСЕ ключи из localStorage

```typescript
// УДАЛИТЬ из фронтенда:
// - localStorage.setItem('ai_settings', ...)
// - localStorage.getItem('ai_settings')
// - Все обращения к localStorage для хранения настроек AI

// ЗАМЕНИТЬ на API-запросы:
const getAIKeys = () => api.get('/settings/ai-keys');
const updateAIKey = (provider: string, key: string) =>
  api.put(`/settings/ai-keys/${provider}`, { api_key: key });
```

#### 5. Полная очистка localStorage при logout

```typescript
// В функции logout:
const logout = () => {
  // Очистить ВСЕ данные
  localStorage.clear();
  // Или точечно:
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('ai_settings');
  localStorage.removeItem('user_avatar_*'); // все аватары
  // Редирект на логин
  navigate('/login');
};
```

#### 6. НЕ хранить в localStorage (чек-лист)

| Данные | Было | Должно быть |
|--------|------|-------------|
| API-ключи LLM | localStorage (plaintext) | БД (зашифровано) |
| Настройки AI-моделей | localStorage | БД (user_settings) |
| Выбранная модель | localStorage | БД (user_settings) |
| Субмодель | localStorage | БД (user_settings) |
| Аватар пользователя | localStorage (base64, 134KB!) | Файловое хранилище + URL |
| Аватары чужих пользователей | localStorage (!!!) | УДАЛИТЬ |
| Access token | localStorage | httpOnly cookie (идеально) или localStorage (допустимо) |
| Refresh token | localStorage | httpOnly cookie (обязательно!) |

### Критерий приёмки
- [ ] `localStorage` не содержит API-ключей
- [ ] `localStorage` не содержит настроек AI
- [ ] `localStorage` не содержит аватаров чужих пользователей
- [ ] API `GET /settings/ai-keys` возвращает только маски
- [ ] API-ключи зашифрованы в БД
- [ ] При logout вызывается `localStorage.clear()`

---

## FIX-002 — 🔴 CRITICAL: Починить LLM-провайдеры (оптимизация не работает)

### Проблема
При запуске оптимизации резюме: "API-ключ не настроен. Все LLM-провайдеры временно недоступны". Основная функция сервиса нерабочая.

### Причина (предположение)
После FIX-001 (перенос в БД) бэкенд должен читать ключи из БД, а не из localStorage/фронтенда. Сейчас ключи есть в localStorage фронта, но бэкенд их не видит.

### Что сделать

1. **Бэкенд: при оптимизации брать ключи из БД**

```python
# backend/app/services/optimization.py
async def get_llm_client(user_id: UUID, provider: str):
    """Получить клиент LLM с ключом из БД"""
    encrypted_key = await get_user_setting(
        user_id=user_id,
        category="ai_models",
        key=f"{provider}_api_key"
    )
    if not encrypted_key:
        raise HTTPException(400, f"API-ключ для {provider} не настроен")

    api_key = decrypt_value(encrypted_key)

    if provider == "gigachat":
        return GigaChatClient(api_key=api_key)
    elif provider == "openai":
        return OpenAIClient(api_key=api_key)
    # ... и т.д.
```

2. **Проверка ключей до начала оптимизации**

```python
@router.post("/optimize")
async def optimize_resume(
    request: OptimizeRequest,
    current_user: User = Depends(get_current_user)
):
    # Проверить наличие ключа ДО начала процесса
    provider = request.model_provider
    key = await get_user_setting(current_user.id, "ai_models", f"{provider}_api_key")
    if not key:
        raise HTTPException(
            400,
            detail=f"API-ключ для {provider} не настроен. "
                   f"Перейдите в Настройки → AI-модели для настройки."
        )
    # ... продолжить оптимизацию
```

3. **Wizard: проверка моделей перед шагом выбора (LIVE-008)**

```typescript
// Перед показом страницы выбора модели:
const availableModels = await api.get('/settings/available-models');
// Показать только модели с настроенными ключами
// Если ни одна модель не доступна — показать предупреждение с ссылкой на настройки
```

### Критерий приёмки
- [ ] Оптимизация резюме работает (хотя бы с одним провайдером)
- [ ] При отсутствии ключа — понятная ошибка ДО начала обработки
- [ ] Wizard показывает только доступные модели

---

## FIX-003 — 🟠 HIGH: Добавить экспорт резюме в 3 форматах

### Проблема
Нет функционала экспорта оптимизированного резюме в файл. Пользователь не может скачать результат.

### Что сделать

#### 1. Backend — API-эндпоинты экспорта

```python
# backend/app/api/v1/resumes.py

@router.get("/resumes/{resume_id}/export/{format}")
async def export_resume(
    resume_id: UUID,
    format: Literal["pdf", "docx", "txt"],
    current_user: User = Depends(get_current_user)
):
    """Экспорт резюме в PDF, DOCX или TXT"""
    resume = await get_resume_by_id(resume_id, current_user.id)
    if not resume:
        raise HTTPException(404, "Резюме не найдено")

    if format == "pdf":
        content = await generate_pdf(resume)
        media_type = "application/pdf"
        filename = f"resume_{resume.id}.pdf"
    elif format == "docx":
        content = await generate_docx(resume)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = f"resume_{resume.id}.docx"
    elif format == "txt":
        content = await generate_txt(resume)
        media_type = "text/plain"
        filename = f"resume_{resume.id}.txt"

    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
```

#### 2. Генерация файлов

```python
# backend/app/services/export.py
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph
from docx import Document

async def generate_pdf(resume) -> bytes:
    """Генерация PDF из данных резюме"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    # Стилизованный PDF с форматированием
    # Заголовки, секции, контактная информация
    doc.build(elements)
    return buffer.getvalue()

async def generate_docx(resume) -> bytes:
    """Генерация DOCX из данных резюме"""
    doc = Document()
    doc.add_heading(resume.full_name, 0)
    # Секции резюме с форматированием
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()

async def generate_txt(resume) -> bytes:
    """Генерация plain text"""
    text = f"{resume.full_name}\n{'='*40}\n\n"
    text += resume.optimized_content or resume.original_content
    return text.encode('utf-8')
```

#### 3. Зависимости

```
# requirements.txt — добавить:
reportlab>=4.0
python-docx>=1.0
```

#### 4. Frontend — UI кнопки экспорта

На странице резюме (просмотр и результат оптимизации) добавить кнопки:

```tsx
// components/ResumeExport.tsx
const ExportButtons = ({ resumeId }: { resumeId: string }) => {
  const handleExport = async (format: 'pdf' | 'docx' | 'txt') => {
    const response = await api.get(
      `/resumes/${resumeId}/export/${format}`,
      { responseType: 'blob' }
    );
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.download = `resume.${format}`;
    link.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="export-buttons">
      <h3>Экспорт резюме</h3>
      <button onClick={() => handleExport('pdf')}>
        📄 Скачать PDF
      </button>
      <button onClick={() => handleExport('docx')}>
        📝 Скачать DOCX
      </button>
      <button onClick={() => handleExport('txt')}>
        📃 Скачать TXT
      </button>
    </div>
  );
};
```

### Критерий приёмки
- [ ] На странице резюме есть 3 кнопки: PDF, DOCX, TXT
- [ ] PDF скачивается с форматированием (заголовки, секции)
- [ ] DOCX скачивается с форматированием
- [ ] TXT скачивается как plain text
- [ ] Экспорт работает как для исходного, так и для оптимизированного резюме

---

## FIX-004 — 🟠 HIGH: Просмотр резюме с форматированием + вьюеры PDF/DOCX

### Проблема
При загрузке резюме в формате PDF или DOCX — нет предпросмотра с сохранением форматирования. Пользователь не видит, как выглядит его загруженное резюме.

### Что сделать

#### 1. Backend — извлечение текста с форматированием

```python
# backend/app/services/resume_parser.py
import fitz  # PyMuPDF для PDF
from docx import Document

async def parse_pdf(file_path: str) -> dict:
    """Извлечь текст и структуру из PDF"""
    doc = fitz.open(file_path)
    blocks = []
    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        blocks.append({
                            "text": span["text"],
                            "font_size": span["size"],
                            "is_bold": "Bold" in span["font"],
                            "is_italic": "Italic" in span["font"],
                        })
    return {"blocks": blocks, "page_count": len(doc)}

async def parse_docx(file_path: str) -> dict:
    """Извлечь текст и структуру из DOCX"""
    doc = Document(file_path)
    blocks = []
    for para in doc.paragraphs:
        blocks.append({
            "text": para.text,
            "style": para.style.name,  # Heading 1, Normal, etc.
            "is_bold": para.runs[0].bold if para.runs else False,
            "alignment": str(para.alignment),
        })
    return {"blocks": blocks}
```

#### 2. API-эндпоинт для получения форматированного содержимого

```python
@router.get("/resumes/{resume_id}/formatted")
async def get_formatted_resume(
    resume_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Вернуть содержимое резюме с форматированием как HTML"""
    resume = await get_resume_by_id(resume_id, current_user.id)
    # Преобразовать блоки в HTML для рендеринга на фронте
    html_content = blocks_to_html(resume.parsed_blocks)
    return {"html": html_content, "original_format": resume.file_format}
```

#### 3. Frontend — PDF-вьюер

```tsx
// Использовать react-pdf для встроенного просмотра PDF
import { Document, Page } from 'react-pdf';

const PDFViewer = ({ resumeId }: { resumeId: string }) => {
  const pdfUrl = `/api/v1/resumes/${resumeId}/file`;

  return (
    <div className="pdf-viewer">
      <Document file={pdfUrl}>
        <Page pageNumber={1} />
      </Document>
    </div>
  );
};
```

#### 4. Frontend — DOCX-вьюер

```tsx
// Использовать mammoth.js для рендеринга DOCX в HTML
import mammoth from 'mammoth';

const DocxViewer = ({ resumeId }: { resumeId: string }) => {
  const [html, setHtml] = useState('');

  useEffect(() => {
    const loadDocx = async () => {
      const response = await api.get(`/resumes/${resumeId}/file`, {
        responseType: 'arraybuffer'
      });
      const result = await mammoth.convertToHtml({ arrayBuffer: response.data });
      setHtml(result.value);
    };
    loadDocx();
  }, [resumeId]);

  return <div className="docx-viewer" dangerouslySetInnerHTML={{ __html: html }} />;
};
```

#### 5. Frontend — универсальный компонент просмотра

```tsx
const ResumeViewer = ({ resume }) => {
  switch (resume.file_format) {
    case 'pdf':
      return <PDFViewer resumeId={resume.id} />;
    case 'docx':
      return <DocxViewer resumeId={resume.id} />;
    case 'txt':
      return <pre className="txt-viewer">{resume.content}</pre>;
    default:
      return <div className="formatted-view">{resume.content}</div>;
  }
};
```

### Зависимости

```
# Backend:
PyMuPDF>=1.23
python-docx>=1.0

# Frontend (package.json):
"react-pdf": "^7.0",
"mammoth": "^1.6"
```

### Критерий приёмки
- [ ] Загруженный PDF отображается с форматированием
- [ ] Загруженный DOCX отображается с форматированием
- [ ] Форматирование сохраняется: заголовки, жирный, курсив, списки
- [ ] Можно переключаться между "Исходное" и "Оптимизированное"

---

## FIX-005 — 🟠 HIGH: Добавить rate limiting

### Проблема
Нет rate limiting ни на одном эндпоинте. Возможен брутфорс паролей, DDoS, злоупотребление API.

### Что сделать

```python
# backend/app/core/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://redis:6379/1"
)

# Применить к эндпоинтам:
@router.post("/auth/login")
@limiter.limit("5/minute")  # 5 попыток логина в минуту
async def login(request: Request, ...):
    ...

@router.post("/auth/register")
@limiter.limit("3/minute")  # 3 регистрации в минуту
async def register(request: Request, ...):
    ...

@router.post("/optimize")
@limiter.limit("10/hour")  # 10 оптимизаций в час
async def optimize(request: Request, ...):
    ...

# Глобальный лимит для всех эндпоинтов
@app.middleware("http")
@limiter.limit("100/minute")
async def rate_limit_middleware(request, call_next):
    ...
```

### Критерий приёмки
- [ ] 6-й неудачный логин за минуту → 429 Too Many Requests
- [ ] 4-я регистрация за минуту → 429
- [ ] Ответ 429 содержит Retry-After header

---

## FIX-006 — 🟡 MEDIUM: Исправить мелкие UI-баги

### LIVE-001: Кнопка X в модальном окне

```tsx
// Убедиться что onClick работает на иконке X
<button
  onClick={(e) => { e.stopPropagation(); onClose(); }}
  className="modal-close"
  aria-label="Закрыть"
>
  <XIcon />
</button>
```

### LIVE-005: Убрать gpt-5.4

```typescript
// Удалить из списка моделей:
const AVAILABLE_MODELS = [
  { id: 'gigachat-pro', name: 'GigaChat Pro', provider: 'gigachat' },
  { id: 'gpt-4o', name: 'GPT-4o', provider: 'openai' },
  { id: 'gpt-4o-mini', name: 'GPT-4o Mini', provider: 'openai' },
  { id: 'claude-sonnet-4-5-20250929', name: 'Claude Sonnet 4.5', provider: 'anthropic' },
  // НЕ добавлять gpt-5.4 — такой модели не существует!
];
```

### LIVE-007: Email обрезается в профиле

```tsx
// Проверить CSS:
.email-field {
  width: 100%;              /* Не фиксированная ширина */
  text-overflow: ellipsis;  /* Многоточие если длинный */
  overflow: hidden;
  white-space: nowrap;
  min-width: 250px;         /* Минимальная ширина для email */
}

// ИЛИ проверить maxLength на input:
<input
  type="email"
  maxLength={255}  /* Не 20! */
  value={email}
/>
```

### LIVE-009: Расхождение счётчиков

```python
# Убедиться что Dashboard и Subscription используют ОДИН запрос:
# Считать только УСПЕШНЫЕ оптимизации
count = await db.scalar(
    select(func.count(Optimization.id))
    .where(Optimization.user_id == user_id)
    .where(Optimization.status == 'completed')  # Только успешные!
)
```

### Критерий приёмки
- [ ] Кнопка X закрывает модальное окно
- [ ] gpt-5.4 отсутствует в списке моделей
- [ ] Email отображается полностью
- [ ] Dashboard и Подписка показывают одинаковое число

---

## FIX-007 — 🟡 MEDIUM: Email-верификация и soft-delete

### Email-верификация

```python
@router.post("/auth/register")
async def register(body: RegisterRequest):
    user = await create_user(body)
    user.is_verified = False  # Не активирован!

    token = generate_verification_token(user.email)
    await send_verification_email(user.email, token)

    return {"message": "Проверьте почту для подтверждения аккаунта"}

@router.get("/auth/verify/{token}")
async def verify_email(token: str):
    email = verify_token(token)
    user = await get_user_by_email(email)
    user.is_verified = True
    return {"message": "Email подтверждён"}
```

### Soft-delete для резюме

```python
# В модели Resume:
class Resume(Base):
    ...
    deleted_at = Column(DateTime, nullable=True)  # NULL = не удалено

@router.delete("/resumes/{id}")
async def delete_resume(id: UUID, current_user: User = ...):
    resume = await get_resume(id, current_user.id)
    resume.deleted_at = datetime.utcnow()  # Soft-delete
    await db.commit()
    return {"message": "Резюме перемещено в корзину"}

@router.post("/resumes/{id}/restore")
async def restore_resume(id: UUID, current_user: User = ...):
    resume = await get_resume(id, current_user.id, include_deleted=True)
    resume.deleted_at = None
    await db.commit()
    return {"message": "Резюме восстановлено"}
```

---

## FIX-008 — 🟡 MEDIUM: Прочие исправления

### LIVE-006: Старые ошибки "LLM-провайдер all"
```sql
-- Миграция: обновить старые записи
UPDATE optimization_history
SET error_message = REPLACE(error_message, 'LLM-провайдер all', 'Все LLM-провайдеры')
WHERE error_message LIKE '%LLM-провайдер all%';
```

### LIVE-013: Email enumeration
```python
# Единый ответ на register:
@router.post("/auth/register", status_code=200)  # Всегда 200!
async def register(body: RegisterRequest):
    try:
        await create_user(body)
    except DuplicateEmailError:
        pass  # Не раскрывать
    return {"message": "Если email свободен, вы получите письмо для подтверждения"}
```

### NEW-007: Убрать "Скоро" placeholder-ы
```tsx
// Скрыть нереализованные секции или вынести в /roadmap
// Удалить из страницы Безопасности:
// - "Двухфакторная аутентификация — Скоро"
// - "Активные сессии — Скоро"
```

---

## Чек-лист полной проверки после фиксинга

### Безопасность
- [ ] localStorage не содержит API-ключей
- [ ] localStorage не содержит настроек AI-моделей
- [ ] localStorage не содержит аватаров других пользователей
- [ ] API-ключи зашифрованы в БД
- [ ] GET /settings/ai-keys возвращает только маски
- [ ] Rate limiting: 6-й логин за минуту → 429
- [ ] При logout — `localStorage.clear()`
- [ ] Email enumeration: одинаковый ответ для существующих и несуществующих

### Основной функционал
- [ ] Оптимизация резюме работает (GigaChat / OpenAI / Anthropic / OpenRouter)
- [ ] Wizard проверяет доступность моделей ДО начала
- [ ] Счётчик оптимизаций корректный
- [ ] История показывает корректные данные

### Экспорт
- [ ] Кнопка "Скачать PDF" — скачивает форматированный PDF
- [ ] Кнопка "Скачать DOCX" — скачивает форматированный DOCX
- [ ] Кнопка "Скачать TXT" — скачивает plain text
- [ ] Экспорт доступен на странице просмотра резюме

### Просмотр резюме
- [ ] Загруженный PDF отображается с форматированием
- [ ] Загруженный DOCX отображается с форматированием
- [ ] Текст рендерится корректно (заголовки, жирный, курсив)

### UI
- [ ] Кнопка X в модалке закрывает окно
- [ ] gpt-5.4 отсутствует в списке моделей
- [ ] Email отображается полностью (не обрезан)
- [ ] Dashboard и Подписка показывают одинаковое число оптимизаций
- [ ] Нет placeholder-ов "Скоро" в production

### API
- [ ] DELETE /resumes/{id} — soft-delete (deleted_at)
- [ ] POST /resumes/{id}/restore — восстановление
- [ ] Регистрация требует верификацию email

---

## Порядок выполнения

| Шаг | FIX | Приоритет | Оценка времени |
|-----|-----|-----------|---------------|
| 1 | FIX-001 | 🔴 CRITICAL | 4-6 часов |
| 2 | FIX-002 | 🔴 CRITICAL | 2-4 часа |
| 3 | FIX-005 | 🟠 HIGH | 1-2 часа |
| 4 | FIX-003 | 🟠 HIGH | 4-6 часов |
| 5 | FIX-004 | 🟠 HIGH | 4-6 часов |
| 6 | FIX-006 | 🟡 MEDIUM | 2-3 часа |
| 7 | FIX-007 | 🟡 MEDIUM | 3-4 часа |
| 8 | FIX-008 | 🟡 MEDIUM | 1-2 часа |
| **ИТОГО** | | | **~21-33 часа** |

---

## ДОПОЛНИТЕЛЬНЫЕ FIX-ы (обнаружены при расширенном ретесте)

---

## FIX-009 — 🔴 CRITICAL: Защитить DELETE аккаунта

### Проблема
`DELETE /api/v1/auth/me` удаляет аккаунт мгновенно, каскадно уничтожая все данные (резюме, историю, настройки). Нет подтверждения, нет soft-delete, нет периода восстановления. Возможна CSRF-атака.

### Что сделать

```python
# 1. Требовать пароль для подтверждения удаления
@router.delete("/auth/me")
async def delete_account(
    body: DeleteAccountRequest,  # {"password": "..."}
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Проверить пароль
    if not verify_password(body.password, current_user.hashed_password):
        raise HTTPException(403, "Неверный пароль")

    # Soft-delete с 30-дневным периодом восстановления
    current_user.deleted_at = datetime.utcnow()
    current_user.scheduled_deletion = datetime.utcnow() + timedelta(days=30)
    await db.commit()

    # Отправить email-уведомление
    await send_deletion_email(current_user.email, days=30)

    return {"message": "Аккаунт будет удалён через 30 дней. Вы можете отменить удаление, войдя в аккаунт."}

# 2. Celery-задача для окончательного удаления
@celery.task
def purge_deleted_accounts():
    """Запускать ежедневно — удалять аккаунты с истёкшим сроком"""
    cutoff = datetime.utcnow()
    accounts = db.query(User).filter(
        User.scheduled_deletion <= cutoff,
        User.deleted_at.isnot(None)
    ).all()
    for user in accounts:
        # Каскадное удаление
        db.delete(user)
    db.commit()
```

### Критерий приёмки
- [ ] DELETE /api/v1/auth/me без пароля → 422
- [ ] DELETE с неверным паролем → 403
- [ ] DELETE с верным паролем → soft-delete (deleted_at устанавливается)
- [ ] Через 30 дней — окончательное удаление
- [ ] При входе в soft-deleted аккаунт — предложение восстановить

---

## FIX-010 — 🟠 HIGH: Починить кнопку "Найти" в wizard

### Проблема
Кнопка "Найти" на странице поиска вакансий имеет `disabled: true` даже при заполненных полях. DOM-инспекция подтверждает `button.disabled = true`, `button.type = "submit"`.

### Что сделать

```tsx
// Проверить логику состояния кнопки
// Вероятно, проблема в валидации формы или state-management

const VacancySearch = () => {
  const [query, setQuery] = useState('');
  const [city, setCity] = useState('');

  // ИСПРАВИТЬ: Убедиться что состояние обновляется
  const isFormValid = query.trim().length > 0; // Город может быть необязательным

  return (
    <form onSubmit={handleSearch}>
      <input value={query} onChange={e => setQuery(e.target.value)} />
      <select value={city} onChange={e => setCity(e.target.value)}>...</select>
      <button type="submit" disabled={!isFormValid}>
        Найти
      </button>
    </form>
  );
};

// ПРОВЕРИТЬ:
// 1. Не блокируется ли кнопка из-за отсутствия выбранного резюме?
// 2. Не зависит ли от шага wizard (step validation)?
// 3. Нет ли race condition при смене города?
```

### Критерий приёмки
- [ ] При вводе должности → кнопка "Найти" активна
- [ ] Клик по "Найти" → запрос к API и отображение результатов
- [ ] API-параметр `text` (не `query`) передаётся корректно

---

## FIX-011 — 🟠 HIGH: Починить просмотр резюме

### Проблема
Кнопка просмотра (👁) на странице "Мои резюме" не реагирует на клик — нет модалки, навигации, сетевых запросов.

### Что сделать

```tsx
// Проверить onClick handler на кнопке просмотра
const ResumeActions = ({ resume }) => {
  const handleView = () => {
    // Вариант 1: Навигация
    navigate(`/app/resumes/${resume.id}`);

    // Вариант 2: Модальное окно
    setViewModalOpen(true);
    setSelectedResume(resume);
  };

  return (
    <button onClick={handleView} aria-label="Просмотр резюме">
      <EyeIcon />  {/* Проверить: onClick на кнопке или на иконке? */}
    </button>
  );
};

// ПРОВЕРИТЬ:
// 1. onClick привязан к button, а не к вложенному элементу?
// 2. Нет ли e.stopPropagation() где-то выше в DOM?
// 3. Роутер настроен для /app/resumes/:id?
```

### Критерий приёмки
- [ ] Клик по 👁 → открывается просмотр резюме
- [ ] Работает для TXT, PDF и DOCX
- [ ] Содержимое отображается с форматированием (связано с FIX-004)

---

## FIX-012 — 🟡 MEDIUM: Закрыть openapi.json + сделать историю кликабельной

### openapi.json

```python
# В main.py — отключить openapi.json в production
app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None if settings.ENVIRONMENT == "production" else "/openapi.json"
)
```

### История — кликабельные записи

```tsx
const HistoryItem = ({ item }) => (
  <div
    className="history-item cursor-pointer hover:bg-gray-50"
    onClick={() => navigate(`/app/history/${item.id}`)}
  >
    <h4>Оптимизация · {item.model_id}</h4>
    <p>{item.status === 'error' ? item.error_message : 'Успешно'}</p>
    <span>{formatDate(item.created_at)}</span>
  </div>
);

// Добавить страницу /app/history/:id с деталями:
// - Исходный текст
// - Результат оптимизации
// - Параметры (модель, вакансия)
// - Кнопки экспорта
```

### Ограничение моделей по плану

```python
@router.post("/rewrite")
async def rewrite(body: RewriteRequest, current_user: User = ...):
    # Проверить доступность модели для плана пользователя
    allowed_models = get_allowed_models(current_user.plan)
    if body.model_id not in allowed_models:
        raise HTTPException(403, f"Модель {body.model_id} недоступна на плане {current_user.plan}")
```

---

## Обновлённый порядок выполнения

| Шаг | FIX | Приоритет | Оценка |
|-----|-----|-----------|--------|
| 1 | FIX-009 | 🔴 CRITICAL | 2-3 часа |
| 2 | FIX-001 | 🔴 CRITICAL | 4-6 часов |
| 3 | FIX-002 | 🔴 CRITICAL | 2-4 часа |
| 4 | FIX-010 | 🟠 HIGH | 1-2 часа |
| 5 | FIX-011 | 🟠 HIGH | 2-3 часа |
| 6 | FIX-005 | 🟠 HIGH | 1-2 часа |
| 7 | FIX-003 | 🟠 HIGH | 4-6 часов |
| 8 | FIX-004 | 🟠 HIGH | 4-6 часов |
| 9 | FIX-012 | 🟡 MEDIUM | 2-3 часа |
| 10 | FIX-006 | 🟡 MEDIUM | 2-3 часа |
| 11 | FIX-007 | 🟡 MEDIUM | 3-4 часа |
| 12 | FIX-008 | 🟡 MEDIUM | 1-2 часа |
| **ИТОГО** | | | **~28-44 часа** |

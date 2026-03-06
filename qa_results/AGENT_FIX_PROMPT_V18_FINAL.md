# 🤖 AGENT FIX PROMPT — ResumeCraft v1.7 → v1.8 (ФИНАЛЬНЫЙ)

> **Этот промпт предназначен для AI-агента (кодера), который будет исправлять все найденные баги.**
> **Составлен на основе 13 QA-отчётов, 3 раундов тестирования, 23+ API-эндпоинтов, 17 страниц.**
> **Дата составления:** 2026-03-06

---

## КОНТЕКСТ ПРОЕКТА

**Проект:** ResumeCraft — AI-реврайтер резюме (https://resumecraft.ru/)
**Стек:** Python 3.11+, FastAPI, SQLAlchemy 2.x, React 19 + TypeScript, Vite 6
**БД:** PostgreSQL (предположительно)
**Очередь:** RabbitMQ (Celery)
**Текущая версия:** v1.7
**Тестовый аккаунт:** test_new@example.com / TestPass1231

### ИСТОРИЯ ИСПРАВЛЕНИЙ

- **v1.5 → v1.6:** исправлено 43 из 71 дефектов (статический анализ + живое тестирование)
- **v1.6 → v1.7:** исправлено ещё 12 дефектов (12 FIX-коммитов, +50 тестов, 516 backend passed)
- **v1.7 (текущая):** осталось **19 живых дефектов** (2 CRITICAL, 6 HIGH, 9 MEDIUM, 2 LOW)

---

## ⚠️ КРИТИЧЕСКИ ВАЖНО — НЕ ЛОМАЙ ТО, ЧТО РАБОТАЕТ!

Перед каждым фиксом убедись, что следующее по-прежнему работает:

| Функционал | Как проверить | Статус v1.7 |
|------------|---------------|-------------|
| Авторизация (JWT) | POST `/api/v1/auth/login` → 200, JSON body `{email, password}` | ✅ |
| Загрузка резюме | POST `/api/v1/resumes/upload` или `/resumes/from-text` → 201 | ✅ |
| Ручной ввод вакансии | POST `/api/v1/vacancies/manual` → 201 | ✅ |
| AI-оптимизация (Anthropic Claude) | POST `/api/v1/rewrite` → 202 → poll status → result | ✅ |
| Экспорт PDF | GET `/api/v1/export/{id}/pdf` → 200, `application/pdf` | ✅ |
| Экспорт DOCX | GET `/api/v1/export/{id}/docx` → 200, корректный MIME | ✅ |
| Rate limiting | 3-й неудачный логин → 429 | ✅ |
| API-ключи в БД | localStorage не содержит API-ключей | ✅ |
| `/openapi.json` закрыт | GET `/openapi.json` → 404 | ✅ |
| История кликабельна | Кнопка «Открыть» → `/app/results/{id}` | ✅ |
| Профиль сохраняется | PUT `/api/v1/auth/me` → 200 | ✅ |

**Если хоть один из этих тестов после твоих исправлений перестал работать — ты регрессировал. Откати и разберись.**

---

## ДЕФЕКТЫ ДЛЯ ИСПРАВЛЕНИЯ

Ниже 19 дефектов в порядке приоритета. Каждый содержит: проблему, доказательства, точное решение и acceptance criteria.

---

### 🔴 P0-1 | NEW-V17-001 | CRITICAL: Кнопка «Найти» не вызывает API

**Где:** Фронтенд, страница `/app/vacancy?resumeId=...`, вкладка «Поиск на hh.ru»

**Проблема:** Кнопка «Найти» при клике ничего не делает. Нет сетевого запроса, нет ошибки в консоли. `onClick` handler не подключён или вызывает неправильный endpoint.

**Доказательство из QA:**
```
✅ GET /api/v1/vacancies/search?text=Product+Manager&area=1 → 200 OK (вакансии возвращаются)
❌ GET /api/v1/vacancies/search?query=... → 422 (неправильный параметр)
❌ POST /api/v1/vacancies/search → 405 (неправильный метод)
❌ GET /api/v1/vacancies → 404 (несуществующий endpoint)
```

**Что сделать:**
1. Найти компонент поиска вакансий (VacancySearch.tsx, SearchTab.tsx или аналог)
2. В `onClick` или `onSubmit` кнопки «Найти» добавить вызов:
   ```typescript
   const searchVacancies = async () => {
     setLoading(true);
     try {
       const response = await api.get('/api/v1/vacancies/search', {
         params: {
           text: searchQuery,  // НЕ 'query', а 'text'!
           area: selectedAreaId // число (1 = Москва), НЕ строка города
         }
       });
       setVacancies(response.data);
     } catch (error) {
       setError('Ошибка поиска вакансий');
     } finally {
       setLoading(false);
     }
   };
   ```
3. Убедиться что маппинг городов: `{ "Москва": 1, "Санкт-Петербург": 2, ... }`
4. После получения результатов — отобразить список вакансий для выбора

**Acceptance criteria:**
- [ ] Ввести «Product Manager» + «Москва» → нажать «Найти» → список вакансий появляется
- [ ] Клик на вакансию → выбор → переход к выбору модели
- [ ] При пустом запросе — кнопка disabled или ошибка валидации
- [ ] Network tab: видно `GET /api/v1/vacancies/search?text=...&area=...`

---

### 🔴 P0-2 | NEW-V17-003 | CRITICAL→HIGH: Match Score показывает 1% вместо 77%

**Где:** Фронтенд, ВСЕ страницы с отображением Match Score

**Проблема:** API возвращает десятичные значения, фронтенд не умножает на 100.

**Доказательство из QA (API ответ):**
```json
{
  "match_score_before": 0.601,
  "match_score_after": 0.773,
  "ats_rating": "B+"
}
```

**UI показывает:**

| Страница | Элемент | Отображает | Должно быть |
|----------|---------|------------|-------------|
| `/app/dashboard` | Средний Match Score | **1%** | **77%** |
| `/app/results/{id}` | Match Score | **1%** | **77%** |
| `/app/results/{id}` | Улучшение | **+0 пунктов** | **+17 пунктов** |
| `/app/results/{id}` | Keywords | **1%** | расчётное |
| `/app/results/{id}` | Experience | **1%** | расчётное |
| `/app/results/{id}` | Structure | **1%** | расчётное |
| `/app/results/{id}` | Readability | **1%** | расчётное |
| `/app/export/{id}` | Match | **1%** | **77%** |
| `/app/history` | Match | **1% → 1%** | **60% → 77%** |

**Что сделать:**
1. Найти ВСЕ компоненты отображения Match Score (поиск по `match_score`, `matchScore`, `score`)
2. Применить формулу:
   ```typescript
   const displayScore = Math.round(rawScore * 100); // 0.773 → 77
   const improvement = Math.round((scoreAfter - scoreBefore) * 100); // 17
   ```
3. Проверить все 4 страницы: dashboard, results, export, history
4. Компоненты (Keywords, Experience, Structure, Readability):
   - Если бэкенд передаёт отдельные значения — умножить каждый на 100
   - Если не передаёт — рассчитать пропорционально: Keywords 40%, Experience 25%, Structure 20%, Readability 15% от общего score

**Acceptance criteria:**
- [ ] Dashboard: «Средний Match Score: 77%»
- [ ] Results: «Match Score: 77%», «Улучшение: +17 пунктов»
- [ ] History: «60% → 77%»
- [ ] Export: «Match: 77%»
- [ ] Компоненты показывают индивидуальные значения > 1%

---

### 🔴 P0-3 | NEW-V17-002 | HIGH: Результат оптимизации = RAW JSON

**Где:** Фронтенд, `/app/results/{task_id}`

**Проблема:** Вместо форматированного резюме пользователь видит сырой JSON: `{"summary":"...","experience":[...]}`.

**API ответ содержит два поля:**
- `rewritten_text` — plain text версия (с переносами строк)
- `rewritten_data` — структурированный JSON (секции summary, experience, education, skills)

**Что сделать:**
1. Найти компонент отображения результата (Results.tsx, RewriteResult.tsx или аналог)
2. Вместо `JSON.stringify(data)` или прямого вывода объекта — использовать один из вариантов:

**Вариант A (простой — использовать rewritten_text):**
```tsx
<div className="rewrite-result">
  {result.rewritten_text.split('\n').map((line, i) => (
    <p key={i}>{line || <br />}</p>
  ))}
</div>
```

**Вариант B (продвинутый — парсить rewritten_data):**
```tsx
const ResumeResult = ({ data }: { data: RewrittenData }) => (
  <div className="resume-result">
    {data.summary && (
      <section>
        <h3>Резюме</h3>
        <p>{data.summary}</p>
      </section>
    )}
    {data.experience?.map((exp, i) => (
      <section key={i}>
        <h3>{exp.title} — {exp.company}</h3>
        <p className="dates">{exp.dates}</p>
        <p>{exp.description}</p>
      </section>
    ))}
    {data.education?.map((edu, i) => (
      <section key={i}>
        <h3>{edu.institution}</h3>
        <p>{edu.degree}, {edu.year}</p>
      </section>
    ))}
    {data.skills && (
      <section>
        <h3>Навыки</h3>
        <p>{data.skills.join(', ')}</p>
      </section>
    )}
  </div>
);
```

3. Проверить Diff-сравнение (если есть): оригинал vs оптимизированный — оба должны быть текстом

**Acceptance criteria:**
- [ ] Результат оптимизации отображается как читаемый текст резюме с секциями
- [ ] Нет видимых `{`, `}`, `[`, `]` в UI
- [ ] Каждая секция (опыт, образование, навыки) визуально разделена

---

### 🔴 P0-4 | NEW-V17-004 | HIGH: OpenAI o-модели: max_tokens → max_completion_tokens

**Где:** Бэкенд, модуль LLM-провайдеров (llm_service.py, openai_provider.py или аналог)

**Проблема:** Модели OpenAI серии `o*` (o1, o1-mini, o3, o3-mini, o4-mini) не поддерживают параметр `max_tokens`, требуют `max_completion_tokens`.

**Полная ошибка из production:**
```
LLM-провайдер openai: Error code: 400 - {'error': {
  'message': "Unsupported parameter: 'max_tokens' is not supported with this model.
  Use 'max_completion_tokens' instead.",
  'type': 'invalid_request_error',
  'param': 'max_tokens'
}} временно недоступен
```

**Что сделать:**
```python
# В файле LLM-провайдера OpenAI (при формировании запроса):
def build_openai_params(model_name: str, base_params: dict) -> dict:
    params = base_params.copy()

    # O-серия моделей использует max_completion_tokens вместо max_tokens
    if model_name.startswith(('o1', 'o3', 'o4')):
        max_tokens_value = params.pop('max_tokens', 4096)
        params['max_completion_tokens'] = max_tokens_value
        # Также o-серия НЕ поддерживает temperature (всегда 1)
        params.pop('temperature', None)

    return params
```

**Важно:** НЕ сломать `gpt-4o`, `gpt-4o-mini`, `gpt-3.5-turbo` — они продолжают использовать `max_tokens`.

**Acceptance criteria:**
- [ ] Оптимизация через `openai:o4-mini` завершается успешно (без ошибки 400)
- [ ] Оптимизация через `openai:gpt-4o` по-прежнему работает
- [ ] В логах нет `Unsupported parameter: 'max_tokens'`

---

### 🟠 P1-1 | NEW-V17-005 + NEW-008 | MEDIUM: Кнопка «Удалить аккаунт» не подключена к API

**Где:** Фронтенд `SecuritySettings.tsx` + Бэкенд `auth_router.py`

**Проблема:** Кнопка «Удалить аккаунт» на `/app/settings/security` при клике ничего не делает. Нет модального окна, нет DELETE-запроса, нет ошибки. В v1.6 была проблема каскадного удаления без подтверждения — сейчас handler просто не подключён.

**Дополнительно:** Текст «Опасная зона» обрезан: «Вы можете » — предложение не завершено (NEW-V17-TRUNC).

**Что сделать:**

**Фронтенд:**
```tsx
const handleDeleteAccount = async () => {
  // 1. Показать модальное окно подтверждения
  setShowDeleteModal(true);
};

const confirmDeleteAccount = async (password: string) => {
  try {
    await api.delete('/api/v1/auth/me', {
      data: { password }
    });
    // 2. Очистить всё и редирект
    localStorage.clear();
    navigate('/auth');
    toast.success('Аккаунт помечен для удаления. Вы можете восстановить его в течение 30 дней.');
  } catch (error) {
    if (error.response?.status === 403) {
      toast.error('Неверный пароль');
    } else {
      toast.error('Ошибка удаления аккаунта');
    }
  }
};
```

**Модальное окно:**
```tsx
<Modal open={showDeleteModal} onClose={() => setShowDeleteModal(false)}>
  <h3>Удаление аккаунта</h3>
  <p>Вы уверены? Все данные будут безвозвратно удалены через 30 дней.</p>
  <p>Введите пароль для подтверждения:</p>
  <input type="password" value={deletePassword} onChange={e => setDeletePassword(e.target.value)} />
  <button onClick={() => confirmDeleteAccount(deletePassword)} variant="danger">
    Удалить аккаунт
  </button>
</Modal>
```

**Бэкенд** (проверить что soft-delete работает — FIX-009 из v1.7 должен был добавить):
```python
@router.delete("/auth/me")
async def delete_account(
    body: DeleteAccountRequest,  # {"password": "..."}
    current_user: User = Depends(get_current_user),
):
    if not verify_password(body.password, current_user.hashed_password):
        raise HTTPException(403, "Неверный пароль")

    current_user.deleted_at = datetime.utcnow()
    current_user.is_active = False
    await db.commit()

    return {"message": "Аккаунт помечен для удаления"}
```

**Текст «Опасная зона»** — дописать:
```
Было:    «Вы можете »
Должно:  «Вы можете отменить удаление в течение 30 дней, написав на support@resumecraft.ru»
```

**Acceptance criteria:**
- [ ] Клик «Удалить аккаунт» → модальное окно с вводом пароля
- [ ] Неверный пароль → ошибка «Неверный пароль»
- [ ] Верный пароль → soft-delete → разлогин → редирект на `/auth`
- [ ] API: `DELETE /api/v1/auth/me` без пароля → 422
- [ ] Текст «Опасная зона» полный, без обрезки

---

### 🟠 P1-2 | NEW-V17-006 + NEW-012 | MEDIUM: Тарифные планы — противоречия и отсутствие ограничений

**Где:** Фронтенд `/app/help` и `/app/settings/subscription` + бэкенд

**Проблема (2 в 1):**

**A) Противоречие текстов:**

| Функция | Справка (`/app/help`) | Подписка (`/app/settings/subscription`) | Реальное поведение |
|---------|----------------------|-----------------------------------------|-------------------|
| AI-модели (Free) | **Все модели** | **1 модель (GigaChat)** | **Все модели** |
| Экспорт (Free) | **PDF/DOCX** | **DOCX only** | **PDF + DOCX + hh.ru** |
| История (Free) | Не упоминается | Standard+ | **Доступна** |

**B) Ограничения не применяются:** Free-пользователь имеет доступ ко всем 4 провайдерам, всем моделям и всем форматам экспорта. Тариф не проверяется.

**Что сделать — ВЫБЕРИ ОДНУ СТРАТЕГИЮ:**

**Стратегия А (рекомендуется — оставить всё доступным, обновить текст Подписки):**
1. Обновить `/app/settings/subscription`: Free = «Все модели», «PDF/DOCX экспорт», «История»
2. Обновить `/app/help` чтобы совпадало
3. Разница между планами: Standard — 20 оптимизаций/мес + приоритетная поддержка, Pro — безлимит + API-доступ

**Стратегия Б (ограничить Free план):**
1. Бэкенд: проверять `user.plan` при вызове `/api/v1/rewrite` и `/api/v1/export`
   ```python
   PLAN_LIMITS = {
       "free": {"models": ["gigachat"], "exports": ["docx"], "optimizations": 5},
       "standard": {"models": ["gigachat", "openai", "anthropic"], "exports": ["docx", "pdf"], "optimizations": 20},
       "pro": {"models": "*", "exports": "*", "optimizations": float('inf')}
   }
   ```
2. Фронтенд: при попытке выбрать недоступную модель → «Обновите до Standard/Pro»
3. Обновить Справку и Подписку чтобы совпадали

**Acceptance criteria:**
- [ ] Справка и Подписка показывают одинаковые возможности для каждого плана
- [ ] Если выбрана стратегия Б: при Free + не-GigaChat модель → 403 с понятным сообщением

---

### 🟠 P1-3 | NEW-002 | HIGH: Рассинхрон UI/бэкенд по API-ключам провайдеров

**Где:** Фронтенд настройки AI (`/app/settings/ai`) + бэкенд `/api/v1/settings/ai-keys`

**Проблема:** UI показывает одно состояние (ключи настроены ✅), бэкенд может иметь другое. При сохранении ключа через UI — бэкенд может не получить его корректно, или наоборот — UI не отображает актуальное состояние с сервера.

**Что сделать:**
1. При загрузке `/app/settings/ai` — ВСЕГДА делать `GET /api/v1/settings/ai-keys` и отображать ответ сервера
2. При сохранении ключа — `PUT /api/v1/settings/ai-keys/{provider}` → после успеха перезагрузить состояние с сервера
3. Зелёная галочка ✅ только если сервер подтвердил наличие ключа (маска не пустая)
4. Тоглы (вкл/выкл провайдера) — `PUT /api/v1/settings/ai-toggles` → подтверждение с сервера

**Acceptance criteria:**
- [ ] Состояние ключей на UI = состояние в БД
- [ ] Сохранение ключа → зелёная галочка обновляется после ответа сервера
- [ ] Пустой ключ → серая иконка, не зелёная

---

### 🟠 P1-4 | LIVE-003 / NEW-V17-LOGIN | HIGH: Login только JSON (form-data → 422)

**Где:** Бэкенд `auth_router.py`, endpoint `POST /api/v1/auth/login`

**Проблема:** Login принимает только `Content-Type: application/json`. Отправка `application/x-www-form-urlencoded` или `multipart/form-data` → 422.

**Доказательство:**
```
POST /api/v1/auth/login  Content-Type: application/json         → 200 ✅
POST /api/v1/auth/login  Content-Type: application/x-www-form-urlencoded → 422 ❌
POST /api/v1/auth/login  Content-Type: multipart/form-data      → 422 ❌
```

**Что сделать:**
```python
from fastapi import Form

# Текущий (только JSON):
@router.post("/auth/login")
async def login(body: LoginRequest):  # Pydantic model from JSON
    ...

# Исправленный (JSON + form-data):
@router.post("/auth/login")
async def login(
    request: Request,
):
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        data = await request.json()
        email = data.get("email")
        password = data.get("password")
    elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        email = form.get("email") or form.get("username")  # OAuth2 compatibility
        password = form.get("password")
    else:
        raise HTTPException(415, "Unsupported Content-Type")

    # ... проверка credentials
```

**Или проще через FastAPI OAuth2PasswordRequestForm:**
```python
from fastapi.security import OAuth2PasswordRequestForm

@router.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    email = form_data.username
    password = form_data.password
    # ... проверка
```

**Acceptance criteria:**
- [ ] `POST /api/v1/auth/login` с JSON body → 200
- [ ] `POST /api/v1/auth/login` с form-data → 200
- [ ] Форма авторизации на `/auth` продолжает работать

---

### 🟠 P1-5 | LIVE-003 | HIGH: Просмотр резюме — plain text без форматирования

**Где:** Фронтенд, страница `/app/resumes/{id}` (просмотр загруженного резюме)

**Проблема:** При просмотре загруженного резюме отображается plain text без структуры. Нет заголовков, нет жирного/курсива, нет разделов.

**Что сделать:**
1. Если резюме загружено как PDF — использовать `react-pdf` для отображения:
   ```tsx
   import { Document, Page } from 'react-pdf';
   <Document file={`/api/v1/resumes/${id}/file`}>
     <Page pageNumber={1} />
   </Document>
   ```
2. Если DOCX — mammoth.js для конвертации в HTML (FIX-004 из v1.7 уже добавил mammoth):
   ```tsx
   import mammoth from 'mammoth';
   const result = await mammoth.convertToHtml({ arrayBuffer });
   <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(result.value) }} />
   ```
3. Если plain text — хотя бы сохранить переносы строк (`white-space: pre-wrap`)

**Acceptance criteria:**
- [ ] PDF-резюме отображается с форматированием (или как встроенный PDF)
- [ ] DOCX-резюме отображается с заголовками, жирным, курсивом
- [ ] Текстовое резюме сохраняет переносы строк

---

### 🟡 P2-1 | NEW-V17-007 + NEW-007 | MEDIUM: Поля «Скоро» в профиле

**Где:** Фронтенд `/app/settings/profile`

**Проблема:** 3 поля (телефон, текущая должность, о себе) показывают placeholder «Скоро» в production.

**Что сделать (выбери одно):**
- **Вариант A:** Скрыть поля до реализации (`display: none` или conditional render)
- **Вариант B:** Реализовать поля — сохранение через `PUT /api/v1/auth/me` (если бэкенд поддерживает эти поля)

**Acceptance criteria:**
- [ ] Нет текста «Скоро» на странице профиля в production

---

### 🟡 P2-2 | NEW-005 | MEDIUM: DELETE резюме без подтверждения

**Где:** Фронтенд `/app/resumes` (список резюме)

**Проблема:** Кнопка 🗑 (удалить) резюме удаляет без модального подтверждения «Вы уверены?».

**Что сделать:**
```tsx
const handleDelete = (resumeId: string) => {
  setResumeToDelete(resumeId);
  setShowConfirmModal(true);
};

const confirmDelete = async () => {
  await api.delete(`/api/v1/resumes/${resumeToDelete}`);
  setShowConfirmModal(false);
  refreshList();
  toast.success('Резюме удалено');
};

// Модальное окно:
<ConfirmModal
  open={showConfirmModal}
  title="Удалить резюме?"
  message="Это действие нельзя отменить."
  onConfirm={confirmDelete}
  onCancel={() => setShowConfirmModal(false)}
/>
```

**Acceptance criteria:**
- [ ] Клик на 🗑 → модальное окно «Вы уверены?»
- [ ] «Отмена» → ничего не происходит
- [ ] «Удалить» → резюме удаляется, список обновляется

---

### 🟡 P2-3 | NEW-004 / NEW-V17-009 | MEDIUM: Чужие аватары в localStorage

**Где:** Фронтенд, логика аутентификации

**Проблема:** В localStorage при логине остаются ключи `user_avatar_{uuid}` от других пользователей:
- `user_avatar_80cb1eb7-d565-4a53-a71e-8d8d277fe28d`
- `user_avatar_1f4367a9-82ab-49bf-a857-2d9a268dc42d`

Эти UUID не принадлежат текущему пользователю. Утечка данных между сессиями.

**Что сделать:**
```typescript
// При успешном логине:
const cleanupOtherAvatars = (currentUserId: string) => {
  const keysToRemove: string[] = [];
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key?.startsWith('user_avatar_') && !key.includes(currentUserId)) {
      keysToRemove.push(key);
    }
  }
  keysToRemove.forEach(key => localStorage.removeItem(key));
};

// Вызвать после получения user data:
cleanupOtherAvatars(user.id);
```

**Acceptance criteria:**
- [ ] После логина localStorage содержит только `access_token`, `refresh_token`, и аватар текущего пользователя
- [ ] Нет ключей `user_avatar_*` с чужими UUID

---

### 🟡 P2-4 | NEW-003 | MEDIUM: Нет верификации email

**Где:** Бэкенд + фронтенд

**Проблема:** `is_verified: false` у рабочего аккаунта. Регистрация не требует подтверждения email.

**Что сделать:**
1. При регистрации → отправить email с verification link
2. До верификации — ограничить доступ (или показать баннер «Подтвердите email»)
3. `GET /api/v1/auth/verify/{token}` → `is_verified = true`

> **Примечание:** Это может быть осознанное решение на данном этапе. Если да — хотя бы показать баннер «Подтвердите email для полного доступа» или убрать поле `is_verified` из ответа API.

**Acceptance criteria:**
- [ ] Регистрация → email с ссылкой подтверждения
- [ ] Клик по ссылке → `is_verified = true`
- [ ] Или: баннер на dashboard «Подтвердите email»

---

### 🟡 P2-5 | LIVE-001 | MEDIUM: Кнопка X в модальных окнах не работает

**Где:** Фронтенд, модальные компоненты (Modal.tsx, Dialog.tsx)

**Проблема:** Кнопка X (крестик) в правом верхнем углу модального окна не закрывает его. Закрытие работает только по клику на overlay.

**Что сделать:**
```tsx
<button
  onClick={(e) => {
    e.stopPropagation(); // Не пробрасывать на overlay
    onClose();
  }}
  className="modal-close-button"
  aria-label="Закрыть"
>
  <XIcon />
</button>
```

**Проверить:**
- `onClick` привязан к `<button>`, а не к вложенному `<svg>` или `<span>`
- Нет `pointer-events: none` на кнопке или её родителе
- Нет перехвата события выше в DOM

**Acceptance criteria:**
- [ ] Клик X → модальное окно закрывается
- [ ] Escape → модальное окно закрывается
- [ ] Клик на overlay → модальное окно закрывается

---

### 🟡 P2-6 | NEW-V17-HIST | MEDIUM: История — Match Score 1% → 1%

**Где:** Фронтенд `/app/history`

**Проблема:** Этот баг — следствие P0-2 (Match Score 1%). Записи истории показывают «Match: 1% → 1%» вместо «60% → 77%».

**Что сделать:** Тот же фикс что P0-2, но проверить отдельно для компонента истории:
```tsx
// В компоненте HistoryItem:
const scoreBefore = Math.round(item.match_score_before * 100); // 60
const scoreAfter = Math.round(item.match_score_after * 100);   // 77
<span>Match: {scoreBefore}% → {scoreAfter}%</span>
```

**Acceptance criteria:**
- [ ] История показывает «60% → 77%» (а не «1% → 1%»)

---

### 🟢 P3-1 | NEW-V17-OR | LOW: OpenRouter dropdown — 250+ моделей без группировки

**Где:** Фронтенд, выбор модели OpenRouter

**Проблема:** Dropdown содержит 250+ моделей в одном плоском списке без поиска и группировки. UX проблема.

**Что сделать:**
```tsx
// Добавить поиск и группировку:
<Select
  options={groupedModels}
  isSearchable={true}
  placeholder="Поиск модели..."
  formatGroupLabel={(group) => <strong>{group.label}</strong>}
/>

// Группировка:
const groupedModels = [
  { label: 'Популярные', options: top10Models },
  { label: 'Meta', options: metaModels },
  { label: 'Google', options: googleModels },
  // ...
];
```

**Acceptance criteria:**
- [ ] Поиск по названию модели работает
- [ ] Модели сгруппированы по провайдеру

---

### 🟢 P3-2 | NEW-V17-TRUNC | LOW: Текст «Опасная зона» обрезан

**Где:** Фронтенд `/app/settings/security`

**Проблема:** Текст обрезан: «Вы можете » — предложение не завершено.

**Что сделать:** Дописать текст полностью:
```
Было:    «Вы можете »
Должно:  «Вы можете отменить удаление в течение 30 дней, написав на support@resumecraft.ru»
```

Также проверить CSS: нет ли `overflow: hidden` или `text-overflow: ellipsis` на контейнере.

**Acceptance criteria:**
- [ ] Текст полный, без обрезки

---

## ДЕФЕКТЫ ИЗ PHASE 2 (низкий приоритет, но не забудь)

Эти дефекты были отложены на Phase 2 ещё в v1.6. Если есть время — исправь:

| ID | Описание | Оценка |
|----|----------|--------|
| SEC-001 | .env в git history — аудит и ротация секретов | 2 часа |
| SEC-004 | Redis JTI blacklist для stateless logout | 3 часа |
| SEC-008 | httpOnly cookies вместо localStorage для токенов | 4 часа |
| SEC-009 | Separate keys для access/refresh JWT | 1 час |
| AUTH-002 | Password policy (минимум 8 символов, цифра, буква) | 1 час |
| LIVE-008 | Wizard проверяет доступность моделей ДО начала обработки | 2 часа |
| LIVE-016 | Ошибки валидации на английском → перевести на русский | 2 часа |
| ARCH-003 | Alembic в CI | 1 час |

---

## ПОРЯДОК ВЫПОЛНЕНИЯ

```
═══════════════════════════════════════════════════
       ДЕНЬ 1 — P0 (БЛОКЕРЫ ОСНОВНОГО ФЛОУ)
═══════════════════════════════════════════════════
 1. P0-1: Кнопка «Найти» → API             ~30 мин
 2. P0-2: Match Score × 100                 ~30 мин
 3. P0-3: RAW JSON → форматированный текст  ~30 мин
 4. P0-4: OpenAI max_completion_tokens      ~15 мин
    ─────────────────────────────────────────────
    Итого День 1: ~1.5–2 часа
    После: основной флоу ПОЛНОСТЬЮ рабочий!

═══════════════════════════════════════════════════
       ДЕНЬ 2 — P1 (ВАЖНЫЕ)
═══════════════════════════════════════════════════
 5. P1-1: Удалить аккаунт + модалка        ~1 час
 6. P1-2: Тарифные планы синхронизация      ~30 мин
 7. P1-3: API-ключи UI/backend sync        ~30 мин
 8. P1-4: Login form-data                   ~20 мин
 9. P1-5: Просмотр резюме с форматированием ~1 час
    ─────────────────────────────────────────────
    Итого День 2: ~3–4 часа

═══════════════════════════════════════════════════
       ДЕНЬ 3 — P2/P3 (СРЕДНИЕ И НИЗКИЕ)
═══════════════════════════════════════════════════
10. P2-1: Убрать «Скоро»                   ~10 мин
11. P2-2: Подтверждение удаления резюме     ~20 мин
12. P2-3: Очистка чужих аватаров            ~10 мин
13. P2-4: Email верификация (или баннер)    ~1 час
14. P2-5: Кнопка X в модалках               ~15 мин
15. P2-6: История Match Score (связано с P0-2) ~5 мин
16. P3-1: OpenRouter группировка моделей    ~30 мин
17. P3-2: Текст «Опасная зона»             ~5 мин
    ─────────────────────────────────────────────
    Итого День 3: ~2–3 часа

═══════════════════════════════════════════════════
    ОБЩИЙ ИТОГ: ~7–9 часов работы
═══════════════════════════════════════════════════
```

---

## ЧЕКЛИСТ ПОСЛЕ ВСЕХ ИСПРАВЛЕНИЙ

### Основной флоу (E2E)
- [ ] Логин (`/auth`) → дашборд с корректными счётчиками
- [ ] Загрузка резюме (PDF/DOCX/текст) → список резюме
- [ ] Поиск вакансий: ввести запрос → «Найти» → список вакансий hh.ru
- [ ] Выбор вакансии → выбор модели → «Начать оптимизацию»
- [ ] Оптимизация (Anthropic Claude) → «Оптимизация завершена!»
- [ ] Результат: **форматированный текст** (не JSON), Match Score **77%** (не 1%)
- [ ] Экспорт PDF → скачивается `application/pdf`
- [ ] Экспорт DOCX → скачивается корректный DOCX
- [ ] Оптимизация через OpenAI o4-mini → успешно (не ошибка max_tokens)

### Безопасность
- [ ] Rate limiting: 3-й неудачный логин → 429
- [ ] localStorage: только access_token + refresh_token (нет ключей, нет чужих аватаров)
- [ ] `/openapi.json`, `/docs`, `/redoc` → 404
- [ ] DELETE аккаунта → модалка с паролем → soft-delete

### Настройки
- [ ] Профиль: имя/email сохраняются, нет «Скоро»
- [ ] AI: ключи синхронизированы с бэкендом
- [ ] Подписка: тексты совпадают с Справкой
- [ ] Безопасность: «Удалить аккаунт» работает, текст полный

### История
- [ ] Match Score: «60% → 77%» (не «1% → 1%»)
- [ ] Кнопка «Открыть» → `/app/results/{id}`

### Модалки
- [ ] X закрывает → ✅
- [ ] Escape закрывает → ✅
- [ ] Overlay закрывает → ✅

---

## ОЖИДАЕМЫЙ РЕЗУЛЬТАТ ПОСЛЕ v1.8

```
Загрузка резюме (PDF/DOCX/текст)
       ↓
Поиск вакансий на hh.ru        ← P0-1 ИСПРАВЛЕН
       ↓
Выбор AI-модели (4 провайдера, включая OpenAI o-серию)  ← P0-4 ИСПРАВЛЕН
       ↓
Оптимизация (~20 сек)
       ↓
Результат: ФОРМАТИРОВАННЫЙ ТЕКСТ  ← P0-3 ИСПРАВЛЕН
Match Score: 77% (+17 пунктов)     ← P0-2 ИСПРАВЛЕН
       ↓
Экспорт PDF/DOCX (корректные MIME)
       ↓
Оценка проекта: 6/10 → 8.5/10
```

---

> **Источники:** `01_CRITICAL_SECURITY.md` → `13_FINAL_3ROUNDS_REPORT.md` (13 отчётов, 3 раунда тестирования, 23+ API endpoints, 17 страниц)

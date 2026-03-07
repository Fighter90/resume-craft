# AGENT FIX PROMPT V20 — Все дефекты и доработки после ретеста V19

**Дата:** 2026-03-07
**Источник:** QA Report #15 (15_RETEST_V19_FINAL.md) + **3 полных прохода тестирования**
**Проект:** ResumeCraft.ru
**Тестовый аккаунт:** test_new@example.com
**Resume ID:** `4a4439b1-b24c-4bb0-9ca8-dc2e37885539`
**Rewrite ID (Claude Sonnet):** `d3b94cf5-e8a8-4476-bcaa-b0d1a2839be1`

---

## СВОДКА ДЕФЕКТОВ

| # | Приоритет | ID | Описание | Тип | Статус 3-го прохода |
|---|-----------|-----|----------|-----|---------------------|
| 1 | 🔴 P0 | P0-3 | RAW JSON на странице /app/results | BUG (partial fix) | ❌ CONFIRMED |
| 2 | 🔴 P0 | P0-4 | OpenAI o-series max_tokens ошибка | BUG (not fixed) | ❌ CONFIRMED (live error on /app/history) |
| 3 | 🟡 P1 | FEATURE-002 | Dropdown скачивания — только DOCX + z-index (overflow:hidden на parent) | FEATURE (partial) + CSS BUG | ❌ CONFIRMED (DOM root cause found) |
| 4 | 🟡 P1 | NEW-V20-001 | OpenRouter dropdown показывает только 3 GigaChat модели вместо 100+ | BUG (new) | ❌ NEW DEFECT |
| 5 | 🟡 P1 | NEW-V20-002 | Фото профиля хранится в localStorage (base64), а не на сервере/в БД | ARCHITECTURE BUG | ❌ NEW DEFECT |
| 6 | 🟡 P2 | NEW-V18-002 | Прогресс-бар застревает на 0% | BUG (not tested) | ⏳ not retested |
| 7 | 🟢 P3 | FEATURE-005 | DOCX viewer не реализован | FEATURE (not tested) | ⏳ not retested |
| 8 | 🟢 P3 | UX-001 | Клик по имени резюме → модал | UX improvement | ⏳ not retested |
| 9 | 🔴 P0 | NEW-V20-003 | Удаление аккаунта: DELETE /api/v1/auth/me → 500 Internal Server Error | BUG (server crash) | ❌ NEW DEFECT |

---

## 🔴 ДЕФЕКТ 1 — P0-3: RAW JSON на странице результатов (CRITICAL)

### Проблема
Страница `/app/results/{rewrite_id}` в секции «Сравнение версий» отображает **сырой JSON** в правой колонке «Оптимизировано» вместо форматированного текста резюме.

### Что видит пользователь
```
Оптимизировано  56 баллов
```json { "summary": "Senior PHP Developer с 14-летним опытом...", "experience": [{"position": "...", "company": "...", "achievements": [...]}]}
```

### Ожидаемый результат
Форматированный текст с секциями (Профессиональное резюме, Опыт работы, Образование, Навыки), bullet points для достижений — **точно такой же формат, как во вкладке «Оптимизировано» в модале просмотра резюме** (viewer modal).

### Важный контекст
✅ В **модале просмотра** (viewer, кнопка 👁 на странице /app/resumes) — JSON уже корректно парсится и отображается форматированно: секции с иконками, заголовками, буллет-листами.
❌ На **странице /app/results** — тот же JSON показывается как сырая строка.

### Где исправлять
- **Frontend:** Компонент отображения результатов оптимизации на странице `/app/results`
- Вероятные файлы: `ResultsPage.tsx`, `ResultsComparison.tsx`, `OptimizedResumeView.tsx` или аналогичные
- **Решение:** Использовать тот же компонент/парсер JSON→HTML, который уже работает во вкладке «Оптимизировано» модала просмотра

### Алгоритм исправления

```typescript
// 1. Найти компонент, который рендерит "Сравнение версий" на странице results
// Вероятно: ResultsComparison или ComparisonView

// 2. В том месте, где выводится optimized_text, добавить парсинг:
function renderOptimizedContent(text: string): JSX.Element {
  // Попытка распарсить как JSON
  let parsed: any = null;
  try {
    // Убрать markdown-обёртку ```json ... ``` если есть
    let cleanText = text.trim();
    if (cleanText.startsWith('```json')) {
      cleanText = cleanText.replace(/^```json\s*/, '').replace(/```\s*$/, '');
    }
    if (cleanText.startsWith('{') || cleanText.startsWith('[')) {
      parsed = JSON.parse(cleanText);
    }
  } catch (e) {
    parsed = null;
  }

  if (parsed && typeof parsed === 'object') {
    return <FormattedResume data={parsed} />;
  }

  // Fallback: показать как plain text / markdown
  return <MarkdownRenderer content={text} />;
}

// 3. Компонент FormattedResume — тот же, что уже используется в viewer modal
// Импортировать его из того же места:
// import { FormattedResume } from '@/components/resume/FormattedResume';
// или как он называется в проекте

// 4. Заменить прямой вывод текста на вызов renderOptimizedContent:
// БЫЛО:
//   <div className="optimized-text">{rewrite.optimized_text}</div>
// СТАЛО:
//   <div className="optimized-text">{renderOptimizedContent(rewrite.optimized_text)}</div>
```

### Структура JSON (для справки)
```json
{
  "summary": "Senior PHP Developer с 14-летним опытом...",
  "experience": [
    {
      "position": "Senior PHP Developer",
      "company": "Company Name",
      "period": "2020–2024",
      "achievements": [
        "Достижение 1",
        "Достижение 2"
      ]
    }
  ],
  "education": [...],
  "skills": [...],
  "certifications": [...]
}
```

### Проверка после исправления
1. Открыть `https://resumecraft.ru/app/results/d3b94cf5-e8a8-4476-bcaa-b0d1a2839be1`
2. Секция «Сравнение версий» → правая колонка «Оптимизировано» должна показывать форматированный текст
3. Формат должен совпадать с вкладкой «Оптимизировано» в модале просмотра (viewer)

---

## 🔴 ДЕФЕКТ 2 — P0-4: OpenAI o-series max_tokens (CRITICAL)

### Проблема
Оптимизация через модели OpenAI o-серии (o1, o3, o3-mini, o4-mini) завершается ошибкой:
```
LLM-провайдер openai: Error code: 400 - {'error': {'message': "Unsupported parameter: 'max_tokens' is not supported with this model. Use 'max_completion_tokens' instead.", 'type': 'invalid_request_error', 'param': 'max_tokens'}}
```

### Причина
Backend отправляет параметр `max_tokens` в запросе к OpenAI API. Модели o-серии (o1, o3, o3-mini, o4-mini) требуют `max_completion_tokens` вместо `max_tokens`.

### Где исправлять
- **Backend:** Сервис/адаптер для вызова OpenAI API
- Вероятные файлы: `llm_service.py`, `openai_provider.py`, `openai_adapter.py` или аналогичные
- Место: формирование параметров запроса к OpenAI API

### Алгоритм исправления

```python
# В месте формирования запроса к OpenAI API:

# Список моделей o-серии, которые требуют max_completion_tokens
O_SERIES_MODELS = ("o1", "o3", "o4")  # покрывает o1, o1-mini, o3, o3-mini, o4-mini и будущие

def get_completion_params(model_name: str, max_tokens: int) -> dict:
    """Возвращает правильный параметр лимита токенов в зависимости от модели."""
    params = {}

    # Извлечь имя модели (может приходить как "openai:o4-mini" или просто "o4-mini")
    clean_model = model_name.split(":")[-1] if ":" in model_name else model_name

    if clean_model.startswith(O_SERIES_MODELS):
        params["max_completion_tokens"] = max_tokens
        # ВАЖНО: НЕ передавать max_tokens для o-серии
    else:
        params["max_tokens"] = max_tokens

    return params

# Пример использования:
# БЫЛО:
#   response = client.chat.completions.create(
#       model=model_name,
#       messages=messages,
#       max_tokens=max_tokens,
#       temperature=temperature,
#   )

# СТАЛО:
#   token_params = get_completion_params(model_name, max_tokens)
#   response = client.chat.completions.create(
#       model=clean_model,
#       messages=messages,
#       temperature=temperature,
#       **token_params,
#   )
```

### Дополнительно для o-серии
Модели o-серии также имеют ограничения:
- `temperature` должен быть `1` (фиксированный, не настраиваемый)
- `top_p` не поддерживается
- Если передаётся `system` message — он должен быть как `developer` role для o1

```python
# Расширенная версия:
if clean_model.startswith(O_SERIES_MODELS):
    params["max_completion_tokens"] = max_tokens
    # Не передавать temperature и top_p
    params.pop("temperature", None)
    params.pop("top_p", None)
else:
    params["max_tokens"] = max_tokens
    params["temperature"] = temperature
```

### Проверка после исправления
1. Зайти в Настройки → AI-модели → выбрать OpenAI → o4-mini
2. Запустить оптимизацию резюме
3. Оптимизация должна завершиться успешно (без ошибки 400)
4. Результат должен появиться в Истории оптимизаций со статусом «Завершено»

---

## 🟡 ДЕФЕКТ 3 — FEATURE-002: Dropdown скачивания — неполный + скрыт под элементами (MEDIUM)

### Проблема (2 подпроблемы)

**A) Неполное меню:** Кнопка скачивания (⬇∨) на странице `/app/resumes` в таблице резюме раскрывает dropdown-меню, но в нём **только одна опция**: «Скачать DOCX». Отсутствуют «Скачать PDF» и «Скачать TXT».

**B) 🔴 CSS/z-index баг:** Выпадающее меню скачивания **скрывается под соседними элементами** таблицы (следующая строка таблицы, другие кнопки или контейнер таблицы перекрывают dropdown). Меню не видно или обрезается — пользователь не может кликнуть по пунктам.

### Контекст
- В модале просмотра (viewer) все 3 формата экспорта работают: DOCX, PDF, TXT (кнопки в хедере)
- API экспорта для всех форматов возвращает 200:
  - `GET /api/v1/export/{rewrite_id}/docx` → 200 ✅
  - `GET /api/v1/export/{rewrite_id}/pdf` → 200 ✅
  - `GET /api/v1/export/{rewrite_id}/txt` → 200 ✅
- Нужно: (1) добавить 2 пункта в dropdown, (2) исправить стили чтобы меню не скрывалось

### Где исправлять
- **Frontend:** Компонент кнопки скачивания в таблице резюме
- Вероятные файлы: `ResumesTable.tsx`, `ResumeActions.tsx`, `DownloadButton.tsx` или аналогичные
- **CSS/стили:** Контейнер таблицы, строки таблицы, dropdown-обёртка

### Алгоритм исправления

**Часть 1 — Исправить CSS/z-index (ПРИОРИТЕТ!):**

```css
/* Проблема: dropdown скрывается под соседними элементами таблицы.
   Причины (проверить все):
   1. overflow: hidden на родительском контейнере таблицы или строке
   2. Отсутствие z-index на dropdown
   3. position: relative/static на dropdown-обёртке
   4. stacking context создаётся родительским элементом */

/* РЕШЕНИЕ A (рекомендуется): Портал — рендерить dropdown вне таблицы */
/* Использовать React Portal чтобы вынести dropdown в document.body: */
```

```tsx
import { createPortal } from 'react-dom';

function DownloadDropdown({ rewriteId, buttonRef, isOpen }: Props) {
  if (!isOpen) return null;

  // Позиционировать относительно кнопки
  const rect = buttonRef.current?.getBoundingClientRect();
  const style = {
    position: 'fixed' as const,
    top: rect ? rect.bottom + 4 : 0,
    left: rect ? rect.left : 0,
    zIndex: 9999,
  };

  return createPortal(
    <div style={style} className="download-dropdown-menu">
      {downloadOptions.map(opt => (
        <button key={opt.format} onClick={() => handleDownload(rewriteId, opt.format)}>
          {opt.icon} {opt.label}
        </button>
      ))}
    </div>,
    document.body
  );
}
```

```css
/* РЕШЕНИЕ B (быстрое): Если портал избыточен — исправить z-index и overflow */

/* 1. На контейнере таблицы — убрать overflow: hidden */
.resumes-table-container,
.resumes-table-wrapper {
  overflow: visible !important;  /* или overflow-x: auto; overflow-y: visible; */
}

/* 2. На строке таблицы (tr) — убрать overflow */
.resumes-table tr,
.resumes-table tbody tr {
  overflow: visible !important;
  position: relative; /* если нужен stacking context */
}

/* 3. На ячейке с кнопкой — убрать overflow */
.resumes-table td:last-child,
.resume-actions-cell {
  overflow: visible !important;
  position: relative;
}

/* 4. На самом dropdown-меню — высокий z-index + position */
.download-dropdown-menu {
  position: absolute;
  z-index: 1000;      /* выше любых элементов таблицы */
  top: 100%;           /* сразу под кнопкой */
  right: 0;            /* выравнивание по правому краю кнопки */
  min-width: 200px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  padding: 4px 0;
}

/* 5. Обёртка кнопки должна быть position: relative */
.download-button-wrapper {
  position: relative;
  display: inline-block;
}
```

```css
/* РЕШЕНИЕ C: Если используется Tailwind — классы */

/* На контейнере dropdown: */
/* className="absolute right-0 top-full mt-1 z-50 bg-white border rounded-lg shadow-lg min-w-[200px]" */

/* На обёртке кнопки: */
/* className="relative" */

/* На контейнере таблицы — добавить overflow-visible: */
/* className="overflow-visible" (или убрать overflow-hidden / overflow-auto) */
```

**Часть 2 — Добавить PDF и TXT в меню:**

```tsx
const downloadOptions = [
  { label: "Скачать DOCX", format: "docx", icon: "📄" },
  { label: "Скачать PDF", format: "pdf", icon: "📕" },
  { label: "Скачать TXT", format: "txt", icon: "📝" },
];

// Стили для каждого пункта меню:
// className="flex items-center gap-2 w-full px-4 py-2 text-sm text-gray-700
//            hover:bg-gray-100 cursor-pointer transition-colors"

const handleDownload = async (rewriteId: string, format: string) => {
  const response = await fetch(`/api/v1/export/${rewriteId}/${format}`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (response.ok) {
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `resume_optimized.${format}`;
    a.click();
    URL.revokeObjectURL(url);
  }
};

// ВАЖНО: Dropdown должен отображаться только если у резюме есть хотя бы одна
// успешная оптимизация (rewrite). Если нет rewrite_id — кнопка неактивна или
// показывает только "Скачать оригинал".
```

**Часть 3 — Закрытие dropdown при клике вне меню:**

```tsx
// Обязательно добавить закрытие при клике вне области dropdown:
useEffect(() => {
  if (!isOpen) return;
  const handleClickOutside = (e: MouseEvent) => {
    if (!dropdownRef.current?.contains(e.target as Node) &&
        !buttonRef.current?.contains(e.target as Node)) {
      setIsOpen(false);
    }
  };
  document.addEventListener('mousedown', handleClickOutside);
  return () => document.removeEventListener('mousedown', handleClickOutside);
}, [isOpen]);
```

### 🔍 ТОЧНАЯ CSS-ДИАГНОСТИКА ИЗ DOM (3-й проход, 07.03.2026)

**Результаты JS-анализа DOM в Chrome DevTools:**
```
Dropdown BUTTON: zIndex=auto, position=static, overflow=visible
Parent DIV (td-actions): overflow=hidden, zIndex=100, position=absolute  ← ROOT CAUSE
Grandparent DIV: overflow=visible
Great-grandparent DIV: overflow=visible
```

**ROOT CAUSE:** Родительский `<div class="td-actions">` имеет `overflow: hidden` — это **обрезает** dropdown. Также `position: absolute` + `z-index: 100` создают stacking context, что мешает дочерним элементам выйти за пределы.

**Минимальный фикс:**
```css
.td-actions {
  overflow: visible !important;  /* БЫЛО: hidden — обрезало dropdown */
}
```

**Или Tailwind:** заменить `overflow-hidden` на `overflow-visible` в classNameList элемента `.td-actions`.

### Чек-лист диагностики z-index проблемы
Если dropdown всё ещё скрыт после исправлений, проверить в DevTools:
1. `Computed` → ищем `overflow` на всех родителях dropdown до `<body>` — не должно быть `hidden` или `auto`
2. `Computed` → `z-index` на dropdown >= 1000
3. `Computed` → `position` на dropdown-обёртке = `relative`, на dropdown = `absolute` или `fixed`
4. Есть ли `transform`, `filter`, `perspective` на родителях? Они создают новый stacking context и могут ограничить z-index

### Проверка после исправления
1. Открыть `/app/resumes`
2. Нажать стрелку ∨ рядом с кнопкой скачивания
3. **Dropdown полностью виден**, не обрезается, не скрыт под другими элементами
4. Должны отображаться 3 опции: DOCX, PDF, TXT
5. Каждая опция должна скачивать файл соответствующего формата
6. Клик вне dropdown — меню закрывается
7. Проверить на последней строке таблицы — dropdown не должен обрезаться снизу (если обрезается — dropdown должен раскрываться вверх)

---

## 🟡 ДЕФЕКТ 4 — NEW-V20-001: OpenRouter dropdown показывает только GigaChat модели (HIGH — NEW)

### Проблема
На странице `/app/settings/ai` при выборе провайдера OpenRouter, dropdown «Модель OpenRouter» содержит **только 3 модели GigaChat** (GigaChat-Pro, GigaChat, GigaChat-Max). Должен содержать **100+ моделей** из каталога OpenRouter (Claude, GPT, Gemini, Mixtral, Llama и т.д.), сгруппированных по провайдерам через `<optgroup>`.

### Данные из DOM-анализа (3-й проход)
```javascript
// JS-анализ select элемента:
{
  totalOptions: 3,
  totalOptgroups: 0,
  selectedValue: "GigaChat-Pro",
  options: [
    { value: "GigaChat-Pro", text: "GigaChat-Pro" },
    { value: "GigaChat", text: "GigaChat" },
    { value: "GigaChat-Max", text: "GigaChat-Max" }
  ]
}
```

### Причина
Frontend не загружает каталог моделей OpenRouter с бэкенда. Вместо этого select заполняется моделями GigaChat (вероятно, это fallback или модели другого провайдера подставляются по ошибке).

### Где исправлять
- **Frontend:** Компонент настроек AI, логика загрузки моделей для OpenRouter
- Вероятные файлы: `AISettingsPage.tsx`, `ModelSelector.tsx`, `useModels.ts` или аналогичные
- **Backend:** Эндпоинт `/api/v1/models/openrouter` или `/api/v1/settings/models` — проверить, возвращает ли полный список

### Алгоритм исправления

```typescript
// 1. При выборе провайдера OpenRouter — загрузить модели с бэкенда:
useEffect(() => {
  if (selectedProvider === 'openrouter') {
    fetch('/api/v1/models/openrouter', {
      headers: { Authorization: `Bearer ${token}` }
    })
    .then(res => res.json())
    .then(models => setOpenRouterModels(models))
    .catch(err => console.error('Failed to load OpenRouter models:', err));
  }
}, [selectedProvider]);

// 2. Сгруппировать модели по провайдерам через <optgroup>:
<select value={selectedModel} onChange={e => setSelectedModel(e.target.value)}>
  {Object.entries(groupedModels).map(([provider, models]) => (
    <optgroup key={provider} label={provider}>
      {models.map(m => (
        <option key={m.id} value={m.id}>{m.name}</option>
      ))}
    </optgroup>
  ))}
</select>

// 3. Группировка:
function groupByProvider(models: Model[]): Record<string, Model[]> {
  return models.reduce((acc, model) => {
    const provider = model.id.split('/')[0]; // e.g. "anthropic/claude-3-sonnet" → "anthropic"
    if (!acc[provider]) acc[provider] = [];
    acc[provider].push(model);
    return acc;
  }, {} as Record<string, Model[]>);
}
```

### Проверка после исправления
1. Открыть `/app/settings/ai` → выбрать OpenRouter
2. Dropdown «Модель OpenRouter» должен содержать 50+ моделей
3. Модели должны быть сгруппированы по провайдерам (Anthropic, OpenAI, Google, Meta, Mistral, etc.)
4. Выбранная модель должна сохраняться при клике «Сохранить»

---

## 🟡 ДЕФЕКТ 5 — NEW-V20-002: Фото профиля хранится в localStorage вместо сервера/БД (HIGH — NEW)

### Проблема
Фото профиля пользователя хранится как **base64 data URL в `localStorage`** браузера (ключ `user_avatar_{userId}`). Файл не отправляется на сервер, ссылка на фото не сохраняется в БД. Это означает:
- Фото **теряется** при очистке кэша браузера, смене браузера или устройства
- `localStorage` имеет лимит ~5-10MB — одно фото в base64 может занять 1-5MB, забивая хранилище
- Фото недоступно в других сессиях пользователя (другой браузер, мобильное приложение)
- API `/api/v1/auth/me` **не содержит поля** `avatar_url` — серверная модель пользователя не знает о фото

### Текущая реализация (из анализа исходного кода)
```javascript
// Загрузка фото — ТЕКУЩИЙ КОД (минифицированный):
const handleFileChange = (event) => {
  const file = event.target.files?.[0];
  if (file && file.type.startsWith("image/")) {
    const reader = new FileReader();
    reader.onload = () => {
      const base64 = reader.result;  // data:image/jpeg;base64,...
      setAvatar(base64);             // React state
      try {
        localStorage.setItem(`user_avatar_${userId}`, base64);  // ← ПРОБЛЕМА
      } catch {}
    };
    reader.readAsDataURL(file);
  }
};

// Удаление фото:
const handleDelete = () => {
  setAvatar(null);
  try {
    localStorage.removeItem(`user_avatar_${userId}`);
  } catch {}
};

// Очистка старых аватаров других пользователей:
// Перебирает localStorage, удаляет ключи user_avatar_* не текущего пользователя
```

### Данные из API (поле avatar отсутствует)
```json
// GET /api/v1/auth/me — ответ:
{
  "id": "a2c06187-...",
  "email": "test_new@example.com",
  "full_name": "Сергей Емельянов",
  "plan": "free",
  "optimizations_used": 2,
  "is_active": true,
  "is_verified": true,
  "created_at": "...",
  "updated_at": "..."
  // ← НЕТ поля avatar_url / photo_url
}
```

### Где исправлять
- **Backend:** Модель пользователя (SQLAlchemy), эндпоинт загрузки аватара, эндпоинт `/api/v1/auth/me`
- **Frontend:** Компонент профиля — заменить localStorage на API-вызовы
- **Инфраструктура:** Хранилище файлов на сервере (папка `media/avatars/` или S3)

### Алгоритм исправления

**Часть 1 — Backend: Модель и миграция БД**

```python
# 1. Добавить поле avatar_url в модель User (SQLAlchemy)
# Файл: models/user.py или models.py

class User(Base):
    __tablename__ = "users"
    # ... существующие поля ...
    avatar_url = Column(String(500), nullable=True, default=None)
    # Хранит относительный путь: "avatars/a2c06187-xxxx.jpg"
```

```bash
# 2. Миграция Alembic
alembic revision --autogenerate -m "add avatar_url to users"
alembic upgrade head
```

**Часть 2 — Backend: Эндпоинт загрузки аватара**

```python
# Файл: routers/users.py или routers/profile.py
import os
import uuid
from pathlib import Path
from fastapi import UploadFile, File, HTTPException

AVATAR_DIR = Path("media/avatars")
AVATAR_DIR.mkdir(parents=True, exist_ok=True)
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

@router.post("/api/v1/profile/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Валидация типа файла
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "Допустимые форматы: JPEG, PNG, WebP, GIF")

    # Валидация размера
    contents = await file.read()
    if len(contents) > MAX_AVATAR_SIZE:
        raise HTTPException(400, "Максимальный размер фото: 5 MB")

    # Удалить старый аватар если есть
    if current_user.avatar_url:
        old_path = AVATAR_DIR / current_user.avatar_url.split("/")[-1]
        if old_path.exists():
            old_path.unlink()

    # Сохранить файл
    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
    filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = AVATAR_DIR / filename
    filepath.write_bytes(contents)

    # Обновить БД
    current_user.avatar_url = f"/media/avatars/{filename}"
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)

    return {"avatar_url": current_user.avatar_url}


@router.delete("/api/v1/profile/avatar")
async def delete_avatar(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.avatar_url:
        # Удалить файл
        old_path = AVATAR_DIR / current_user.avatar_url.split("/")[-1]
        if old_path.exists():
            old_path.unlink()
        # Очистить в БД
        current_user.avatar_url = None
        db.add(current_user)
        await db.commit()

    return {"avatar_url": None}
```

**Часть 3 — Backend: Статика для раздачи аватаров**

```python
# В main.py — добавить StaticFiles для media
from fastapi.staticfiles import StaticFiles

app.mount("/media", StaticFiles(directory="media"), name="media")
```

**Часть 4 — Backend: Обновить схему ответа /api/v1/auth/me**

```python
# В схеме UserResponse добавить:
class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    plan: str
    optimizations_used: int
    is_active: bool
    is_verified: bool
    avatar_url: str | None = None  # ← ДОБАВИТЬ
    created_at: datetime
    updated_at: datetime
```

**Часть 5 — Frontend: Заменить localStorage на API**

```typescript
// Файл: компонент ProfileSettings или ProfilePage

// БЫЛО (localStorage):
// const [avatar, setAvatar] = useState(localStorage.getItem(`user_avatar_${userId}`));
// localStorage.setItem(`user_avatar_${userId}`, base64);

// СТАЛО (API):
const [avatar, setAvatar] = useState<string | null>(user?.avatar_url || null);

// Загрузка фото — отправка на сервер
const handlePhotoUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
  const file = event.target.files?.[0];
  if (!file || !file.type.startsWith("image/")) return;

  // Валидация на клиенте
  if (file.size > 5 * 1024 * 1024) {
    toast.error("Максимальный размер фото: 5 MB");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("/api/v1/profile/avatar", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: formData,  // НЕ устанавливать Content-Type — browser сам поставит multipart/form-data
    });

    if (response.ok) {
      const data = await response.json();
      setAvatar(data.avatar_url);  // "/media/avatars/xxx.jpg"
      toast.success("Фото обновлено");
    } else {
      const err = await response.json();
      toast.error(err.detail || "Ошибка загрузки фото");
    }
  } catch {
    toast.error("Ошибка сети");
  }
};

// Удаление фото
const handlePhotoDelete = async () => {
  try {
    const response = await fetch("/api/v1/profile/avatar", {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (response.ok) {
      setAvatar(null);
      toast.success("Фото удалено");
    }
  } catch {
    toast.error("Ошибка удаления");
  }
};

// Отображение аватара
<img
  src={avatar || undefined}
  alt="Фото профиля"
  onError={(e) => { e.currentTarget.style.display = 'none'; }}
/>
// Если avatar === null → показывать инициалы (как сейчас: "АП")

// УДАЛИТЬ: весь код с localStorage.setItem/getItem/removeItem для user_avatar_*
```

**Часть 6 — Миграция существующих аватаров (опционально)**

```typescript
// Одноразовая миграция: если у пользователя есть аватар в localStorage — загрузить на сервер
useEffect(() => {
  const localAvatar = localStorage.getItem(`user_avatar_${userId}`);
  if (localAvatar && !user?.avatar_url) {
    // Конвертировать base64 → Blob → FormData и отправить на сервер
    fetch(localAvatar)
      .then(res => res.blob())
      .then(blob => {
        const formData = new FormData();
        formData.append("file", blob, "avatar.jpg");
        return fetch("/api/v1/profile/avatar", {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
          body: formData,
        });
      })
      .then(res => res.json())
      .then(data => {
        setAvatar(data.avatar_url);
        localStorage.removeItem(`user_avatar_${userId}`);  // Очистить после миграции
      })
      .catch(() => {});  // Тихо пропустить ошибки миграции
  }
}, [userId, user?.avatar_url]);
```

### Проверка после исправления
1. Загрузить фото на `/app/settings/profile` → файл должен отправиться на сервер (`POST /api/v1/profile/avatar`)
2. `GET /api/v1/auth/me` должен возвращать `avatar_url: "/media/avatars/xxx.jpg"`
3. Фото должно отображаться в профиле и сайдбаре
4. Открыть сайт в другом браузере / инкогнито → фото должно быть видно
5. `localStorage` не должен содержать ключей `user_avatar_*`
6. Удалить фото → `DELETE /api/v1/profile/avatar` → файл удалён с сервера, поле в БД = null
7. Проверить лимит: файл > 5MB → ошибка 400
8. Проверить формат: загрузить .txt → ошибка 400

---

## 🟡 ДЕФЕКТ 6 — NEW-V18-002: Прогресс-бар застревает на 0% (MEDIUM)

### Проблема
На странице `/app/processing` во время оптимизации прогресс-бар показывает 0% в течение ~20-25 секунд, затем резко перескакивает на 100%.

### Где исправлять
- **Frontend:** Компонент ProcessingPage, механизм polling/SSE
- **Backend:** Эндпоинт `/api/v1/rewrite/{id}/status` — проверить, обновляется ли поле progress

### Алгоритм исправления

**Вариант A: Фейковый прогресс (быстрое решение)**
```typescript
// На фронтенде — анимированный прогресс, который плавно двигается
// пока задача в статусе "processing":
const [progress, setProgress] = useState(0);

useEffect(() => {
  if (status === 'processing') {
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 90) return prev; // Не доходить до 100% пока не придёт реальный результат
        // Быстро до 30%, потом медленнее
        const increment = prev < 30 ? 3 : prev < 60 ? 1.5 : 0.5;
        return Math.min(prev + increment, 90);
      });
    }, 1000);
    return () => clearInterval(interval);
  }
  if (status === 'completed') {
    setProgress(100);
  }
}, [status]);
```

**Вариант B: Реальный прогресс через SSE (правильное решение)**
```python
# Backend: SSE endpoint
@router.get("/api/v1/rewrite/{rewrite_id}/stream")
async def stream_progress(rewrite_id: str):
    async def event_generator():
        while True:
            task = await get_rewrite_task(rewrite_id)
            yield f"data: {json.dumps({'progress': task.progress, 'status': task.status})}\n\n"
            if task.status in ('completed', 'failed'):
                break
            await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

```typescript
// Frontend: SSE client
useEffect(() => {
  const eventSource = new EventSource(`/api/v1/rewrite/${rewriteId}/stream`);
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    setProgress(data.progress);
    if (data.status === 'completed' || data.status === 'failed') {
      eventSource.close();
      // redirect to results
    }
  };
  return () => eventSource.close();
}, [rewriteId]);
```

**Вариант C: Уменьшить polling interval (минимальное решение)**
```typescript
// Если используется polling — уменьшить интервал до 2-3 секунд:
const POLL_INTERVAL = 2000; // было, вероятно, 5000-10000

useEffect(() => {
  const interval = setInterval(async () => {
    const res = await fetch(`/api/v1/rewrite/${rewriteId}/status`);
    const data = await res.json();
    setProgress(data.progress || 0);
    if (data.status === 'completed') {
      clearInterval(interval);
      navigate(`/app/results/${rewriteId}`);
    }
  }, POLL_INTERVAL);
  return () => clearInterval(interval);
}, [rewriteId]);
```

### Рекомендация
Начать с **Варианта A** (фейковый прогресс) как быстрое решение для UX, затем перейти на **Вариант B** (SSE) для реального отображения прогресса.

### Проверка после исправления
1. Загрузить резюме и запустить оптимизацию
2. На странице processing прогресс-бар должен плавно двигаться
3. Не должно быть застывания на 0%
4. После завершения — переход на страницу результатов

---

## 🟢 ДЕФЕКТ 7 — FEATURE-005: DOCX viewer (LOW)

### Проблема
Модал просмотра (viewer) не поддерживает отображение DOCX-файлов. Для PDF уже реализован просмотрщик на pdf.js. Для DOCX — нет.

### Где исправлять
- **Frontend:** Компонент viewer modal, вкладка «Оригинал»

### Алгоритм исправления

```bash
# Установить библиотеку для рендеринга DOCX
npm install mammoth
# или
npm install docx-preview
```

```typescript
// Вариант с mammoth (конвертация в HTML):
import mammoth from 'mammoth';

async function renderDocx(fileUrl: string): Promise<string> {
  const response = await fetch(fileUrl);
  const arrayBuffer = await response.arrayBuffer();
  const result = await mammoth.convertToHtml({ arrayBuffer });
  return result.value; // HTML строка
}

// В компоненте viewer:
// Если формат === 'docx':
//   <div dangerouslySetInnerHTML={{ __html: docxHtml }} />
// Если формат === 'pdf':
//   <PdfViewer url={fileUrl} />  // существующий компонент
```

### Проверка после исправления
1. Загрузить DOCX-файл через /app/resumes
2. Нажать 👁 для просмотра
3. Вкладка «Оригинал» → должен отображаться рендеренный DOCX

---

## 🟢 ДЕФЕКТ 8 — UX-001: Клик по имени резюме → модал (LOW)

### Проблема
В таблице на странице `/app/resumes` имя файла резюме отображается как обычный текст. Клик по нему ничего не делает. Логично, что клик по имени должен открывать модал просмотра (viewer).

### Где исправлять
- **Frontend:** Компонент таблицы резюме, колонка «Название»

### Алгоритм исправления

```tsx
// В таблице резюме, в колонке "Название":
// БЫЛО:
<td>{resume.filename}</td>

// СТАЛО:
<td>
  <button
    onClick={() => handleViewResume(resume.id)}
    className="text-blue-600 hover:underline cursor-pointer bg-transparent border-none"
  >
    {resume.filename}
  </button>
</td>

// handleViewResume — та же функция, что вызывается при клике на 👁
```

### Проверка после исправления
1. Открыть `/app/resumes`
2. Кликнуть по имени файла резюме
3. Должен открыться модал просмотра (viewer)

---

## 🔴 ДЕФЕКТ 9 — NEW-V20-003: Удаление аккаунта — 500 Internal Server Error (CRITICAL — NEW)

### Проблема
При попытке удалить аккаунт через форму на странице `/app/settings/security` (секция «Опасная зона»), сервер возвращает **HTTP 500 Internal Server Error**. Функция удаления аккаунта полностью неработоспособна.

### Шаги воспроизведения
1. Войти в аккаунт (любой, включая новый)
2. Перейти: Настройки → Безопасность (`/app/settings/security`)
3. В секции «Опасная зона» нажать «Удалить аккаунт»
4. Заполнить поле «Введите ваш пароль» — корректный текущий пароль
5. Заполнить поле «Введите "УДАЛИТЬ" для подтверждения» — `УДАЛИТЬ`
6. Нажать кнопку «Подтвердить»

### Результат
```
Ошибка: "Внутренняя ошибка сервера" (красный блок в UI)
```

### Технические данные
```
Request:  DELETE /api/v1/auth/me
Headers:  Authorization: Bearer <access_token>
Body:     {"password":"QaNew2026!"}
Response: 500
Body:     {"error":"INTERNAL_ERROR","message":"Внутренняя ошибка сервера"}
```

### Ожидаемый результат
- Аккаунт помечается как удалённый (soft delete, 30-дневный grace period)
- Пользователь получает уведомление об успешном удалении
- Происходит logout и редирект на `/auth`
- В течение 30 дней вход восстанавливает аккаунт

### Вероятные причины (backend)
1. **Отсутствует endpoint** `DELETE /api/v1/auth/me` или он не реализован
2. **Ошибка в ORM** — каскадное удаление связанных данных (resumes, rewrites, exports) без правильных foreign key constraints
3. **Ошибка верификации пароля** — неверная обработка тела запроса
4. **Отсутствует поле `is_deleted` / `deleted_at`** в модели User для soft delete

### Где исправлять
- **Backend:** `app/api/v1/auth.py` или `app/api/v1/users.py` — endpoint DELETE
- **Backend:** `app/models/user.py` — добавить поля soft delete если отсутствуют
- **Backend:** Проверить серверные логи на traceback при 500

### Алгоритм исправления

```python
# 1. В модели User — добавить поля soft delete (если отсутствуют)
class User(Base):
    # ... существующие поля ...
    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

# 2. Alembic миграция
# alembic revision --autogenerate -m "add_user_soft_delete_fields"

# 3. Endpoint DELETE /api/v1/auth/me
@router.delete("/me", status_code=200)
async def delete_account(
    body: DeleteAccountRequest,  # {"password": str}
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 3a. Верифицировать пароль
    if not verify_password(body.password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Неверный пароль")

    # 3b. Soft delete
    current_user.is_deleted = True
    current_user.deleted_at = datetime.utcnow()

    # 3c. Инвалидировать все сессии (опционально: занести токен в blacklist)
    await db.commit()

    return {"message": "Аккаунт помечен для удаления. Вы можете восстановить его в течение 30 дней."}

# 4. Pydantic схема
class DeleteAccountRequest(BaseModel):
    password: str

# 5. В get_current_user — добавить проверку:
if user.is_deleted:
    raise HTTPException(status_code=403, detail="Аккаунт удалён")

# 6. Cron-задача для окончательного удаления через 30 дней:
# DELETE FROM users WHERE is_deleted = true AND deleted_at < NOW() - INTERVAL '30 days'
```

### Frontend — текущая реализация (работает корректно)
Фронтенд корректно отправляет `DELETE /api/v1/auth/me` с `{"password": "..."}`. Форма удаления имеет:
- Поле ввода пароля
- Поле подтверждения (ввести «УДАЛИТЬ»)
- Кнопки «Подтвердить» / «Отмена»

Проблема **только на бэкенде** — endpoint возвращает 500.

### Проверка после исправления
1. Создать тестовый аккаунт
2. Перейти в Настройки → Безопасность
3. Нажать «Удалить аккаунт», ввести пароль + «УДАЛИТЬ»
4. Нажать «Подтвердить» → ожидать redirect на /auth
5. Попытаться войти → ожидать сообщение «Аккаунт удалён»
6. Войти повторно (если grace period) → ожидать восстановление
7. Проверить: неверный пароль → ошибка «Неверный пароль», а не 500

---

## РЕГРЕССИОННЫЕ ТЕСТЫ

При исправлении дефектов V20 необходимо проверить, что не сломаны:

| # | Функционал | Как проверить |
|---|-----------|---------------|
| 1 | Авторизация | Логин/логаут, JWT refresh |
| 2 | Дашборд | Статистика, кнопки навигации |
| 3 | Загрузка PDF/DOCX | Страница /app/resumes → загрузить файл |
| 4 | Модал просмотра (viewer) | 👁 → 3 вкладки, экспорт DOCX/PDF/TXT |
| 5 | PDF viewer | Вкладка Оригинал → pdf.js, навигация, зум |
| 6 | Оптимизация (Anthropic Claude) | Запустить через claude-sonnet |
| 7 | Страница результатов | Match Score, ATS, ключевые слова |
| 8 | История оптимизаций | Список, кнопки «Открыть» |
| 9 | OpenRouter optgroup | 57 групп по провайдерам |
| 10 | Настройки профиля | Сохранение данных |
| 11 | Подписка | Тарифы, лимиты |
| 12 | Безопасность | Смена пароля |
| 13 | Справка | Отображение контента |
| 14 | Экспорт | /app/export — форматы и шаблоны |
| 15 | Фильтры и поиск | На странице резюме |
| 16 | Фото профиля | Загрузка, отображение, удаление, кросс-браузерность |
| 17 | Удаление аккаунта | Настройки → Безопасность → Удалить аккаунт → ввод пароля + «УДАЛИТЬ» → успешное удаление |
| 18 | Регистрация | /auth → Регистрация → 4 поля → Создать аккаунт → redirect на dashboard |
| 19 | Вход | /auth → Войти → email + пароль → redirect на dashboard |
| 20 | Смена пароля | Настройки → Безопасность → 3 поля → Обновить пароль → logout + redirect на /auth |

---

## ПРИОРИТЕТ ИСПРАВЛЕНИЙ

### 🔴 Приоритет 1 — MUST FIX (блокируют production):
1. **P0-3** — RAW JSON на странице results → форматированный текст ❌ CONFIRMED 3-й проход
2. **P0-4** — OpenAI o-series max_tokens → max_completion_tokens ❌ CONFIRMED 3-й проход (live error: `Error code: 400`)
3. **NEW-V20-003** — Удаление аккаунта: DELETE /api/v1/auth/me → 500 ❌ NEW DEFECT (server crash, endpoint нерабочий)

### 🟡 Приоритет 2 — SHOULD FIX:
3. **FEATURE-002** — Dropdown: добавить PDF/TXT + исправить CSS `overflow: hidden` на `.td-actions` ❌ CONFIRMED 3-й проход (DOM root cause found)
4. **NEW-V20-001** — OpenRouter dropdown: загружать каталог моделей вместо GigaChat ❌ NEW DEFECT 3-й проход
5. **NEW-V20-002** — Фото профиля: перенести из localStorage на сервер/БД ❌ NEW DEFECT (base64 в localStorage, API не поддерживает avatar_url)
6. **NEW-V18-002** — Прогресс-бар: фейковый или реальный прогресс

### 🟢 Приоритет 3 — NICE TO HAVE:
7. **FEATURE-005** — DOCX viewer (mammoth.js)
8. **UX-001** — Клик по имени резюме → модал

---

## ТЕКУЩЕЕ СОСТОЯНИЕ ПРОЕКТА

**Версия:** V19
**Готовность к продакшену:** 82%
**После исправления P0-3 + P0-4 + NEW-V20-003:** ~88%
**После исправления P0-3 + P0-4 + NEW-V20-003 + FEATURE-002 + NEW-V20-001 + NEW-V20-002:** ~95%
**После исправления всех 9 дефектов:** 100% MVP

### Что работает отлично (✅):
- Авторизация и JWT
- Загрузка и парсинг PDF/DOCX
- Оптимизация через Anthropic Claude и GigaChat
- Модал просмотра с 3 вкладками
- PDF viewer (pdf.js)
- Экспорт DOCX, PDF, TXT
- ~~OpenRouter с 57 optgroup группами~~ ❌ **3-й проход:** Dropdown OpenRouter содержит ТОЛЬКО 3 модели GigaChat (GigaChat-Pro, GigaChat, GigaChat-Max), 0 optgroups. Каталог моделей OpenRouter не загружается
- Все модули настроек (профиль, AI-модели, подписка, ~~безопасность~~ безопасность: смена пароля ✅, удаление аккаунта ❌ 500)
- Дашборд со статистикой
- Справка
- Регрессии нет (15/15 ранее исправленных багов OK)

---

## ДОПОЛНИТЕЛЬНЫЕ НАБЛЮДЕНИЯ ИЗ 2 ПРОХОДОВ

### Наблюдение 1: Экспорт — имя файла при скачивании
При экспорте через API (`/api/v1/export/{rewrite_id}/{format}`) файл скачивается с техническим именем. Рекомендуется:
- Устанавливать `Content-Disposition: attachment; filename="resume_optimized.{format}"` в ответе API
- Ещё лучше — использовать оригинальное имя файла резюме: `Content-Disposition: attachment; filename="{original_filename}_optimized.{format}"`

### Наблюдение 2: Множественные вкладки в браузере
При навигации по разделам приложения (Dashboard → Resumes → Results → Settings) не используется SPA-навигация через React Router в некоторых случаях — страница перезагружается целиком. Проверить, что все ссылки в боковом меню используют `<Link>` из react-router-dom, а не `<a href>`.

### Наблюдение 3: Страница /app/results — кнопка «Экспорт» (УТОЧНЕНИЕ 3-го прохода)
~~На странице результатов `/app/results/{rewrite_id}` кнопка «Экспорт» не работала.~~
**ИСПРАВЛЕНО (3-й проход):** Кнопка «Экспорт» на странице results **работает корректно** — она навигирует на **полную страницу экспорта** `/app/export/{rewrite_id}`, которая содержит:
- Выбор формата: DOCX, PDF, TXT
- Выбор шаблона: Минималистичный, Профессиональный, Креативный
- Кнопка скачивания
- Файл: resume_optimized.docx, ~48 KB
**Это НЕ z-index проблема.** Страница /app/export — полноценный standalone модуль экспорта.

### Наблюдение 4: Модал просмотра — вкладка «Сравнение»
Вкладка «Сравнение» в модале viewer показывает diff между оригинальным и оптимизированным текстом. Если `optimized_text` хранится как JSON, то diff показывает сравнение оригинального текста с JSON-строкой, что некорректно. После исправления P0-3 нужно убедиться, что diff также работает с распарсенным текстом, а не с сырым JSON.

### Наблюдение 5: История оптимизаций — кнопка «Открыть»
На странице `/app/history` кнопка «Открыть» рядом с записью оптимизации ведёт на `/app/results/{rewrite_id}`. Если P0-3 не исправлен — пользователь опять увидит сырой JSON. Это подтверждает критичность P0-3.

### Наблюдение 6: Безопасность API-ключей
На странице настроек AI-моделей (`/app/settings/ai`) пользователь вводит API-ключи (Anthropic, OpenAI, OpenRouter). Проверить:
- Ключи маскируются после сохранения (показывать `sk-ant-...PLUA***`)
- Ключи не передаются в открытом виде в HTML/JS бандле
- Ключи хранятся в зашифрованном виде в БД

### Наблюдение 7: FEATURE-002 — поведение кнопки «Скачать» (основная, не dropdown)
Основная кнопка «Скачать» (не стрелка ∨) скачивает DOCX по умолчанию. После добавления PDF/TXT в dropdown — основная кнопка должна продолжать скачивать DOCX (наиболее востребованный формат), а dropdown показывать все 3 варианта.

---

## ИТОГОВЫЙ ЧЕКЛИСТ ДЛЯ РАЗРАБОТЧИКА

```
[ ] P0-3: Заменить сырой JSON на форматированный текст на /app/results
    [ ] Использовать тот же компонент парсинга, что в viewer modal
    [ ] Проверить вкладку «Сравнение» в viewer — diff не должен использовать JSON
    [ ] Проверить кнопку «Экспорт» на /app/results — должна работать

[ ] P0-4: max_tokens → max_completion_tokens для o-серии
    [ ] Добавить проверку model.startswith(("o1","o3","o4"))
    [ ] Убрать temperature/top_p для o-серии
    [ ] Протестировать на o4-mini

[ ] FEATURE-002: Dropdown скачивания
    [ ] Добавить «Скачать PDF» и «Скачать TXT»
    [ ] Исправить z-index — dropdown не должен скрываться
    [ ] Основная кнопка «Скачать» → DOCX по умолчанию
    [ ] Закрытие dropdown при клике вне
    [ ] Проверить на последней строке таблицы

[ ] NEW-V18-002: Прогресс-бар
    [ ] Реализовать плавную анимацию (Вариант A минимум)
    [ ] Не застревает на 0%
    [ ] Переход на 100% при завершении

[ ] FEATURE-005: DOCX viewer
    [ ] Установить mammoth или docx-preview
    [ ] Рендеринг в «Оригинал» для DOCX файлов

[ ] UX-001: Клик по имени резюме
    [ ] Сделать имя кликабельным
    [ ] Открывает viewer modal

[ ] NEW-V20-001: OpenRouter dropdown
    [ ] Загружать каталог моделей OpenRouter с бэкенда при выборе провайдера
    [ ] Группировать по провайдерам через <optgroup>
    [ ] Должно быть 50+ моделей, НЕ 3 GigaChat

[ ] NEW-V20-002: Фото профиля — перенести на сервер/БД
    [ ] Backend: добавить поле avatar_url в модель User + миграция Alembic
    [ ] Backend: POST /api/v1/profile/avatar — загрузка файла на сервер (media/avatars/)
    [ ] Backend: DELETE /api/v1/profile/avatar — удаление файла и очистка поля
    [ ] Backend: обновить схему UserResponse — добавить avatar_url
    [ ] Backend: app.mount("/media", StaticFiles) для раздачи аватаров
    [ ] Frontend: заменить localStorage.setItem/getItem на fetch POST/DELETE
    [ ] Frontend: удалить весь код с user_avatar_* в localStorage
    [ ] Frontend: миграция — если есть base64 в localStorage, загрузить на сервер и очистить
    [ ] Валидация: формат (JPEG/PNG/WebP/GIF), размер (≤5MB)
    [ ] Проверить: фото видно в другом браузере/инкогнито

[ ] NEW-V20-003: Удаление аккаунта — 500 Internal Server Error
    [ ] Backend: проверить серверные логи на traceback
    [ ] Backend: реализовать/исправить endpoint DELETE /api/v1/auth/me
    [ ] Backend: добавить поля is_deleted + deleted_at в модель User (если нет)
    [ ] Backend: верификация пароля из тела запроса {"password": "..."}
    [ ] Backend: soft delete (is_deleted=True, deleted_at=now())
    [ ] Backend: проверка is_deleted в get_current_user
    [ ] Backend: инвалидация JWT после удаления
    [ ] Frontend: после успешного удаления → logout + redirect на /auth
    [ ] Проверить: неверный пароль → 400, а не 500
    [ ] Проверить: повторный вход восстанавливает аккаунт (grace period 30 дней)

[ ] Общее:
    [ ] Имя файла при скачивании = оригинальное имя + _optimized
    [ ] SPA-навигация через React Router (не полная перезагрузка)
    [ ] API-ключи маскируются после сохранения
    [ ] Регрессионные тесты (15 пунктов в таблице выше)
```

---

## РЕЗУЛЬТАТЫ 3-ГО ПРОХОДА ТЕСТИРОВАНИЯ (07.03.2026)

### Проверено и работает ✅:
| Модуль | URL | Статус |
|--------|-----|--------|
| Dashboard | /app/dashboard | ✅ Статистика: 1 резюме, 2 оптимизации, Match Score 67% |
| Мои резюме | /app/resumes | ✅ Таблица, фильтры, кнопки действий |
| Viewer modal | (кнопка 👁) | ✅ 3 вкладки (Оригинал/Оптимизировано/Сравнение) + 3 кнопки экспорта (DOCX/PDF/TXT) |
| PDF viewer | (вкладка Оригинал) | ✅ pdf.js, 7 страниц, навигация |
| История | /app/history | ✅ 3 записи, кнопки «Открыть» |
| Экспорт | /app/export/{id} | ✅ Standalone страница, 3 формата + 3 шаблона |
| Настройки Профиль | /app/settings/profile | ✅ Имя, фамилия, email (подтверждён), город |
| Настройки AI-модели | /app/settings/ai | ✅ 4 провайдера, API-ключи (все 4 сохранены) |
| Параметры оптимизации | /app/settings/ai | ✅ 5 toggle-ов (все включены) |
| Подписка | /app/settings/subscription | ✅ 3 плана (Free/490₽/1490₽), Робокасса |
| Безопасность | /app/settings/security | ⚠️ Смена пароля ✅, удаление аккаунта ❌ (500 Internal Server Error) |
| Справка | /app/help | ✅ Быстрый старт, описание процесса |

### Подтверждённые дефекты ❌:
| Дефект | Доказательство |
|--------|---------------|
| P0-3: RAW JSON | /app/results/{id} → правая колонка «Оптимизировано» = сырой JSON. В viewer modal — распарсен корректно |
| P0-4: max_tokens | /app/history → запись openai:o4-mini показывает `Error code: 400 - 'max_tokens' is not supported` |
| FEATURE-002: Dropdown | DOM-анализ: только option "Скачать DOCX". Parent .td-actions: overflow=hidden (root cause) |
| NEW-V20-001: OpenRouter | DOM-анализ: select содержит 3 GigaChat модели, 0 optgroups. Каталог OpenRouter не загружен |
| NEW-V20-003: Удаление аккаунта | DELETE /api/v1/auth/me → 500 `{"error":"INTERNAL_ERROR","message":"Внутренняя ошибка сервера"}`. Тестовый аккаунт: qa_test_delete@example.com |

### Результаты тестирования auth-цикла (новый аккаунт qa_test_delete@example.com):
| Шаг | Результат |
|-----|-----------|
| Регистрация (Имя + Email + Пароль + Подтверждение) | ✅ Успешно, redirect на /app/dashboard |
| Вход (Email + Пароль) | ✅ Успешно, redirect на /app/dashboard |
| Смена пароля (Текущий + Новый + Подтверждение) | ✅ Успешно, logout + redirect на /auth |
| Вход с новым паролем | ✅ Успешно, redirect на /app/dashboard |
| Удаление аккаунта (Пароль + «УДАЛИТЬ») | ❌ 500 Internal Server Error |

---

*Промт создан: 07.03.2026*
*Обновлён: 07.03.2026 (3-й проход + NEW-V20-002 + NEW-V20-003: удаление аккаунта 500)*
*Источник: QA Ретест V19 (3 полных прохода + auth-цикл, 9 дефектов) | QA Engineer*

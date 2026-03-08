# AGENT FIX PROMPT V21 — Все дефекты и доработки после ретеста V20

**Дата:** 2026-03-08
**Источник:** QA Report #16 (16_RETEST_V20.md) — полный code review + browser testing
**Проект:** ResumeCraft.ru
**Тестовые аккаунты:** test@example.com, test_new@example.com

---

## СВОДКА ДЕФЕКТОВ

| # | Приоритет | ID | Описание | Тип | Статус |
|---|-----------|-----|----------|-----|--------|
| 1 | 🔴 P0 | P0-3 | ResultsPage: plain text вместо rich HTML для JSON | BUG (partial fix from V20) | ❌ NEEDS REWORK |
| 2 | 🟡 P2 | NEW-V21-003 | Backend progress hardcoded (0/50/100) | ENHANCEMENT | ❌ NEW |
| 3 | 🟡 P2 | NEW-V21-004 | Non-atomic optimizations_used counter (race condition) | BUG | ❌ NEW |
| 4 | 🟡 P2 | NEW-V21-005 | session.flush() без commit() — потенциальная потеря данных | BUG | ❌ NEEDS VERIFICATION |
| 5 | 🟢 P3 | NEW-V21-002 | useState side-effect вместо useEffect (SettingsProfilePage) | CODE QUALITY | ❌ NEW |
| 6 | 🟢 P3 | NEW-V21-006 | Download dropdown z-index: 100 (потенциально мало) | CSS | ❌ MINOR |
| 7 | 🟢 P3 | NEW-V21-007 | OpenRouter fallback model list может устареть | MAINTENANCE | ❌ MINOR |

---

## 🔴 ДЕФЕКТ 1 — P0-3: ResultsPage — plain text вместо rich HTML (CRITICAL)

### Проблема

Страница `/app/results` (ResultsPage.tsx) при получении JSON от LLM конвертирует его в **plain text** с `\n` разделителями. При этом компонент `FormattedResume` в `ResumeViewerModal.tsx` уже реализует **полный rich HTML рендеринг** с иконками, секциями и стилями.

### Текущий код (ResultsPage.tsx:100-136)

```typescript
// ПРОБЛЕМА: plain text вместо rich HTML
const rewrittenText = (() => {
    const trimmed = rewrittenRaw.trim()
    if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
        try {
            const parsed = ...
            const parts: string[] = []
            if (parsed.summary) parts.push(parsed.summary, '')
            // MISSING: contacts, certifications, projects, languages
            // OUTPUT: plain text join('\n')
            return parts.join('\n')
        } catch { }
    }
    return rewrittenRaw
})()
```

### Эталон (ResumeViewerModal.tsx:91-181)

Компонент `FormattedResume` уже умеет рендерить:
- ✅ contacts (name, position, phone, email, city) — с центрированным header
- ✅ summary — с иконкой User
- ✅ experience — с иконкой Briefcase, achievements как `<ul>`
- ✅ education — с иконкой GraduationCap
- ✅ skills — с иконкой Wrench, badge chips

### Как исправить

**Шаг 1:** Вынести `FormattedResume`, `tryParseJSON`, `jsonToPlainText` из ResumeViewerModal.tsx в отдельный файл `frontend/src/components/FormattedResume.tsx`.

**Шаг 2:** В ResultsPage.tsx:
1. Импортировать `FormattedResume` и `tryParseJSON`
2. Определить `optimizedData`:
```typescript
const optimizedData = useMemo(() => {
    if (result.rewritten_data && typeof result.rewritten_data === 'object') {
        return result.rewritten_data
    }
    if (rewrittenRaw) {
        return tryParseJSON(rewrittenRaw)
    }
    return null
}, [result, rewrittenRaw])
```
3. В секции "Оптимизировано" (diff-panel):
```tsx
{optimizedData ? (
    <FormattedResume data={optimizedData} />
) : (
    <FormattedPlainText text={rewrittenText} />
)}
```
4. Для diff comparison использовать `jsonToPlainText(optimizedData)` вместо raw rewrittenText.

**Шаг 3:** Добавить недостающие секции в FormattedResume:
- `certifications` — список сертификатов с датами
- `projects` — список проектов с описаниями
- `languages` — список языков с уровнями

### Файлы для изменения

1. `frontend/src/components/FormattedResume.tsx` — **СОЗДАТЬ** (вынести из ResumeViewerModal.tsx)
2. `frontend/src/pages/wizard/ResultsPage.tsx` — **ИЗМЕНИТЬ** (использовать FormattedResume)
3. `frontend/src/components/ResumeViewerModal.tsx` — **ИЗМЕНИТЬ** (импортировать из FormattedResume.tsx)

### Критерий приёмки

- [ ] На /app/results JSON резюме отображается как rich HTML (не plain text)
- [ ] Секции: contacts, summary, experience, education, skills, certifications, projects, languages
- [ ] Стиль идентичен ResumeViewerModal (иконки, badges, spacing)
- [ ] Diff comparison работает корректно (jsonToPlainText для word-level diff)
- [ ] Markdown code blocks (```json...```) корректно парсятся

---

## 🟡 ДЕФЕКТ 2 — NEW-V21-003: Backend progress hardcoded (0/50/100)

### Проблема

Status endpoint `GET /api/v1/rewrite/{task_id}/status` возвращает только 3 значения progress:
- `pending` → 0%
- `processing` → 50%
- `completed` → 100%

Frontend компенсирует это simulated animation (ProcessingPage.tsx), но реальный progress от сервера может быть точнее.

### Текущий код (rewriter/router.py:150-168)

```python
progress = 0
step = 'pending'
if task.status.value == 'processing':
    progress = 50
    step = 'rewriting'
elif task.status.value == 'completed':
    progress = 100
    step = 'completed'
```

### Как исправить

**Вариант A (минимальный):** Добавить `progress` и `step` поля в RewriteTask model и обновлять их в Celery task:

```python
# В execute_rewrite_task (tasks.py):
task.progress = 10; task.step = 'extracting'; session.flush()
# ... extracting ...
task.progress = 30; task.step = 'analyzing'; session.flush()
# ... analyzing ...
task.progress = 60; task.step = 'rewriting'; session.flush()
# ... rewriting ...
task.progress = 80; task.step = 'scoring'; session.flush()
# ... scoring ...
task.progress = 100; task.step = 'completed'; session.flush()
```

**Вариант B (Redis):** Использовать Redis для real-time progress (быстрее, без нагрузки на БД).

### Файлы для изменения

1. `src/app/rewriter/models.py` — добавить `progress: int`, `step: str` поля
2. `src/app/rewriter/tasks.py` — обновлять progress в каждом шаге
3. `src/app/rewriter/router.py` — читать progress из task model
4. Alembic migration — добавить столбцы

### Критерий приёмки

- [ ] Backend возвращает progress: 10, 30, 60, 80, 100 (не 0/50/100)
- [ ] Backend возвращает step: extracting, analyzing, rewriting, scoring, completed
- [ ] Frontend ProcessingPage использует реальный progress от сервера (Math.max)

---

## 🟡 ДЕФЕКТ 3 — NEW-V21-004: Non-atomic optimizations_used counter

### Проблема

```python
user.optimizations_used += 1  # Python-level increment
```

При concurrent requests (2 оптимизации одновременно) оба читают одно значение и записывают +1, теряя один инкремент.

### Как исправить

```python
from sqlalchemy import update

await session.execute(
    update(User)
    .where(User.id == user_id)
    .values(optimizations_used=User.optimizations_used + 1)
)
```

### Файлы для изменения

1. `src/app/rewriter/service.py` — заменить `user.optimizations_used += 1` на SQL expression

### Критерий приёмки

- [ ] Инкремент через SQL expression (`SET optimizations_used = optimizations_used + 1`)
- [ ] Нет race condition при concurrent requests

---

## 🟡 ДЕФЕКТ 4 — NEW-V21-005: session.flush() без commit()

### Проблема

Несколько мест в коде используют `session.flush()` без явного `session.commit()`:
- `auth/service.py:260` — soft_delete_account
- `auth/router.py:299` — avatar upload (flush avatar_url)
- `auth/service.py:285` — restore_account

### Необходимое действие

**Верифицировать** что FastAPI middleware (get_session dependency) выполняет `await session.commit()` после каждого request. Если да — это корректный паттерн (flush гарантирует SQL выполняется, commit происходит в middleware).

**Если middleware НЕ делает commit:**
```python
# Заменить flush() на commit() в каждом месте:
await session.commit()
```

### Файлы для проверки

1. `src/app/core/database.py` — проверить get_session dependency (должен быть `await session.commit()` в finally или context manager)

### Критерий приёмки

- [ ] Верифицировано что get_session делает commit после flush
- [ ] Или заменены flush() на commit() в критических местах

---

## 🟢 ДЕФЕКТ 5 — NEW-V21-002: useState side-effect (Code Quality)

### Проблема

```typescript
// SettingsProfilePage.tsx:23-26
// WRONG: side-effect в useState initializer
useState(() => {
    const oldKey = `user_avatar_${user?.id || 'default'}`
    try { localStorage.removeItem(oldKey) } catch { /* ignore */ }
})
```

### Как исправить

```typescript
// Заменить на useEffect:
useEffect(() => {
    const oldKey = `user_avatar_${user?.id || 'default'}`
    try { localStorage.removeItem(oldKey) } catch { /* ignore */ }
}, [user?.id])
```

### Файлы для изменения

1. `frontend/src/pages/settings/SettingsProfilePage.tsx` — строки 23-26

### Критерий приёмки

- [ ] Side-effect в useEffect вместо useState
- [ ] Dependency array: [user?.id]

---

## 🟢 ДЕФЕКТ 6 — NEW-V21-006: Download dropdown z-index

### Проблема

`zIndex: 100` на download dropdown в ResumesPage. Модалы используют zIndex 9999/10000. Маловероятно что будет проблема, но для consistency лучше увеличить.

### Как исправить

```typescript
// ResumesPage.tsx:258
zIndex: 200, // было 100
```

### Критерий приёмки

- [ ] z-index dropdown увеличен до 200+

---

## 🟢 ДЕФЕКТ 7 — NEW-V21-007: OpenRouter fallback list maintenance

### Проблема

`FALLBACK_SUB_MODELS` в SettingsAiPage.tsx содержит hardcoded список моделей. Со временем появляются новые модели, старые deprecated.

### Как исправить

**Краткосрочно:** Добавить timestamp комментарий и напоминание обновлять:
```typescript
// Last updated: 2026-03-08. Update quarterly.
const FALLBACK_SUB_MODELS: Record<string, SubModel[]> = {
```

**Долгосрочно:** Перенести fallback list в backend (endpoint `/api/v1/models/fallback`) и периодически обновлять.

### Критерий приёмки

- [ ] Комментарий с датой последнего обновления
- [ ] (Опционально) Backend endpoint для fallback моделей

---

## ПРИОРИТЕТЫ ИСПРАВЛЕНИЯ

### Sprint 1 (Критичный — 1-2 дня)
1. **P0-3** — ResultsPage rich HTML рендеринг (переиспользовать FormattedResume)

### Sprint 2 (Важный — 3-5 дней)
2. **NEW-V21-004** — Atomic counter для optimizations_used
3. **NEW-V21-005** — Верификация session.flush/commit

### Sprint 3 (Улучшения)
4. **NEW-V21-003** — Step-based backend progress
5. **NEW-V21-002** — useState → useEffect fix
6. **NEW-V21-006** — z-index increase
7. **NEW-V21-007** — Fallback list maintenance

---

## ЗАКРЫТЫЕ ДЕФЕКТЫ (из V20)

| ID | Описание | Вердикт |
|----|----------|---------|
| P0-4 | OpenAI o-series max_tokens | ✅ FIXED — llm_client.py o-series detection |
| FEATURE-002 | Download dropdown | ✅ FIXED — 3 формата + outside click |
| NEW-V20-001 | OpenRouter только 3 модели | ✅ FIXED — 16 fallback моделей + server fetch |
| NEW-V18-002 | Progress bar 0% | ✅ FIXED — simulated progress animation |
| FEATURE-005 | DOCX viewer | ✅ FIXED — mammoth + DOMPurify |
| UX-001 | Клик по имени → модал | ✅ FIXED — onClick с handleView |
| NEW-V20-003 | DELETE /me → 500 | ✅ FIXED — soft-delete с 30-дневным recovery |

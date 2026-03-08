# AGENT FIX PROMPT V22 — Все дефекты и доработки после ретеста V21

**Дата:** 2026-03-08
**Источник:** QA Report #17 (17_RETEST_V21.md) — browser testing + code review
**Проект:** ResumeCraft.ru
**Тестовые аккаунты:** test@example.com, test_new@example.com

---

## СВОДКА ДЕФЕКТОВ

| # | Приоритет | ID | Описание | Тип | Статус |
|---|-----------|-----|----------|-----|--------|
| 1 | 🔴 P0 | P0-3 | ResultsPage: RAW JSON / plain text вместо rich HTML | BUG (NOT FIXED from V21) | ❌ CRITICAL |
| 2 | 🔴 P1 | NEW-V22-001 | ATS оценка "D" отображается как "Отлично" | BUG | ❌ NEW |
| 3 | 🔴 P1 | NEW-V22-002 | Все компоненты Match Score идентичны (42%/47%/31%) | BUG | ❌ NEW |
| 4 | 🔴 P1 | NEW-V22-004 | Raw API error leak на странице History | BUG | ❌ NEW |
| 5 | 🟡 P2 | NEW-V22-003 | Счётчик оптимизаций не обновляется в реальном времени | BUG | ❌ NEW |
| 6 | 🟡 P2 | NEW-V22-007 | Download dropdown — только DOCX вместо 3 форматов | BUG | ❌ NEW |
| 7 | 🟡 P2 | NEW-V21-004 | Non-atomic optimizations_used counter (race condition) | BUG (from V21) | ❌ NOT FIXED |
| 8 | 🟡 P2 | NEW-V21-005 | session.flush() без commit() | BUG (from V21) | ❌ NEEDS VERIFICATION |
| 9 | 🟢 P3 | NEW-V22-005 | Avatar initials hardcoded "АП" | BUG | ❌ NEW |
| 10 | 🟢 P3 | NEW-V21-002 | useState side-effect вместо useEffect | CODE QUALITY (from V21) | ❌ NOT FIXED |
| 11 | 🟢 P3 | NEW-V22-008 | API key status icons не обновляются в реальном времени | UX | ❌ NEW |
| 12 | 🟢 P3 | NEW-V21-006 | Download dropdown z-index: 100 | CSS (from V21) | ❌ NOT FIXED |
| 13 | 🟢 P3 | NEW-V21-007 | OpenRouter fallback model list maintenance | MAINTENANCE (from V21) | ❌ NOT FIXED |

---

## 🔴 ДЕФЕКТ 1 — P0-3: ResultsPage — RAW JSON / plain text (CRITICAL)

### Проблема

Страница `/app/results` (ResultsPage.tsx) при получении JSON от LLM:

**Сценарий A (Anthropic Claude):** Claude возвращает JSON в markdown code blocks:
```
```json
{
  "summary": "Senior Frontend Developer...",
  "experience": [...]
}
```​
```
ResultsPage **НЕ СТРИПАЕТ** markdown code blocks → пользователь видит RAW JSON.

**Сценарий B (OpenAI):** Если JSON парсится успешно, он конвертируется в **plain text** через `parts.join('\n')`, а не используется FormattedResume компонент.

### Текущий код (ResultsPage.tsx:100-136)

```typescript
// ПРОБЛЕМА 1: Нет stripping markdown code blocks
// ПРОБЛЕМА 2: Plain text вместо rich HTML
const rewrittenText = (() => {
    const trimmed = rewrittenRaw.trim()
    if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
        // Не ловит: ```json\n{...}\n```
        try {
            const parsed = ...
            // Конвертация в plain text — WRONG
            return parts.join('\n')
        } catch { }
    }
    return rewrittenRaw
})()
```

### Как исправить

**Шаг 1:** Создать файл `frontend/src/components/FormattedResume.tsx` — вынести из ResumeViewerModal.tsx:
- `FormattedResume` компонент (rich HTML рендеринг)
- `tryParseJSON` функция (с stripping markdown code blocks)
- `jsonToPlainText` функция (для diff comparison)

```typescript
// frontend/src/components/FormattedResume.tsx

// Стрипать markdown code blocks
export function tryParseJSON(text: string): any {
    if (!text) return null
    let cleaned = text.trim()
    // Strip markdown code blocks: ```json\n...\n```
    const codeBlockMatch = cleaned.match(/^```(?:json)?\s*\n?([\s\S]*?)\n?\s*```$/)
    if (codeBlockMatch) {
        cleaned = codeBlockMatch[1].trim()
    }
    if (!cleaned.startsWith('{')) return null
    try {
        return JSON.parse(cleaned)
    } catch {
        return null
    }
}

// Plain text конвертация для diff
export function jsonToPlainText(data: any): string {
    const parts: string[] = []
    if (data.contacts) {
        if (data.contacts.name) parts.push(data.contacts.name)
        if (data.contacts.position) parts.push(data.contacts.position)
        const contactInfo = [data.contacts.phone, data.contacts.email, data.contacts.city].filter(Boolean).join(', ')
        if (contactInfo) parts.push(`Контакты: ${contactInfo}`)
        parts.push('')
    }
    if (data.summary) { parts.push('ПРОФЕССИОНАЛЬНЫЙ ПРОФИЛЬ', data.summary, '') }
    if (data.experience?.length) {
        parts.push('ОПЫТ РАБОТЫ')
        data.experience.forEach((exp: any) => {
            parts.push(`${exp.position} — ${exp.company} (${exp.period})`)
            exp.achievements?.forEach((a: string) => parts.push(`• ${a}`))
            parts.push('')
        })
    }
    if (data.education?.length) {
        parts.push('ОБРАЗОВАНИЕ')
        data.education.forEach((edu: any) => {
            parts.push(`${edu.institution} — ${edu.degree} (${edu.year || edu.period || ''})`)
        })
        parts.push('')
    }
    if (data.skills?.length) { parts.push('НАВЫКИ', data.skills.join(', '), '') }
    if (data.certifications?.length) {
        parts.push('СЕРТИФИКАТЫ')
        data.certifications.forEach((c: any) => parts.push(`• ${typeof c === 'string' ? c : `${c.name} (${c.year || c.date || ''})`}`))
        parts.push('')
    }
    if (data.projects?.length) {
        parts.push('ПРОЕКТЫ')
        data.projects.forEach((p: any) => parts.push(`• ${p.name}: ${p.description || ''}`))
        parts.push('')
    }
    if (data.languages?.length) {
        parts.push('ЯЗЫКИ')
        data.languages.forEach((l: any) => parts.push(`• ${typeof l === 'string' ? l : `${l.name} — ${l.level || ''}`}`))
        parts.push('')
    }
    return parts.join('\n')
}

// FormattedResume компонент — полный rich HTML рендеринг
// (вынести из ResumeViewerModal.tsx:91-181)
// Добавить секции: certifications, projects, languages
```

**Шаг 2:** В ResultsPage.tsx:
```typescript
import { FormattedResume, tryParseJSON, jsonToPlainText } from '../../components/FormattedResume'

// Парсинг JSON (с markdown code block stripping)
const optimizedData = useMemo(() => {
    if (result?.rewritten_data && typeof result.rewritten_data === 'object') {
        return result.rewritten_data
    }
    if (rewrittenRaw) {
        return tryParseJSON(rewrittenRaw)
    }
    return null
}, [result, rewrittenRaw])

// В секции "Оптимизировано":
{optimizedData ? (
    <FormattedResume data={optimizedData} />
) : (
    <FormattedPlainText text={rewrittenText} />
)}

// Для diff comparison:
const optimizedPlainText = optimizedData ? jsonToPlainText(optimizedData) : rewrittenText
```

**Шаг 3:** В ResumeViewerModal.tsx — импортировать из FormattedResume.tsx вместо дублирования.

**Шаг 4:** Добавить в FormattedResume недостающие секции:
- `certifications` — список сертификатов с датами (иконка Award)
- `projects` — список проектов с описаниями (иконка FolderOpen)
- `languages` — список языков с уровнями (иконка Globe)

### Файлы для изменения

1. `frontend/src/components/FormattedResume.tsx` — **СОЗДАТЬ** (вынести из ResumeViewerModal.tsx)
2. `frontend/src/pages/wizard/ResultsPage.tsx` — **ИЗМЕНИТЬ** (использовать FormattedResume + tryParseJSON)
3. `frontend/src/components/ResumeViewerModal.tsx` — **ИЗМЕНИТЬ** (импортировать из FormattedResume.tsx)

### Критерий приёмки

- [ ] Anthropic Claude JSON в ```json...``` корректно парсится
- [ ] OpenAI JSON отображается как rich HTML (не plain text)
- [ ] Секции: contacts, summary, experience, education, skills, certifications, projects, languages
- [ ] Стиль идентичен ResumeViewerModal (иконки, badges, spacing)
- [ ] Diff comparison работает (jsonToPlainText для word-level diff)
- [ ] Fallback на plain text если JSON не парсится

---

## 🔴 ДЕФЕКТ 2 — NEW-V22-001: ATS оценка "D" = "Отлично"

### Проблема

На странице `/app/results` ATS совместимость "D" отображается с подписью **"Отлично"**. Оценка D — это плохой результат, не "Отлично".

### Воспроизведение
1. Оптимизировать резюме через любой провайдер
2. Перейти на /app/results
3. Увидеть: ATS совместимость → D → "Отлично"

### Как исправить

```typescript
// ResultsPage.tsx — маппинг ATS grade → label и цвет
function getAtsInfo(grade: string): { label: string; color: string } {
    switch (grade?.toUpperCase()) {
        case 'A+': case 'A': return { label: 'Отлично', color: 'var(--success)' }
        case 'A-': case 'B+': return { label: 'Хорошо', color: '#22C55E' }
        case 'B': case 'B-': return { label: 'Выше среднего', color: '#84CC16' }
        case 'C+': case 'C': return { label: 'Средне', color: 'var(--warning, #F59E0B)' }
        case 'C-': case 'D+': return { label: 'Ниже среднего', color: '#F97316' }
        case 'D': case 'D-': return { label: 'Требует доработки', color: 'var(--danger, #EF4444)' }
        case 'F': return { label: 'Критично', color: '#DC2626' }
        default: return { label: grade || 'N/A', color: 'var(--text-secondary)' }
    }
}
```

**Текущий код вероятно:** Всегда показывает "Отлично" или не маппит grade → label.

### Файлы для изменения

1. `frontend/src/pages/wizard/ResultsPage.tsx` — маппинг ATS grade → label

### Критерий приёмки

- [ ] A/A+ → "Отлично" (зелёный)
- [ ] B+/B → "Хорошо"/"Выше среднего" (светло-зелёный)
- [ ] C → "Средне" (жёлтый)
- [ ] D → "Требует доработки" (красный)
- [ ] F → "Критично" (тёмно-красный)

---

## 🔴 ДЕФЕКТ 3 — NEW-V22-002: Все компоненты Match Score идентичны

### Проблема

Секция "Компоненты Match Score" на /app/results показывает одинаковые значения для всех 4 компонентов:
- Ключевые слова: 42% (вес 40%)
- Опыт: 42% (вес 25%)
- Структура: 42% (вес 20%)
- Читаемость: 42% (вес 15%)

Все показывают 42% — это просто match_score дублированный на все компоненты.

### Как исправить

**Вариант A (Backend — правильный):** Backend должен возвращать отдельные scores для каждого компонента:
```python
# rewriter/tasks.py или scoring.py
def calculate_match_components(resume_data, vacancy_data):
    return {
        'keywords_score': calculate_keyword_match(resume_data, vacancy_data),
        'experience_score': calculate_experience_match(resume_data, vacancy_data),
        'structure_score': calculate_structure_score(resume_data),
        'readability_score': calculate_readability_score(resume_data),
    }
```

**Вариант B (Frontend — временный фикс):** Если backend пока не может рассчитать компоненты отдельно, скрыть секцию "Компоненты Match Score" или показать disclaimer "Детальная разбивка в разработке".

### Файлы для изменения

1. `src/app/rewriter/tasks.py` или `scoring.py` — раздельный расчёт компонентов
2. `src/app/rewriter/router.py` — возвращать component scores
3. `frontend/src/pages/wizard/ResultsPage.tsx` — отображать реальные компоненты

### Критерий приёмки

- [ ] Каждый компонент Match Score имеет уникальное значение
- [ ] ИЛИ секция скрыта/заменена disclaimer если backend не поддерживает

---

## 🔴 ДЕФЕКТ 4 — NEW-V22-004: Raw API error leak на History

### Проблема

На странице "История" для failed оптимизации отображается полный raw API error:
```
Ошибка: LLM-провайдер openai: Error code: 400 - {'error': {'message': "Unsupported parameter: 'max_tokens'...", 'type': 'invalid_request_error', 'param': 'max_tok временно недоступен
```

### Как исправить

```python
# Backend: rewriter/tasks.py — при ошибке LLM
try:
    result = await llm_client.generate(...)
except Exception as e:
    # Сохранять полную ошибку в лог
    logger.error(f"LLM error for task {task_id}: {e}")
    # Но в task.error_message сохранять user-friendly текст
    task.error_message = "Оптимизация не удалась. Попробуйте другую модель или повторите позже."
    task.status = TaskStatus.FAILED
```

```typescript
// Frontend: HistoryPage или компонент отображения истории
// Показывать user-friendly текст вместо raw error
const displayError = task.error_message?.includes('Error code:')
    ? 'Оптимизация не удалась. Попробуйте другую модель.'
    : task.error_message
```

### Файлы для изменения

1. `src/app/rewriter/tasks.py` — user-friendly error messages при LLM ошибках
2. Frontend history component — fallback на user-friendly текст

### Критерий приёмки

- [ ] Пользователь НЕ видит: Error code, JSON, parameter names, type
- [ ] Пользователь видит: "Оптимизация не удалась. Попробуйте другую модель."

---

## 🟡 ДЕФЕКТ 5 — NEW-V22-003: Счётчик оптимизаций не обновляется в реальном времени

### Проблема

После завершения оптимизации счётчик в sidebar показывает старое значение. Обновляется только при переходе на другую страницу.

### Как исправить

```typescript
// После получения результата оптимизации на ProcessingPage или ResultsPage:
await refreshUser() // Обновить данные пользователя включая optimizations_used
```

ИЛИ в Sidebar/Layout компоненте:
```typescript
// Подписаться на events или polling при изменении маршрута
useEffect(() => {
    refreshUser()
}, [location.pathname])
```

### Файлы для изменения

1. `frontend/src/pages/wizard/ProcessingPage.tsx` — вызвать refreshUser() при completion
2. `frontend/src/pages/wizard/ResultsPage.tsx` — вызвать refreshUser() при mount

### Критерий приёмки

- [ ] Счётчик обновляется сразу после завершения оптимизации

---

## 🟡 ДЕФЕКТ 6 — NEW-V22-007: Download dropdown — только DOCX

### Проблема

На странице "Мои резюме" dropdown для скачивания оптимизированного резюме показывает только "Скачать DOCX". В модальном окне (ResumeViewerModal) все 3 формата (DOCX, PDF, TXT) доступны.

### Как исправить

В `ResumesPage.tsx` добавить все 3 формата в dropdown:
```typescript
// ResumesPage.tsx — dropdown items
{openDropdownId === r.id && (
    <div style={{ position: 'absolute', top: '100%', right: 0, zIndex: 200, ... }}>
        <button onClick={() => handleExport(r.id, 'docx')}>
            <FileText size={14} /> Скачать DOCX
        </button>
        <button onClick={() => handleExport(r.id, 'pdf')}>
            <FileText size={14} /> Скачать PDF
        </button>
        <button onClick={() => handleExport(r.id, 'txt')}>
            <FileText size={14} /> Скачать TXT
        </button>
    </div>
)}
```

### Файлы для изменения

1. `frontend/src/pages/resumes/ResumesPage.tsx` — добавить PDF и TXT в dropdown

### Критерий приёмки

- [ ] Dropdown показывает 3 формата: DOCX, PDF, TXT
- [ ] Все 3 формата скачиваются корректно

---

## 🟡 ДЕФЕКТ 7 — NEW-V21-004: Non-atomic optimizations_used counter (из V21)

### Проблема

```python
user.optimizations_used += 1  # Python-level increment — race condition
```

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

1. `src/app/rewriter/service.py` — SQL expression вместо Python increment

---

## 🟡 ДЕФЕКТ 8 — NEW-V21-005: session.flush() без commit() (из V21)

### Необходимое действие

Верифицировать что FastAPI middleware (get_session) делает `await session.commit()` после каждого request.

### Файлы для проверки

1. `src/app/core/database.py` — get_session dependency

---

## 🟢 ДЕФЕКТ 9 — NEW-V22-005: Avatar initials hardcoded "АП"

### Проблема

`SettingsProfilePage.tsx:96` — аватар без фото показывает "АП" вместо реальных инициалов.

### Как исправить

```typescript
// SettingsProfilePage.tsx
const initials = useMemo(() => {
    const first = form.firstName?.[0] || ''
    const last = form.lastName?.[0] || ''
    return (first + last).toUpperCase() || 'U'
}, [form.firstName, form.lastName])

// В JSX:
{!avatarUrl && initials}  // вместо hardcoded 'АП'
```

### Файлы для изменения

1. `frontend/src/pages/settings/SettingsProfilePage.tsx` — динамические инициалы

---

## 🟢 ДЕФЕКТ 10 — NEW-V21-002: useState side-effect (из V21)

### Как исправить

```typescript
// SettingsProfilePage.tsx:23-26
// ЗАМЕНИТЬ useState на useEffect:
useEffect(() => {
    const oldKey = `user_avatar_${user?.id || 'default'}`
    try { localStorage.removeItem(oldKey) } catch { /* ignore */ }
}, [user?.id])
```

### Файлы для изменения

1. `frontend/src/pages/settings/SettingsProfilePage.tsx` — строки 23-26

---

## 🟢 ДЕФЕКТ 11 — NEW-V22-008: API key status icons

### Проблема

При сохранении API ключа зелёная галочка на карточке провайдера не появляется сразу.

### Как исправить

После успешного сохранения ключа — вызвать `refreshUser()` или обновить локальное состояние карточек.

---

## 🟢 ДЕФЕКТ 12 — NEW-V21-006: z-index dropdown (из V21)

```typescript
// ResumesPage.tsx:258
zIndex: 200, // было 100
```

---

## 🟢 ДЕФЕКТ 13 — NEW-V21-007: OpenRouter fallback list (из V21)

Добавить timestamp и комментарий:
```typescript
// Last updated: 2026-03-08. Update quarterly.
const FALLBACK_SUB_MODELS: Record<string, SubModel[]> = {
```

---

## ПРИОРИТЕТЫ ИСПРАВЛЕНИЯ

### Sprint 1 (Критичный — 1-2 дня)
1. **P0-3** — ResultsPage: FormattedResume + tryParseJSON с markdown stripping
2. **NEW-V22-001** — ATS grade → label маппинг (D ≠ "Отлично")
3. **NEW-V22-002** — Match Score components (скрыть или исправить backend)
4. **NEW-V22-004** — Raw error leak → user-friendly messages

### Sprint 2 (Важный — 3-5 дней)
5. **NEW-V22-003** — Счётчик оптимизаций real-time update
6. **NEW-V22-007** — Download dropdown 3 формата
7. **NEW-V21-004** — Atomic counter
8. **NEW-V21-005** — Верификация session.flush/commit

### Sprint 3 (Улучшения)
9. **NEW-V22-005** — Avatar initials
10. **NEW-V21-002** — useState → useEffect
11. **NEW-V22-008** — API key status real-time
12. **NEW-V21-006** — z-index increase
13. **NEW-V21-007** — Fallback list maintenance

---

## ЗАКРЫТЫЕ ДЕФЕКТЫ (из V20/V21)

| ID | Описание | Вердикт |
|----|----------|---------|
| P0-4 | OpenAI o-series max_tokens | ✅ FIXED — llm_client.py o-series detection |
| FEATURE-002 | Download dropdown existence | ✅ FIXED — dropdown существует (но только DOCX) |
| NEW-V20-001 | OpenRouter только 3 модели | ✅ FIXED — 346 моделей от сервера + 16 fallback |
| NEW-V18-002 | Progress bar 0% | ✅ FIXED — simulated progress animation |
| FEATURE-005 | DOCX viewer | ✅ FIXED — mammoth + DOMPurify |
| UX-001 | Клик по имени → модал | ✅ FIXED — onClick с handleView |
| NEW-V20-003 | DELETE /me → 500 | ✅ FIXED — soft-delete с 30-дневным recovery |

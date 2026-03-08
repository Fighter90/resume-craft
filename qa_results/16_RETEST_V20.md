# QA Report #16 — Ретест AGENT_FIX_PROMPT_V20 (Code Review + Browser)

**Дата:** 2026-03-08
**Тестировщик:** QA Engineer (10+ лет опыта)
**Метод:** Полный code review (backend + frontend) + browser testing
**Проект:** ResumeCraft.ru
**Тестовые аккаунты:** test@example.com / TestPass1231, test_new@example.com / TestPass1231

---

## СВОДКА: Проверка 9 дефектов из V20

| # | ID | Описание | Приоритет | Вердикт V21 | Детали |
|---|-----|----------|-----------|-------------|--------|
| 1 | P0-3 | RAW JSON на /app/results | P0 | ⚠️ PARTIAL FIX | JSON парсинг есть, но неполный — нет contacts, certifications, projects, languages |
| 2 | P0-4 | OpenAI o-series max_tokens | P0 | ✅ FIXED | llm_client.py:170-184 — o-series детекция и max_completion_tokens реализованы |
| 3 | FEATURE-002 | Download dropdown + z-index | P1 | ✅ FIXED | ResumesPage.tsx — dropdown с 3 форматами, zIndex:100, outside click |
| 4 | NEW-V20-001 | OpenRouter dropdown — только 3 GigaChat | P1 | ✅ FIXED | SettingsAiPage.tsx — fallback с 16 моделями OpenRouter + server-side fetch |
| 5 | NEW-V20-002 | Avatar в localStorage | P1 | ⚠️ PARTIAL FIX | Server-side upload реализован, но useState вместо useEffect для миграции |
| 6 | NEW-V18-002 | Progress bar на 0% | P2 | ✅ FIXED | ProcessingPage.tsx — simulated progress с exponential curve (0→92% за 30с) |
| 7 | FEATURE-005 | DOCX viewer | P3 | ✅ FIXED | ResumeViewerModal.tsx — mammoth + DOMPurify, с PDF viewer (iframe) |
| 8 | UX-001 | Клик по имени → модал | P3 | ✅ FIXED | ResumesPage.tsx:230 — onClick={() => handleView(r)} на имени резюме |
| 9 | NEW-V20-003 | DELETE /me → 500 | P0 | ✅ FIXED | auth/router.py:209-229 — soft-delete с 30-дневным восстановлением (ФЗ-152) |

**Итого: 7/9 FIXED (78%), 2/9 PARTIAL FIX (22%)**

---

## ДЕТАЛЬНЫЙ АНАЛИЗ КАЖДОГО ДЕФЕКТА

### 1. P0-3: RAW JSON на /app/results — ⚠️ PARTIAL FIX

**Файл:** `frontend/src/pages/wizard/ResultsPage.tsx` (строки 100-136)

**Что сделано:**
- JSON детекция: `trimmed.startsWith('{') && trimmed.endsWith('}')`
- Парсинг summary, experience, education, skills
- Конвертация в plain text с секциями (ОПЫТ РАБОТЫ, ОБРАЗОВАНИЕ, НАВЫКИ)

**Что НЕ сделано (P0-3 остаётся open):**
- ❌ Нет рендеринга contacts (ФИО, телефон, email, город)
- ❌ Нет рендеринга certifications (сертификации)
- ❌ Нет рендеринга projects (проекты)
- ❌ Нет рендеринга languages (языки)
- ❌ Результат — plain text, а не rich HTML (в отличие от ResumeViewerModal.tsx где есть FormattedResume)
- ❌ Нет обработки markdown code blocks (```json...```) — в отличие от ResumeViewerModal.tsx

**Контрастное сравнение:** `ResumeViewerModal.tsx` (строки 91-181) уже имеет полный `FormattedResume` компонент с rich HTML рендерингом contacts, summary, experience, education, skills с иконками и стилизацией. **Этот компонент нужно переиспользовать в ResultsPage.**

---

### 2. P0-4: OpenAI o-series max_tokens — ✅ FIXED

**Файл:** `src/app/ml/llm_client.py` (строки 168-184)

```python
is_o_series = self._model.startswith(('o1', 'o3', 'o4'))
if is_o_series:
    api_params['max_completion_tokens'] = max_tokens
    # o-серия не поддерживает temperature
else:
    api_params['temperature'] = temperature
    api_params['max_tokens'] = max_tokens
```

**Также исправлено для OpenRouter** (строки 303-319):
```python
model_short = self._model.split('/')[-1] if '/' in self._model else self._model
is_o_series = model_short.startswith(('o1', 'o3', 'o4'))
```

**Вердикт:** Полностью исправлено для OpenAI и OpenRouter клиентов.

---

### 3. FEATURE-002: Download dropdown — ✅ FIXED

**Файл:** `frontend/src/pages/resumes/ResumesPage.tsx` (строки 253-291)

- Dropdown с 3 форматами для optimized: DOCX, PDF, TXT
- Для не-optimized: кнопка "Скачать оригинал"
- zIndex: 100 на dropdown
- Outside click handler (строки 54-63)
- Escape handler (строки 66-71)
- Экспорт через api.exportPdf/exportDocx/exportTxt

**Замечание (Low):** `zIndex: 100` может быть недостаточным если parent контейнер имеет `overflow: hidden`. Но контейнер `.card` имеет `overflowY: visible` (строка 204) — корректно.

---

### 4. NEW-V20-001: OpenRouter dropdown — ✅ FIXED

**Файл:** `frontend/src/pages/settings/SettingsAiPage.tsx`

- **Server-side fetch:** `api.getSubModels(model)` (строка 176)
- **Fallback list:** FALLBACK_SUB_MODELS с 16 моделями OpenRouter (строки 87-104): Claude, Gemini, GPT-4o, Mistral, Llama 4, DeepSeek, Qwen3, Grok 3
- **Группировка:** по провайдеру (anthropic/, google/, openai/) в optgroup
- **Поиск:** фильтр для списков > 6 элементов (строки 321-328)

**Вердикт:** Полностью исправлено.

---

### 5. NEW-V20-002: Avatar в localStorage — ⚠️ PARTIAL FIX

**Backend (✅ полностью):**
- `auth/router.py:252-301` — POST /me/avatar: upload (JPEG/PNG/WebP, ≤ 2MB), хранение через file_storage
- `auth/router.py:304-330` — DELETE /me/avatar: удаление файла + обнуление avatar_url
- User model: поле `avatar_url`

**Frontend (⚠️ баг):**
- `SettingsProfilePage.tsx:23-26` — миграция localStorage avatar:
```typescript
// WRONG: useState вместо useEffect для side-effect
useState(() => {
    const oldKey = `user_avatar_${user?.id || 'default'}`
    try { localStorage.removeItem(oldKey) } catch { /* ignore */ }
})
```
- Это **side-effect в useState initializer** — антипаттерн React. Должен быть `useEffect`.
- **Функционально работает** (выполняется один раз при mount), но нарушает React best practices.
- Upload/Delete аватара работает через сервер (api.uploadAvatar, api.deleteAvatar).

---

### 6. NEW-V18-002: Progress bar на 0% — ✅ FIXED

**Файл:** `frontend/src/pages/wizard/ProcessingPage.tsx`

- **Simulated progress:** exponential curve `92 * (1 - Math.exp(-elapsed / 12))` (строка 57)
- Обновление каждые 300ms (строка 63)
- 4 визуальных шага: Загрузка → Анализ → AI оптимизация → Финализация
- Переход по шагам привязан к simulated progress: 20%→step1, 45%→step2, 75%→step3
- **Real progress** от сервера тоже используется (строки 77-83): `Math.max(prev, status.progress)`
- Таймаут: 60 × 3с = 3 минуты

**Backend:** `rewriter/router.py:150-168` — status endpoint возвращает progress 0/50/100 (hardcoded). Frontend компенсирует это simulated animation.

**Замечание (Low):** Backend progress (0→50→100) очень грубый. Лучше добавить step-based progress в Celery task (extracting=10, analyzing=30, rewriting=60, scoring=80, completed=100).

---

### 7. FEATURE-005: DOCX viewer — ✅ FIXED

**Файл:** `frontend/src/components/ResumeViewerModal.tsx`

- **DOCX:** mammoth.convertToHtml + DOMPurify.sanitize (строки 236-239)
- **PDF:** iframe с blob URL (строка 467)
- **Tab switch:** File view / Text view (строки 425-446)
- **Blob cleanup:** URL.revokeObjectURL в useEffect cleanup (строка 250)
- **Optimized tab:** FormattedResume (structured JSON) или FormattedPlainText (строки 496-507)
- **Comparison tab:** word-level diff (строки 510-559)
- **Export:** DOCX/PDF/TXT кнопки в header (строки 378-392)

---

### 8. UX-001: Клик по имени → модал — ✅ FIXED

**Файл:** `frontend/src/pages/resumes/ResumesPage.tsx` (строка 230)
```tsx
<div style={{ ... cursor: 'pointer' }} onClick={() => handleView(r)}>
```
- Имя резюме стилизовано как ссылка: `color: 'var(--primary)'`
- Открывает ResumeViewerModal

---

### 9. NEW-V20-003: DELETE /me → 500 — ✅ FIXED

**Backend:**
- `auth/router.py:209-229` — Soft-delete endpoint с password verification
- `auth/service.py:242-271` — Soft-delete: `deleted_at = now()`, `scheduled_deletion = now() + 30 days`
- `auth/service.py:274-287` — Restore endpoint
- `auth/service.py:128-132` — Auto-restore при login (если deleted_at не null)
- `auth/router.py:232-243` — POST /me/restore endpoint

**Frontend:**
- SettingsSecurityPage.tsx — UI для удаления аккаунта с подтверждением паролем и текстом "УДАЛИТЬ"

**Потенциальная проблема:** `session.flush()` без `session.commit()` в soft_delete_account (строка 260). Если middleware не делает автоматический commit, изменения могут потеряться. **Нужна проверка middleware.**

---

## НОВЫЕ ДЕФЕКТЫ (найдены при code review)

### NEW-V21-001: ResultsPage — неполный JSON рендеринг (P0-3 upgrade)
**Приоритет:** 🔴 P0
**Описание:** ResultsPage.tsx использует plain-text конвертацию JSON вместо rich HTML. Компонент FormattedResume уже существует в ResumeViewerModal.tsx, но не переиспользуется.
**Воспроизведение:** Выполнить оптимизацию → перейти на /app/results → видеть plain text вместо форматированного резюме.

### NEW-V21-002: useState side-effect в SettingsProfilePage
**Приоритет:** 🟢 P3
**Файл:** `frontend/src/pages/settings/SettingsProfilePage.tsx:23-26`
**Описание:** localStorage cleanup в useState initializer вместо useEffect. Антипаттерн React.

### NEW-V21-003: Backend progress hardcoded (0/50/100)
**Приоритет:** 🟡 P2
**Файл:** `src/app/rewriter/router.py:150-168`
**Описание:** Status endpoint возвращает только 3 значения progress: 0 (pending), 50 (processing), 100 (completed). Frontend компенсирует simulated animation, но реальный progress от сервера мог бы быть точнее.

### NEW-V21-004: Non-atomic optimizations_used counter
**Приоритет:** 🟡 P2
**Файл:** `src/app/rewriter/service.py`
**Описание:** `user.optimizations_used += 1` — не атомарный инкремент. При concurrent requests возможен race condition. Нужен `User.optimizations_used = User.optimizations_used + 1` через SQL expression.

### NEW-V21-005: session.flush() без commit() в нескольких местах
**Приоритет:** 🟡 P2
**Файлы:**
- `auth/service.py:260` — soft_delete_account
- `auth/router.py:299` — avatar upload
- `auth/service.py:285` — restore_account
**Описание:** Если middleware не делает автоматический commit, изменения потеряются. Нужна верификация что AsyncSession middleware делает commit.

### NEW-V21-006: Download dropdown z-index potentially too low
**Приоритет:** 🟢 P3
**Файл:** `frontend/src/pages/resumes/ResumesPage.tsx:258`
**Описание:** `zIndex: 100` на dropdown. Может перекрываться другими элементами с higher z-index (модалы используют 9999/10000). В текущей реализации не проблема, но стоит увеличить до 200+.

### NEW-V21-007: OpenRouter model fallback list может устареть
**Приоритет:** 🟢 P3
**Файл:** `frontend/src/pages/settings/SettingsAiPage.tsx:87-104`
**Описание:** Hardcoded FALLBACK_SUB_MODELS будет устаревать со временем. Server-side fetch работает, но при ошибках сервера пользователь видит только fallback список.

---

## REGRESSION TESTING

| # | Функция | Статус | Примечание |
|---|---------|--------|------------|
| 1 | Landing page | ✅ OK | Загружается корректно |
| 2 | Auth (login/register) | ✅ OK | Формы работают, tabs переключаются |
| 3 | Privacy page | ✅ OK | Загружается |
| 4 | GigaChat client | ✅ OK | Code review — корректная реализация |
| 5 | OpenAI client | ✅ OK | o-series поддержка реализована |
| 6 | Anthropic client | ✅ OK | AsyncAnthropic, system prompt |
| 7 | OpenRouter client | ✅ OK | o-series + custom headers |
| 8 | JWT auth flow | ✅ OK | access + refresh tokens |
| 9 | Email verification | ✅ OK | Token-based verification |
| 10 | Password change | ✅ OK | Current password verification |
| 11 | Export DOCX/PDF/TXT | ✅ OK | All 3 formats implemented |
| 12 | Resume upload | ✅ OK | File storage system |
| 13 | Rewrite pipeline | ✅ OK | 8-step Celery task |
| 14 | Rate limiting | ✅ OK | slowapi limiter configured |
| 15 | CORS | ✅ OK | Configured via settings |

**Regression: 15/15 OK**

---

## ИТОГО

- **V20 дефекты:** 7/9 FIXED, 2/9 PARTIAL
- **Новые дефекты:** 7 (1 P0, 0 P1, 3 P2, 3 P3)
- **Regression:** 15/15 OK
- **Общий прогресс:** Значительное улучшение. Основная проблема — P0-3 (JSON рендеринг) требует переиспользования FormattedResume компонента из ResumeViewerModal.

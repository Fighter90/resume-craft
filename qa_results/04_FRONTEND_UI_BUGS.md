# QA Report #04 — БАГИ ФРОНТЕНДА И UI

**Проект:** ResumeCraft v1.5
**Дата:** 2026-03-06
**Тестировщик:** QA Engineer (10+ лет опыта)
**Метод:** Статический анализ React-компонентов, контекстов, API-клиента

---

## UI-001: XSS через dangerouslySetInnerHTML в описании вакансии

**Severity:** 🔴 CRITICAL
**Файлы:**
- `frontend/src/pages/wizard/VacancyPage.tsx` (строки 392, 400, 410)
- `frontend/src/pages/wizard/ResultsPage.tsx` (строка 394)
**Категория:** CWE-79 (Cross-Site Scripting)

### Описание
HTML-контент вакансий с hh.ru рендерится через `dangerouslySetInnerHTML` без санитизации:

```jsx
// VacancyPage.tsx — 3 уязвимых места
dangerouslySetInnerHTML={{ __html: detailVacancy.description }}
dangerouslySetInnerHTML={{ __html: detailVacancy.snippet.requirement }}
dangerouslySetInnerHTML={{ __html: detailVacancy.snippet.responsibility }}

// ResultsPage.tsx — 1 уязвимое место
dangerouslySetInnerHTML={{ __html: vacancy.description }}
```

### Тест-кейс
1. Создать вакансию вручную (таб "Ввести вручную")
2. В описание вставить: `<img src=x onerror="alert(document.cookie)">`
3. Открыть подробности вакансии → модальное окно
4. **Фактический результат:** Скрипт выполняется, XSS в контексте авторизованного пользователя

### Вектор атаки через hh.ru
Даже при парсинге данных с hh.ru, API может вернуть HTML с вредоносными тегами. Если описание вакансии содержит `<script>` или обработчики событий, они будут выполнены.

### Рекомендация
Использовать DOMPurify для санитизации HTML:
```jsx
import DOMPurify from 'dompurify'
dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(description) }}
```

---

## UI-002: Фейковый breakdown компонентов Match Score

**Severity:** 🟡 MEDIUM
**Файл:** `frontend/src/pages/wizard/ResultsPage.tsx` (строки 186–191)

### Описание
Компоненты Match Score (Keywords, Experience, Structure, Readability) вычисляются фейковыми формулами на основе общего балла:

```jsx
{ label: 'Ключевые слова', value: Math.round(score * 0.4 / 0.4) }, // = score (!)
{ label: 'Опыт',           value: Math.round(score * 0.95) },
{ label: 'Структура',      value: Math.round(score * 0.9) },
{ label: 'Читаемость',     value: Math.round(score * 0.85) },
```

- `Keywords` = `score * 0.4 / 0.4` = `score` (само на себя)
- `Experience` = `score * 0.95` (просто 95% от общего)
- `Structure` = `score * 0.9`
- `Readability` = `score * 0.85`

### Тест-кейс
1. Выполнить оптимизацию с Match Score = 80
2. Посмотреть компоненты на странице результатов
3. **Фактический:** Keywords = 80%, Experience = 76%, Structure = 72%, Readability = 68%
4. **Ожидаемый:** Реальные значения из scoring.py (TF-IDF=40%, cosine=25%, sections=20%, readability=15%)

### Влияние
Пользователь видит фейковую детализацию. "Ключевые слова" всегда равны общему баллу. Подрывает доверие к сервису.

### Рекомендация
Бэкенд должен возвращать реальные компоненты Match Score из `scoring.py`, а не вычислять их на фронтенде.

---

## UI-003: Регистрация без подтверждения пароля

**Severity:** 🟡 MEDIUM
**Файл:** `frontend/src/pages/auth/AuthPage.tsx` (строки 146–183)

### Описание
Форма регистрации содержит только одно поле пароля. Нет:
- Повторного ввода пароля для подтверждения
- Индикатора сложности пароля
- Подсказок по требованиям (кроме плейсхолдера "Минимум 8 символов")

### Тест-кейс
1. Открыть страницу регистрации
2. Ввести email и пароль с опечаткой
3. **Фактический:** Аккаунт создан с неправильным паролем, пользователь не может войти
4. **Ожидаемый:** Поле "Подтвердите пароль" предотвращает опечатку

### Контраст с Security Settings
На странице смены пароля (`SettingsSecurityPage.tsx`) поле подтверждения **есть** (строка 43):
```jsx
if (pwForm.newPw !== pwForm.confirm) {
  setPwMessage({ type: 'error', text: 'Пароли не совпадают' })
```
Но при регистрации его нет — непоследовательный UX.

### Рекомендация
Добавить поле "Подтвердите пароль" и индикатор сложности при регистрации.

---

## UI-004: JWT-токены хранятся в localStorage

**Severity:** 🟡 MEDIUM
**Файлы:**
- `frontend/src/services/api.ts` (строки 8, 18)
- `frontend/src/contexts/AuthContext.tsx` (строки 28, 68–69, 79–80)

### Описание
Токены access_token и refresh_token хранятся в `localStorage`:
```typescript
// api.ts
localStorage.setItem('access_token', token)

// AuthContext.tsx
localStorage.setItem('access_token', data.access_token)
localStorage.setItem('refresh_token', data.refresh_token)
```

### Риски
- Доступны через `document.cookie` — нет, но через XSS (UI-001) доступен `localStorage.getItem('access_token')`
- Не очищаются при закрытии браузера (в отличие от sessionStorage)
- refresh_token (30 дней TTL) остаётся доступным

### Тест-кейс
1. Войти в систему
2. Открыть DevTools → Application → Local Storage
3. **Фактический:** `access_token` и `refresh_token` видны в открытом виде
4. Эксплуатация: XSS-атака через UI-001 → `fetch('/api/v1/auth/me', {headers: {'Authorization': 'Bearer ' + localStorage.getItem('access_token')}})`

### Рекомендация
Использовать httpOnly cookies для токенов. Если localStorage необходим — минимизировать время жизни access_token и использовать автоматический refresh.

---

## UI-005: Нет автоматического обновления токена при 401

**Severity:** 🟡 MEDIUM
**Файл:** `frontend/src/services/api.ts` (строки 23–35)

### Описание
Метод `request()` не перехватывает ошибку 401 для автоматического обновления токена:
```typescript
private async request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(...)
  if (!res.ok) {
    const err = await res.json().catch(...)
    throw new Error(err.message || err.detail || res.statusText)
    // Нет перехвата 401 → нет retry с refresh_token
  }
}
```

### Тест-кейс
1. Войти в систему
2. Подождать >30 минут (access_token TTL)
3. Нажать кнопку "Оптимизировать"
4. **Фактический:** Ошибка "Unauthorized", пользователь видит экран ошибки
5. **Ожидаемый:** Автоматический refresh и повтор запроса

### Рекомендация
Добавить interceptor:
```typescript
if (res.status === 401) {
  const newToken = await this.refreshToken(...)
  // Retry original request with new token
}
```

---

## UI-006: alert() вместо UI-компонента ошибки

**Severity:** 🟢 LOW
**Файл:** `frontend/src/pages/settings/SettingsSecurityPage.tsx` (строка 27)

### Описание
```jsx
} catch (err) {
  alert(err instanceof Error ? err.message : 'Ошибка удаления аккаунта')
}
```

Удаление аккаунта использует `alert()` для отображения ошибок. Это выбивается из общего дизайна приложения, где все остальные ошибки отображаются через inline-уведомления.

### Рекомендация
Использовать состояние и inline-блок ошибки (как `pwMessage` в том же файле).

---

## UI-007: Плейсхолдеры 2FA и Active Sessions

**Severity:** 🟢 LOW (информационное)
**Файл:** `frontend/src/pages/settings/SettingsSecurityPage.tsx` (строки 97–114)

### Описание
Два блока на странице безопасности показаны с `opacity: 0.6` и текстом "Будет доступно в следующем обновлении":
- Двухфакторная аутентификация
- Активные сессии

### Влияние
- Пользователь видит неработающие функции → создаёт ощущение незрелости продукта
- В production рекомендуется убирать или заменять на лист ожидания

---

## UI-008: Polling без очистки при unmount в ProcessingPage

**Severity:** 🟡 MEDIUM
**Файл:** `frontend/src/pages/wizard/ProcessingPage.tsx` (строки 47–84)

### Описание
Polling реализован через `setInterval` с cleanup в useEffect return:
```jsx
pollingRef.current = setInterval(poll, 3000)
return () => { if (pollingRef.current) clearInterval(pollingRef.current) }
```

Проблемы:
1. Если пользователь уходит со страницы и возвращается — новый интервал создаётся, но `setResult()` может обновить уже unmounted компонент
2. Нет maxRetries — polling бесконечен если задача зависла на сервере
3. `eslint-disable react-hooks/exhaustive-deps` скрывает потенциальные баги с зависимостями

### Тест-кейс
1. Запустить оптимизацию
2. Во время обработки быстро уйти на другую страницу и вернуться
3. **Возможный результат:** Два параллельных polling-а или React warning "Can't perform state update on unmounted component"

### Рекомендация
Добавить AbortController, maxRetries, и проверку mounted-состояния.

---

## UI-009: computeWordDiff — ложный diff на одинаковых словах

**Severity:** 🟢 LOW
**Файл:** `frontend/src/pages/wizard/ResultsPage.tsx` (строки 10–28)

### Описание
Алгоритм diff основан на множествах (Set), а не на позиционном сравнении:
```javascript
const origSet = new Set(origWords.filter(w => w.trim()).map(w => w.trim().toLowerCase()))
const newSet = new Set(newWords.filter(w => w.trim()).map(w => w.trim().toLowerCase()))
```

Это приводит к:
- Повторяющиеся слова ("и", "в", "на") не будут подсвечены, даже если их позиция/количество изменилось
- Если слово есть в обоих текстах в разных местах — оно не выделяется как изменённое

### Тест-кейс
1. Оригинал: "Разработка программного обеспечения и тестирование программного кода"
2. Оптимизировано: "Тестирование программного кода и разработка программного обеспечения"
3. **Фактический:** Нет подсветки изменений (все слова есть в обоих множествах)
4. **Ожидаемый:** Показан перенос блоков текста

### Рекомендация
Использовать библиотеку `diff-match-patch` или `jsdiff` для точного word-level diff.

---

## UI-010: Нет Error Boundary для React-компонентов

**Severity:** 🟡 MEDIUM
**Файл:** Отсутствует в проекте

### Описание
В проекте нет React Error Boundary. Любая необработанная ошибка в рендеринге компонента приведёт к белому экрану.

### Тест-кейс
1. Бэкенд возвращает `result.match_score_after = null` (не число)
2. `ResultsPage` пытается вычислить `circumference - (null / 100) * circumference`
3. **Фактический:** Белый экран, React crash
4. **Ожидаемый:** Fallback UI с кнопкой "Вернуться"

### Рекомендация
Добавить `<ErrorBoundary>` с fallback-компонентом, хотя бы на уровне маршрутов.

---

## UI-011: Logout не инвалидирует refresh_token на сервере надёжно

**Severity:** 🟡 MEDIUM
**Файл:** `frontend/src/contexts/AuthContext.tsx` (строки 31–42)

### Описание
```javascript
const logout = useCallback(() => {
  const rt = localStorage.getItem('refresh_token')
  if (rt) {
    api.serverLogout(rt).catch(() => {/* ignore errors on logout */})
  }
  // Клиентская очистка выполняется СРАЗУ, не дожидаясь ответа
  setUser(null)
  setToken(null)
  ...
}, [])
```

Проблемы:
- `serverLogout` вызывается fire-and-forget — ошибки игнорируются
- Если запрос не дойдёт до сервера, refresh_token остаётся валидным 30 дней
- Нет retry-механизма

### Рекомендация
Ждать ответа сервера или добавить retry при неудачном logout.

---

## UI-012: Маршрут /app/editor ведёт в никуда

**Severity:** 🟡 MEDIUM
**Файл:** `frontend/src/pages/wizard/ResultsPage.tsx` (строки 114, 277)

### Описание
Кнопка "Редактировать" ведёт на `/app/editor`:
```jsx
<button onClick={() => navigate('/app/editor')} className="btn btn-secondary">
  <Edit size={16} /> Редактировать
</button>
```

Файл `EditorPage.tsx` существует, но нет проверки что данные для редактирования загружены. Если пользователь перейдёт по прямой ссылке `/app/editor` — данные будут пустые.

### Рекомендация
Добавить guard: если `WizardContext` пуст — редирект на `/app/upload`.

---

## UI-013: Отсутствие debounce на поиске вакансий

**Severity:** 🟢 LOW
**Файл:** `frontend/src/pages/wizard/VacancyPage.tsx` (строки 68–87)

### Описание
Поиск вакансий срабатывает по нажатию Enter или кнопки. Но нет защиты от множественных быстрых кликов — каждый клик отправляет запрос к API hh.ru.

### Рекомендация
Добавить debounce и/или дизейбл кнопки на время запроса (частично реализовано через `disabled={searching}`).

---

## Сводная таблица

| ID | Severity | Описание | Статус v1.6 |
|----|----------|----------|-------------|
| UI-001 | 🔴 CRITICAL | XSS через dangerouslySetInnerHTML | ✅ FIXED |
| UI-002 | 🟡 MEDIUM | Фейковый breakdown Match Score | ✅ FIXED |
| UI-003 | 🟡 MEDIUM | Нет подтверждения пароля при регистрации | ✅ FIXED |
| UI-004 | 🟡 MEDIUM | JWT-токены в localStorage | ⏳ Phase 2 |
| UI-005 | 🟡 MEDIUM | Нет автообновления токена при 401 | ✅ FIXED |
| UI-006 | 🟢 LOW | alert() вместо UI ошибки | ✅ FIXED |
| UI-007 | 🟢 LOW | Плейсхолдеры 2FA и Sessions | ⏳ Phase 2 |
| UI-008 | 🟡 MEDIUM | Polling без maxRetries | ✅ FIXED |
| UI-009 | 🟢 LOW | Неточный word diff | ⏳ Phase 2 |
| UI-010 | 🟡 MEDIUM | Нет Error Boundary | ✅ FIXED |
| UI-011 | 🟡 MEDIUM | Fire-and-forget logout | ⏳ (by design) |
| UI-012 | 🟡 MEDIUM | Editor без guard на данные | ✅ FIXED |
| UI-013 | 🟢 LOW | Нет debounce на поиске | ⏳ (has disable) |

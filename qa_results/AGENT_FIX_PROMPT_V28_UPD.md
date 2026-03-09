# AGENT_FIX_PROMPT_V28 (ОБНОВЛЁННЫЙ)

> Промт для AI-агента на доработку проекта ResumeCraft.ru
> Создан на основе QA Report #23 + #24 (V28 New Account Test)
> Дата: 09.03.2026

---

## КОНТЕКСТ

Проведён полный ретест V28 (сервер v1.11.0) на **3 аккаунтах**, включая НОВЫЙ аккаунт test_qa_v28@example.com.

**Результат: Обнаружен НОВЫЙ баг KEY-CHECK-001 (P2 MEDIUM)** — новые пользователи не могут запустить оптимизацию, несмотря на корректно сохранённые API-ключи.

Открытые проблемы:
1. **KEY-CHECK-001** — оптимизация не видит сохранённые API-ключи на новом аккаунте (P2 MEDIUM, **NEW**)
2. **NAV-001** — ссылка «Обновить до Pro →» не работает при клике (P3 LOW, STILL OPEN)
3. **OPENAI-O4MINI** — не удалось верифицировать фикс (заблокирован KEY-CHECK-001) (P3 LOW)
4. **GIGACHAT-001** — ошибка биллинга на стороне Сбер GigaChat (НЕ баг приложения)

---

## ИСПРАВЛЕННЫЕ БАГИ (подтверждено на 3 аккаунтах)

| Bug ID | Описание | V28 |
|--------|----------|-----|
| P0-3-CLAUDE | RAW JSON в результатах Claude | ✅ CONFIRMED |
| GROQ-KEY | Ключ Groq не сохраняется | ✅ CONFIRMED |
| AVATAR-001 | Инициалы не соответствуют имени | ✅ CONFIRMED |
| LOGOUT-001 | Нет кнопки выхода | ✅ CONFIRMED |
| DASHBOARD-001 | «Недавние резюме» пустые | ✅ CONFIRMED |
| EMAIL-VERIFY-001 | Противоречие баннера верификации | ✅ CONFIRMED |
| RESET-001 | «Сбросить» удаляет ALL API-ключи | ✅ FIXED |

---

## 🔴 ДЕФЕКТ 1 (ПРИОРИТЕТ): KEY-CHECK-001 — Оптимизация не видит API-ключи (P2 MEDIUM)

**Severity:** P2 (Medium) — блокирует основной функционал для новых пользователей
**Страница:** /app/processing
**Статус:** NEW — воспроизведён 3 раза на test_qa_v28@example.com

### Описание
При попытке запустить оптимизацию с моделью OpenAI o4-mini, все 4 этапа показывают зелёные ✓ (Загрузка, Анализ, AI оптимизация, Финализация), затем ошибка:

```
Ошибка обработки
API-ключ не настроен

API-ключ для OpenAI не настроен. Для использования OpenAI необходимо указать
API-ключ в настройках или выбрать другую модель (например, OpenRouter).
```

### Доказательства что ключи СОХРАНЕНЫ

API-ключи подтверждены 3 независимыми методами:

1. **PUT API:** `PUT /api/v1/settings/ai-keys/openai` → `200 OK, {"has_key": true}`
2. **GET API:** `GET /api/v1/settings/ai-keys` → все 5 ключей `has_key: true`
3. **UI:** Страница /app/settings/ai → зелёные ✓ "Сохранён" для всех 5 ключей

### Предполагаемый Root Cause

Бэкенд-процесс оптимизации проверяет наличие API-ключа **по другому механизму**, нежели API настроек. Возможные варианты:

1. **Кэширование:** Optimization engine кэширует состояние ключей и не видит новые
2. **Race condition:** Асинхронное сохранение, ключ не успевает стать видимым
3. **Разные хранилища:** Settings API и Optimization engine читают из разных источников
4. **Session/user context:** Ключи привязаны к одному контексту, оптимизация проверяет другой

### Исправление

```python
# Файл: app/services/optimization/engine.py (или аналогичный)

# ПРОБЛЕМА: Оптимизация проверяет ключ не через тот же сервис, что Settings API

# РЕШЕНИЕ: Использовать единый источник данных для проверки ключей
async def check_api_key(user_id: int, provider: str) -> bool:
    # ДОЛЖНО использовать тот же сервис, что и /api/v1/settings/ai-keys
    key = await ai_keys_service.get_key(user_id, provider)
    return key is not None and len(key) > 0

# Проверить:
# 1. Нет ли отдельного кэша ключей в optimization engine
# 2. Совпадает ли user_id при запросе ключа из optimization контекста
# 3. Нет ли фильтрации по дате создания аккаунта или другому признаку
```

### Шаги воспроизведения
1. Создать новый аккаунт
2. Сохранить API-ключ OpenAI через PUT /api/v1/settings/ai-keys/openai
3. Подтвердить: GET /api/v1/settings/ai-keys → has_key: true
4. Подтвердить: UI /app/settings/ai → зелёная ✓
5. Загрузить резюме, ввести вакансию, выбрать OpenAI o4-mini
6. Нажать "Начать оптимизацию"
7. **Результат:** "API-ключ не настроен"

### ВАЖНО
Баг обнаружен ТОЛЬКО на НОВОМ аккаунте. На старых аккаунтах оптимизации работали ранее. Возможна специфика аккаунтов, созданных после определённого обновления.

---

## 🟡 ДЕФЕКТ 2: NAV-001 — «Обновить до Pro →» не кликается (P3 LOW)

**Severity:** P3 (Low)
**Страница:** Sidebar на всех /app/* страницах
**Статус:** STILL OPEN (с V25) — подтверждён на 3 аккаунтах

### Root Cause
React `onClick` обработчик на `<a class="plan-upgrade">` вызывает `e.preventDefault()`, блокируя нативную навигацию по `href`. onClick handler НЕ выполняет программную навигацию.

### Исправление

**ВАРИАНТ 1 (рекомендуется): React Router Link**
```tsx
// Файл: src/components/Sidebar.tsx (или аналогичный)

// БЫЛО:
<a
    href="/app/settings/subscription"
    className="plan-upgrade"
    onClick={(e) => {
        e.preventDefault(); // ← БЛОКИРУЕТ НАВИГАЦИЮ
    }}
>
    Обновить до Pro →
</a>

// ДОЛЖНО БЫТЬ:
import { Link } from 'react-router-dom';

<Link to="/app/settings/subscription" className="plan-upgrade">
    Обновить до Pro →
</Link>
```

**ВАРИАНТ 2: Если onClick нужен для аналитики**
```tsx
<a
    href="/app/settings/subscription"
    className="plan-upgrade"
    onClick={() => {
        trackEvent('upgrade_click');
        // НЕ вызывать e.preventDefault()!
    }}
>
    Обновить до Pro →
</a>
```

**ВАРИАНТ 3: SPA-навигация из onClick**
```tsx
const navigate = useNavigate();

<a
    href="/app/settings/subscription"
    className="plan-upgrade"
    onClick={(e) => {
        e.preventDefault();
        trackEvent('upgrade_click');
        navigate('/app/settings/subscription'); // ← ДОБАВИТЬ
    }}
>
    Обновить до Pro →
</a>
```

---

## ⚠️ ДЕФЕКТ 3: OPENAI-O4MINI — max_tokens для o4-mini (P3 LOW)

**Severity:** P3 (Low)
**Статус:** НЕ ВЕРИФИЦИРОВАН — заблокирован KEY-CHECK-001

### Описание
При оптимизации с openai:o4-mini API возвращает:
```
400 Bad Request: "max_tokens" is an unsupported parameter for this model.
Use 'max_completion_tokens' instead.
```

### Для верификации
1. Сначала исправить KEY-CHECK-001
2. Запустить оптимизацию с o4-mini на test_qa_v28@example.com (0/5 лимит)

### Исправление (если ещё не сделано)

```python
# Файл: app/services/llm/openai_provider.py (или аналогичный)

def build_request_params(model: str, prompt: str, max_tokens: int) -> dict:
    params = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }

    # Модели серии o* используют max_completion_tokens
    if model.startswith("o") and model[1:2].isdigit():
        params["max_completion_tokens"] = max_tokens
    else:
        params["max_tokens"] = max_tokens

    return params
```

---

## 💡 РЕКОМЕНДАЦИИ (Улучшения)

### 1. User-friendly ошибки LLM-провайдеров

```python
# Файл: app/services/llm/error_handler.py

ERROR_MESSAGES = {
    402: "Ошибка биллинга {provider} — проверьте баланс в личном кабинете",
    400: "Модель {model} временно недоступна. Попробуйте другую модель",
    401: "Неверный API-ключ для {provider}. Проверьте ключ в Настройках",
    429: "Превышен лимит запросов {provider}. Попробуйте через минуту",
    500: "Сервер {provider} временно недоступен. Попробуйте позже",
}
```

### 2. Тестовые аккаунты
Для QA нужна возможность сбросить лимит оптимизаций или повысить лимит на тестовых аккаунтах.

---

## РЕЗЮМЕ ДЕЙСТВИЙ

### 🔴 Приоритет 1 (ВЫСОКИЙ):
- [ ] **KEY-CHECK-001**: Исправить проверку API-ключей в optimization engine — новые аккаунты не могут оптимизировать

### 🟡 Приоритет 2 (СРЕДНИЙ):
- [ ] **OPENAI-O4MINI**: После фикса KEY-CHECK-001 — верифицировать max_completion_tokens на test_qa_v28@example.com

### 🟢 Приоритет 3 (НИЗКИЙ):
- [ ] **NAV-001**: Исправить onClick на plan-upgrade ссылке
- [ ] User-friendly ошибки LLM-провайдеров

### Не баг приложения:
- **GIGACHAT-001**: 402 Payment Required — проблема биллинга Сбер

---

## ТЕСТОВЫЕ АККАУНТЫ

| Аккаунт | Пароль | Оптимизации | Примечание |
|---------|--------|-------------|------------|
| test@example.com | TestPass1231 | 5/5 исчерпан | Старый аккаунт |
| test_new@example.com | TestPass1231 | 5/5 исчерпан | Старый аккаунт |
| test_qa_v28@example.com | TestPass1231 | 0/5 свободно | Новый, заблокирован KEY-CHECK-001 |

---

## СТАТИСТИКА КАЧЕСТВА

| Метрика | Значение |
|---------|----------|
| Всего багов найдено (V1-V28+) | 11 |
| Исправлено и подтверждено | 7 |
| Открытых багов приложения | 3 (KEY-CHECK-001, NAV-001, OPENAI-O4MINI) |
| Provider-side | 1 (GIGACHAT-001) |
| Критичных (P1) | 0 |
| Средних (P2) | 1 (KEY-CHECK-001 — NEW) |
| Низких (P3) | 2 |
| Оценка V28 | 8.0/10 |
| Production ready | ⚠️ С ОГОВОРКАМИ — KEY-CHECK-001 блокирует новых пользователей |

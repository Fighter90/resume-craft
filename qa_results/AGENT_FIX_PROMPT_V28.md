# AGENT_FIX_PROMPT_V28

> Промт для AI-агента на доработку проекта ResumeCraft.ru
> Создан на основе QA Report #23 (23_FULL_RETEST_V28.md)
> Дата: 09.03.2026

---

## КОНТЕКСТ

Проведён полный ретест V28 (сервер v1.11.0) с фокусом на Параметры оптимизации.
**Результат: RESET-001 (P1) ИСПРАВЛЕН.** Критичных багов больше нет.

Остались 2 проблемы приложения + 1 provider-side:
1. **NAV-001** — ссылка «Обновить до Pro →» не работает при клике (P3, STILL OPEN — обновлён root cause)
2. **OPENAI-O4MINI** — не удалось верифицировать фикс (лимит 5/5 на обоих аккаунтах) (P3)
3. **GIGACHAT-001** — ошибка биллинга на стороне Сбер GigaChat (НЕ баг приложения)

---

## ИСПРАВЛЕННЫЕ БАГИ (подтверждено ретестом V28)

| Bug ID | Описание | V27 | V28 |
|--------|----------|-----|-----|
| P0-3-CLAUDE | RAW JSON в результатах Claude | ✅ | ✅ CONFIRMED |
| GROQ-KEY | Ключ Groq не сохраняется | ✅ | ✅ CONFIRMED |
| AVATAR-001 | Инициалы не соответствуют имени | ✅ | ✅ CONFIRMED |
| LOGOUT-001 | Нет кнопки выхода | ✅ | ✅ CONFIRMED |
| DASHBOARD-001 | «Недавние резюме» пустые | ✅ | ✅ CONFIRMED |
| EMAIL-VERIFY-001 | Противоречие баннера верификации | ✅ | ✅ CONFIRMED |
| RESET-001 | «Сбросить» удаляет ALL API-ключи | ❌ | ✅ FIXED |

---

## 🔴 ДЕФЕКТ 1: NAV-001 — «Обновить до Pro →» не кликается (P3 LOW)

**Severity:** P3 (Low)
**Страница:** Sidebar на всех страницах /app/*
**Статус:** STILL OPEN (с V25) — root cause обновлён

### Описание
Ссылка «Обновить до Pro →» в нижней части sidebar:
- DOM корректный: `<a class="plan-upgrade" href="/app/settings/subscription">`
- Физический клик мышью попадает на ссылку (подтверждено elementFromPoint)
- Навигация НЕ происходит
- Программный `element.click()` через JS — работает
- **Workaround есть:** пользователь может перейти через Настройки → Подписка

### Root Cause (ОБНОВЛЕНО в V28)

Предыдущие версии промта предполагали CSS overlay или z-index конфликт. **Это было неверно.**

Детальное исследование через React internals выявило:
```javascript
// React __reactProps ссылки содержат:
// keys: ["className", "children", "href", "onClick", "ref", "target"]
// hasOnClick: true
```

**Причина:** React `onClick` обработчик на `<a class="plan-upgrade">` вызывает `e.preventDefault()`, что блокирует нативную навигацию по `href`. При этом onClick handler НЕ выполняет альтернативную программную навигацию.

### Исправление

**ВАРИАНТ 1 (рекомендуется): Использовать React Router Link**
```tsx
// Файл: src/components/Sidebar.tsx (или аналогичный)

// БЫЛО:
<a
    href="/app/settings/subscription"
    className="plan-upgrade"
    onClick={(e) => {
        e.preventDefault(); // ← ЭТО БЛОКИРУЕТ НАВИГАЦИЮ
        // ... какая-то логика, которая НЕ навигирует
    }}
>
    Обновить до Pro →
</a>

// ДОЛЖНО БЫТЬ:
import { Link } from 'react-router-dom'; // или useNavigate

<Link to="/app/settings/subscription" className="plan-upgrade">
    Обновить до Pro →
</Link>
```

**ВАРИАНТ 2: Если onClick нужен (аналитика) — не вызывать preventDefault**
```tsx
<a
    href="/app/settings/subscription"
    className="plan-upgrade"
    onClick={() => {
        // Аналитика БЕЗ preventDefault:
        trackEvent('upgrade_click');
        // Навигация произойдёт автоматически по href
    }}
>
    Обновить до Pro →
</a>
```

**ВАРИАНТ 3: Если нужна SPA-навигация из onClick**
```tsx
import { useNavigate } from 'react-router-dom';

const navigate = useNavigate();

<a
    href="/app/settings/subscription"
    className="plan-upgrade"
    onClick={(e) => {
        e.preventDefault();
        trackEvent('upgrade_click'); // аналитика
        navigate('/app/settings/subscription'); // ← ДОБАВИТЬ ЭТУ СТРОКУ
    }}
>
    Обновить до Pro →
</a>
```

---

## ⚠️ ДЕФЕКТ 2: OPENAI-O4MINI — Ошибка max_tokens для o4-mini (P3 LOW)

**Severity:** P3 (Low)
**Статус:** НЕ ВЕРИФИЦИРОВАН (лимит 5/5 на обоих аккаунтах)

### Описание
При оптимизации с моделью openai:o4-mini API возвращает:
```
400 Bad Request: "max_tokens" is an unsupported parameter for this model.
Use 'max_completion_tokens' instead.
```

Запись ошибки видна в Истории оптимизаций test_new@example.com от 06.03.2026.

### Для верификации фикса
Нужно один из вариантов:
1. Сбросить лимит оптимизаций на одном из тестовых аккаунтов
2. Создать новый тестовый аккаунт
3. Временно увеличить лимит Free плана

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
        # o1, o1-mini, o3, o3-mini, o4-mini и т.д.
        params["max_completion_tokens"] = max_tokens
    else:
        # gpt-4o, gpt-4o-mini, gpt-3.5-turbo и т.д.
        params["max_tokens"] = max_tokens

    return params
```

---

## 💡 РЕКОМЕНДАЦИИ (Улучшения)

### 1. User-friendly ошибки LLM-провайдеров

Сейчас ошибки показываются как raw HTTP responses. Рекомендация: обернуть в понятные сообщения.

```python
# Файл: app/services/llm/error_handler.py

ERROR_MESSAGES = {
    402: "Ошибка биллинга {provider} — проверьте баланс в личном кабинете",
    400: "Модель {model} временно недоступна. Попробуйте другую модель",
    401: "Неверный API-ключ для {provider}. Проверьте ключ в Настройках",
    429: "Превышен лимит запросов {provider}. Попробуйте через минуту",
    500: "Сервер {provider} временно недоступен. Попробуйте позже",
}

def format_llm_error(provider: str, model: str, status_code: int, raw_error: str) -> str:
    template = ERROR_MESSAGES.get(status_code, "Ошибка {provider}: {raw_error}")
    return template.format(provider=provider, model=model, raw_error=raw_error)
```

### 2. Тестовые аккаунты — сброс лимита
Для будущего QA необходимо иметь возможность сбросить лимит оптимизаций на тестовых аккаунтах или использовать аккаунты с повышенным лимитом.

---

## РЕЗЮМЕ ДЕЙСТВИЙ

### Приоритет 1 (СРЕДНИЙ):
- [ ] **NAV-001**: Исправить onClick на `<a class="plan-upgrade">` — убрать preventDefault() или добавить navigate()

### Приоритет 2 (НИЗКИЙ):
- [ ] **OPENAI-O4MINI**: Верифицировать фикс (нужен сброс лимита или новый аккаунт)

### Приоритет 3 (УЛУЧШЕНИЯ):
- [ ] User-friendly ошибки LLM-провайдеров вместо raw JSON
- [ ] Сброс лимита для тестовых аккаунтов

### Не баг приложения:
- **GIGACHAT-001**: 402 Payment Required — проблема биллинга на стороне Сбер

---

## СТАТИСТИКА КАЧЕСТВА

| Метрика | Значение |
|---------|----------|
| Всего багов найдено (V1-V28) | 10 |
| Исправлено и подтверждено | 7 |
| Открытых багов приложения | 2 (NAV-001, OPENAI-O4MINI) |
| Provider-side | 1 (GIGACHAT-001) |
| Критичных (P1) | 0 ✅ |
| Оценка V28 | 8.5/10 |
| Production ready | ✅ ДА |

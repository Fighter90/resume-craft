# AGENT_FIX_PROMPT_V29

> Промт для AI-агента на доработку проекта ResumeCraft.ru
> Создан на основе QA Report #25 (V29 Full Retest)
> Дата: 09.03.2026

---

## КОНТЕКСТ

Проведён полный ретест V29 на **3 аккаунтах** (test@example.com, test_new@example.com, test_qa_v28@example.com).

**Результат:** NAV-001 ИСПРАВЛЕН! Остаются 2 открытых бага.

Открытые проблемы:
1. **KEY-CHECK-001** — оптимизация не видит сохранённые API-ключи на новом аккаунте (P2 MEDIUM, OPEN)
2. **OPENAI-O4MINI** — не удалось верифицировать фикс (заблокирован KEY-CHECK-001) (P3 LOW)
3. **GIGACHAT-001** — ошибка биллинга на стороне Сбер GigaChat (НЕ баг приложения)

---

## ИСПРАВЛЕННЫЕ БАГИ (подтверждено на 3 аккаунтах)

| Bug ID | Описание | V29 |
|--------|----------|-----|
| P0-3-CLAUDE | RAW JSON в результатах Claude | ✅ CONFIRMED |
| GROQ-KEY | Ключ Groq не сохраняется | ✅ CONFIRMED |
| AVATAR-001 | Инициалы не соответствуют имени | ✅ CONFIRMED |
| LOGOUT-001 | Нет кнопки выхода | ✅ CONFIRMED |
| DASHBOARD-001 | «Недавние резюме» пустые | ✅ CONFIRMED |
| EMAIL-VERIFY-001 | Противоречие баннера верификации | ✅ CONFIRMED |
| RESET-001 | «Сбросить» удаляет ALL API-ключи | ✅ CONFIRMED |
| **NAV-001** | **«Обновить до Pro →» не кликается** | **✅ FIXED (NEW!)** |

---

## 🔴 ДЕФЕКТ 1 (ПРИОРИТЕТ): KEY-CHECK-001 — Оптимизация не видит API-ключи (P2 MEDIUM)

**Severity:** P2 (Medium) — блокирует основной функционал для новых пользователей
**Страница:** /app/processing
**Статус:** OPEN — впервые обнаружен в V28 на test_qa_v28@example.com, не верифицирован в V29

### Проблема
При попытке запустить оптимизацию с моделью OpenAI o4-mini, все 4 этапа показывают зелёные ✓ (Загрузка, Анализ, AI оптимизация, Финализация), затем ошибка:

```
Ошибка обработки
API-ключ не настроен

API-ключ для OpenAI не настроен. Для использования OpenAI необходимо указать
API-ключ в настройках или выбрать другую модель (например, OpenRouter).
```

### Ожидаемый результат
Оптимизация должна успешно запуститься, используя API-ключ, подтверждённый через GET /api/v1/settings/ai-keys (has_key: true).

### Доказательства что ключи СОХРАНЕНЫ (test_qa_v28@example.com)

API-ключи подтверждены 3 независимыми методами:

1. **PUT API:** `PUT /api/v1/settings/ai-keys/openai` → `200 OK, {"has_key": true}`
2. **GET API:** `GET /api/v1/settings/ai-keys` → все 5 ключей `has_key: true`
3. **UI:** Страница /app/settings/ai → зелёные ✓ "Сохранён" для всех 5 ключей:
   - GigaChat Pro: MDU2...NA==
   - OpenAI: sk-p...QcMA
   - Anthropic Claude: sk-a...UAAA
   - OpenRouter: sk-o...4d2d
   - Groq: gsk_...GiQv

### Предполагаемый Root Cause

Бэкенд-процесс оптимизации проверяет наличие API-ключа **по другому механизму**, нежели API настроек. Возможные варианты:

1. **Кэширование:** Optimization engine кэширует состояние ключей и не видит новые
2. **Race condition:** Асинхронное сохранение, ключ не успевает стать видимым
3. **Разные хранилища:** Settings API и Optimization engine читают из разных источников
4. **Session/user context:** Ключи привязаны к одному контексту, оптимизация проверяет другой

### Где исправлять

- **Backend:** Файл, отвечающий за запуск оптимизации и проверку API-ключей
- Вероятные файлы: `app/services/optimization/engine.py`, `app/services/llm/provider.py`, или аналогичные
- **Решение:** Использовать единый сервис для проверки ключей

### Алгоритм исправления

```python
# Файл: app/services/optimization/engine.py (или аналогичный)

# ПРОБЛЕМА: Оптимизация проверяет ключ не через тот же сервис, что Settings API

# РЕШЕНИЕ: Использовать единый источник данных для проверки ключей
async def check_api_key(user_id: int, provider: str) -> bool:
    # ДОЛЖНО использовать тот же сервис, что и /api/v1/settings/ai-keys
    key = await ai_keys_service.get_key(user_id, provider)
    return key is not None and len(key) > 0

# ОТЛАДКА: Добавить логирование для диагностики
async def start_optimization(user_id: int, provider: str, model: str, ...):
    logger.info(f"Checking API key for user={user_id}, provider={provider}")

    # Проверка ключа через Settings service (единый источник)
    key = await ai_keys_service.get_key(user_id, provider)
    logger.info(f"Key found: {key is not None}, length: {len(key) if key else 0}")

    if not key:
        raise APIKeyNotConfiguredError(provider)

    # ... продолжить оптимизацию

# Проверить:
# 1. Нет ли отдельного кэша ключей в optimization engine
# 2. Совпадает ли user_id при запросе ключа из optimization контекста
# 3. Нет ли фильтрации по дате создания аккаунта или другому признаку
# 4. Правильно ли передаётся user context из JWT в optimization service
```

### Шаги воспроизведения
1. Создать новый аккаунт (или использовать test_qa_v28@example.com / TestPass1231)
2. Сохранить API-ключ OpenAI через PUT /api/v1/settings/ai-keys/openai
3. Подтвердить: GET /api/v1/settings/ai-keys → has_key: true
4. Подтвердить: UI /app/settings/ai → зелёная ✓
5. Загрузить резюме, ввести вакансию, выбрать OpenAI o4-mini
6. Нажать "Начать оптимизацию"
7. **Результат:** "API-ключ не настроен"

### ВАЖНО
Баг обнаружен ТОЛЬКО на НОВОМ аккаунте. На старых аккаунтах оптимизации работали ранее. Возможна специфика аккаунтов, созданных после определённого обновления.

---

## 🟡 ДЕФЕКТ 2: OPENAI-O4MINI — max_tokens для o4-mini (P3 LOW)

**Severity:** P3 (Low)
**Статус:** НЕ ВЕРИФИЦИРОВАН — заблокирован KEY-CHECK-001

### Проблема
При оптимизации с openai:o4-mini API возвращает:
```
400 Bad Request: "max_tokens" is an unsupported parameter for this model.
Use 'max_completion_tokens' instead.
```

### Ожидаемый результат
Оптимизация с моделью o4-mini должна завершиться успешно, используя параметр `max_completion_tokens` вместо `max_tokens`.

### Для верификации
1. Сначала исправить KEY-CHECK-001
2. Запустить оптимизацию с o4-mini на test_qa_v28@example.com (0/5 лимит)

### Где исправлять
- **Backend:** Файл, формирующий запрос к OpenAI API
- Вероятные файлы: `app/services/llm/openai_provider.py`, `app/services/llm/providers/openai.py`, или аналогичные

### Алгоритм исправления (если ещё не сделано)

```python
# Файл: app/services/llm/openai_provider.py (или аналогичный)

def build_request_params(model: str, prompt: str, max_tokens: int) -> dict:
    params = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }

    # Модели серии o* (o1, o1-mini, o3, o3-mini, o4-mini и т.д.)
    # используют max_completion_tokens вместо max_tokens
    if model.startswith("o") and model[1:2].isdigit():
        params["max_completion_tokens"] = max_tokens
    else:
        params["max_tokens"] = max_tokens

    return params
```

---

## 💡 РЕКОМЕНДАЦИИ (Улучшения)

### 1. User-friendly ошибки LLM-провайдеров

Сейчас ошибки провайдеров показываются как raw JSON/HTTP:
```
Ошибка: LLM-провайдер gigachat-pro: (URL('https://gigachat.devices.sberbank.ru/...'), 402,
b'{"status":402,"message":"Payment Required"}\n', Headers({...}), 'conte временно недоступен
```

**Решение:**
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
    template = ERROR_MESSAGES.get(status_code,
        "Ошибка {provider}: {raw_error}")
    return template.format(
        provider=provider,
        model=model,
        raw_error=raw_error[:100]  # обрезать raw для fallback
    )
```

### 2. Тестовые аккаунты
Для QA нужна возможность сбросить лимит оптимизаций или повысить лимит на тестовых аккаунтах. Оба основных аккаунта (test@, test_new@) исчерпали 5/5 лимит.

---

## РЕЗЮМЕ ДЕЙСТВИЙ

### 🔴 Приоритет 1 (ВЫСОКИЙ):
- [ ] **KEY-CHECK-001**: Исправить проверку API-ключей в optimization engine — новые аккаунты не могут оптимизировать

### 🟡 Приоритет 2 (СРЕДНИЙ):
- [ ] **OPENAI-O4MINI**: После фикса KEY-CHECK-001 — верифицировать max_completion_tokens на test_qa_v28@example.com

### 🟢 Приоритет 3 (НИЗКИЙ):
- [ ] User-friendly ошибки LLM-провайдеров

### ✅ Исправлено в V29:
- [x] **NAV-001**: Ссылка «Обновить до Pro →» теперь навигирует корректно

### Не баг приложения:
- **GIGACHAT-001**: 402 Payment Required — проблема биллинга Сбер

---

## ТЕСТОВЫЕ АККАУНТЫ

| Аккаунт | Пароль | Оптимизации | Примечание |
|---------|--------|-------------|------------|
| test@example.com | TestPass1231 | 5/5 исчерпан | Старый аккаунт |
| test_new@example.com | TestPass1231 | 5/5 исчерпан | Старый аккаунт |
| test_qa_v28@example.com | TestPass1231 | 0/5 свободно | Новый, для тестирования KEY-CHECK-001 |

---

## СТАТИСТИКА КАЧЕСТВА

| Метрика | Значение |
|---------|----------|
| Всего багов найдено (V1-V29) | 11 |
| Исправлено и подтверждено | 8 |
| Открытых багов приложения | 2 (KEY-CHECK-001, OPENAI-O4MINI) |
| Provider-side | 1 (GIGACHAT-001) |
| Критичных (P1) | 0 |
| Средних (P2) | 1 (KEY-CHECK-001) |
| Низких (P3) | 1 (OPENAI-O4MINI) |
| Оценка V29 | 8.5/10 |
| Production ready | ⚠️ С ОГОВОРКАМИ — KEY-CHECK-001 блокирует новых пользователей |

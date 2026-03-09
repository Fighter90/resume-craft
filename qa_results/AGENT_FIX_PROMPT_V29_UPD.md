# AGENT_FIX_PROMPT_V29_UPD

> Промт для AI-агента на доработку проекта ResumeCraft.ru
> Создан на основе QA Report #26 (V29 Full Retest — Updated)
> Дата: 09.03.2026
> **ОБНОВЛЕНИЕ:** KEY-CHECK-001 ВЕРИФИЦИРОВАН — severity повышен до P1 CRITICAL

---

## КОНТЕКСТ

Проведён полный ретест V29 на **3 аккаунтах** (test@example.com, test_new@example.com, test_qa_v28@example.com).

**Главная находка:** KEY-CHECK-001 полностью верифицирован на **3 из 3 провайдеров** (OpenAI, OpenRouter, Groq). Severity повышен с P2 MEDIUM до **P1 CRITICAL**.

**Результат:** NAV-001 ИСПРАВЛЕН. KEY-CHECK-001 — БЛОКЕР РЕЛИЗА.

Открытые проблемы:
1. **KEY-CHECK-001** — оптимизация не видит сохранённые API-ключи на новом аккаунте — **ВСЕ провайдеры** (**P1 CRITICAL**, VERIFIED)
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

## 🔴 ДЕФЕКТ 1 (БЛОКЕР РЕЛИЗА): KEY-CHECK-001 — P1 CRITICAL

**Severity:** P1 CRITICAL ⬆️ (повышен с P2 MEDIUM)
**Страница:** /app/processing
**Статус:** ✅ VERIFIED — воспроизведён на 3 из 3 провайдеров

### Проблема

При запуске оптимизации на аккаунте test_qa_v28@example.com, **ВСЕ провайдеры** возвращают ошибку "API-ключ не настроен", несмотря на то что ключи подтверждённо сохранены (зелёные ✓ на странице настроек).

### Результаты тестирования (3 провайдера)

| # | Провайдер | Модель | Результат |
|---|-----------|--------|-----------|
| 1 | **OpenAI** | GPT-4o | ❌ "API-ключ для OpenAI не настроен" |
| 2 | **OpenRouter** | AI21 Jamba Large 1.7 | ❌ "API-ключ для OpenRouter не настроен" |
| 3 | **Groq** | Llama 3.3 70B | ❌ "API-ключ для groq не настроен" |

### Доказательства что ключи СОХРАНЕНЫ (test_qa_v28@example.com)

На странице /app/settings/ai все 5 провайдеров показывают зелёный ✓:
- GigaChat Pro (Сбер): ✅ Сохранён: MDU2...NA==
- OpenAI (OpenAI): ✅ Сохранён: sk-p...QcMA
- Anthropic Claude (Anthropic): ✅ Сохранён: sk-a...UAAA
- OpenRouter (OpenRouter): ✅ Сохранён: sk-o...4d2d
- Groq (Groq): ✅ Сохранён: gsk_...GiQv

API подтверждение: GET /api/v1/settings/ai-keys → все 5 ключей has_key: true

### Критическое наблюдение: Этапы обработки ПРОХОДЯТ до ошибки

При тестировании прогресс-бар обработки показывает:
- ✅ Загрузка документа — зелёная ✓
- ✅ Анализ вакансии — зелёная ✓
- ✅ AI оптимизация — зелёная ✓ (!)
- ✅ Финализация — показывает прогресс
- **ЗАТЕМ** ошибка: "API-ключ не настроен"

**Вывод:** Проверка API-ключа происходит **ПОСЛЕ** начальных этапов обработки, а не ДО. Фронтенд показывает зелёные ✓ ещё до реальной проверки ключа — это вводит пользователя в заблуждение.

### Root Cause Analysis (ОБНОВЛЁННЫЙ)

**Факт:** Баг воспроизводится для **ВСЕХ** провайдеров (OpenAI, OpenRouter, Groq). Это **ИСКЛЮЧАЕТ** провайдер-специфичную проблему.

Наиболее вероятные причины (в порядке вероятности):

1. **User context / Session mismatch:** Optimization engine получает user_id, но **не может найти ключи для этого пользователя**:
   - Ключи сохраняются в одном хранилище (Settings API), а optimization engine читает из другого
   - Или user_id из JWT не совпадает с user_id, по которому ищутся ключи
   - Или optimization engine использует устаревший/некорректный user context

2. **Migration / Schema issue:** Аккаунт test_qa_v28@example.com создан 06.03.2026 (после определённого обновления). Возможно:
   - Новая миграция БД изменила структуру хранения ключей
   - Новые аккаунты используют другую таблицу/схему
   - Ключи сохраняются в новом формате, а optimization engine ожидает старый

3. **Lazy initialization:** Optimization service при первом запуске для нового аккаунта:
   - Не инициализирует контекст с ключами
   - Или инициализирует с пустым набором ключей и не обновляет

4. **Кэширование:** Optimization engine кэширует состояние ключей при первом обращении (когда ключей ещё не было) и не инвалидирует кэш при добавлении ключей

### Где исправлять

- **Backend:** Файл, отвечающий за запуск оптимизации и получение API-ключей пользователя
- Вероятные файлы:
  - `app/services/optimization/engine.py` — главный orchestrator оптимизации
  - `app/services/llm/provider.py` — фабрика LLM-провайдеров
  - `app/services/ai_keys/service.py` — сервис управления ключами
  - `app/api/routes/optimization.py` — API endpoint запуска оптимизации

### Алгоритм диагностики и исправления

```python
# ====================================================================
# ШАГ 1: ДИАГНОСТИКА — Добавить логирование в optimization engine
# ====================================================================
# Файл: app/services/optimization/engine.py (или аналогичный)

async def start_optimization(user_id: int, provider: str, model: str, ...):
    # ДИАГНОСТИКА: Логировать все параметры
    logger.info(f"[OPTIMIZATION] Start: user_id={user_id}, provider={provider}, model={model}")

    # ДИАГНОСТИКА: Проверить какой сервис используется для получения ключей
    # Сравнить с Settings API
    key_from_optimization = await get_api_key_for_provider(user_id, provider)
    logger.info(f"[OPTIMIZATION] Key from optimization service: exists={key_from_optimization is not None}")

    # ДИАГНОСТИКА: Проверить через Settings service напрямую
    from app.services.ai_keys.service import ai_keys_service
    key_from_settings = await ai_keys_service.get_key(user_id, provider)
    logger.info(f"[OPTIMIZATION] Key from settings service: exists={key_from_settings is not None}")

    # Если ключи не совпадают — найден root cause!
    if key_from_settings and not key_from_optimization:
        logger.error(f"[OPTIMIZATION] KEY MISMATCH! Settings has key, optimization doesn't!")
        logger.error(f"[OPTIMIZATION] This is KEY-CHECK-001 bug!")

# ====================================================================
# ШАГ 2: ИСПРАВЛЕНИЕ — Единый источник данных для ключей
# ====================================================================

# ПРОБЛЕМА: optimization engine проверяет ключ НЕ через тот же сервис, что Settings API
# РЕШЕНИЕ: Использовать единый источник данных

async def get_api_key_for_provider(user_id: int, provider: str) -> Optional[str]:
    """
    Единый метод получения API-ключа.
    ДОЛЖЕН использовать тот же сервис, что и /api/v1/settings/ai-keys
    """
    # ПРАВИЛЬНО: Использовать Settings service
    key = await ai_keys_service.get_key(user_id, provider)
    return key

    # НЕПРАВИЛЬНО (возможная текущая реализация):
    # key = await some_cache.get(f"api_key:{user_id}:{provider}")
    # key = await optimization_db.get_key(user_id, provider)  # другая таблица!
    # key = self._cached_keys.get(provider)  # локальный кэш без инвалидации!

# ====================================================================
# ШАГ 3: ПРОВЕРКИ
# ====================================================================

# Проверить:
# 1. Нет ли отдельного кэша ключей в optimization engine
# 2. Совпадает ли user_id при запросе ключа из optimization контекста vs settings
# 3. Нет ли фильтрации по дате создания аккаунта или другому признаку
# 4. Правильно ли передаётся user context из JWT в optimization service
# 5. Не используется ли другая таблица/коллекция для хранения ключей
# 6. Нет ли проблемы с шифрованием/дешифрованием ключей для новых аккаунтов

# ====================================================================
# ШАГ 4: ДОПОЛНИТЕЛЬНО — Переместить проверку ключа ДО этапов обработки
# ====================================================================

async def start_optimization(user_id: int, provider: str, model: str, ...):
    # ПЕРВЫМ ДЕЛОМ проверить наличие ключа — ДО загрузки документа и анализа
    key = await ai_keys_service.get_key(user_id, provider)
    if not key:
        # Вернуть ошибку СРАЗУ, а не после 4 этапов прогресса
        raise APIKeyNotConfiguredError(
            provider=provider,
            message=f"API-ключ для {provider} не настроен. "
                    f"Укажите ключ в Настройках → AI-модели."
        )

    # Только после успешной проверки — начинать обработку
    await upload_document(...)      # Загрузка
    await analyze_vacancy(...)      # Анализ
    result = await run_llm(key, ...)  # AI оптимизация
    await finalize(result, ...)     # Финализация
```

### Шаги воспроизведения (полностью верифицированы)

1. Залогиниться как test_qa_v28@example.com / TestPass1231
2. Перейти в "Мои резюме" → выбрать любое резюме → ⚡ Оптимизировать
3. Заполнить вакансию: "Senior Python Developer", компания "Яндекс", описание: "Python, Django, FastAPI..."
4. Нажать "Продолжить"
5. Выбрать ЛЮБОЙ провайдер (OpenAI GPT-4o / OpenRouter AI21 Jamba / Groq Llama 3.3)
6. Нажать "Начать оптимизацию"
7. **Результат:** Прогресс-бар доходит до 74-82%, показывает зелёные ✓, затем "Ошибка обработки → API-ключ не настроен"
8. Счётчик остаётся 0/5 (оптимизация не засчитана)

### Влияние

- **ВСЕ новые пользователи** не могут пользоваться основной функцией приложения
- Пользователь видит, что ключи сохранены (зелёные ✓), но оптимизация всё равно не работает
- Прогресс-бар обманывает, показывая зелёные ✓ до реальной проверки ключа
- Крайне негативный UX — пользователь не понимает, что делать
- **P1 CRITICAL — полная блокировка основного use case для ВСЕХ новых аккаунтов**

### ВАЖНО

Баг обнаружен ТОЛЬКО на НОВОМ аккаунте (test_qa_v28@example.com, создан 06.03.2026). На старых аккаунтах (test@, test_new@) оптимизации работали ранее. Это указывает на проблему, связанную с аккаунтами, созданными после определённого обновления.

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
- Вероятные файлы: `app/services/llm/openai_provider.py`, `app/services/llm/providers/openai.py`

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
        raw_error=raw_error[:100]
    )
```

### 2. Ранняя проверка API-ключа (UX)

Текущая проблема: прогресс-бар показывает зелёные ✓ для этапов Загрузка/Анализ/AI оптимизация, а затем появляется ошибка "ключ не настроен". Это обман пользователя.

**Решение:** Проверять наличие ключа ДО начала обработки (см. ШАГ 4 в алгоритме исправления KEY-CHECK-001).

### 3. Тестовые аккаунты

Для QA нужна возможность сбросить лимит оптимизаций или повысить лимит на тестовых аккаунтах. Оба основных аккаунта (test@, test_new@) исчерпали 5/5 лимит.

---

## РЕЗЮМЕ ДЕЙСТВИЙ

### 🔴 Приоритет 1 (БЛОКЕР РЕЛИЗА):
- [ ] **KEY-CHECK-001**: Optimization engine не видит API-ключи для ВСЕХ провайдеров на новых аккаунтах. Воспроизводится на OpenAI, OpenRouter, Groq. **SEVERITY P1 CRITICAL.**
  - Добавить диагностическое логирование
  - Найти расхождение между Settings API и Optimization engine
  - Использовать единый сервис для проверки ключей
  - Перенести проверку ключа на начало обработки

### 🟡 Приоритет 2 (СРЕДНИЙ):
- [ ] **OPENAI-O4MINI**: После фикса KEY-CHECK-001 — верифицировать max_completion_tokens на test_qa_v28@example.com

### 🟢 Приоритет 3 (НИЗКИЙ):
- [ ] User-friendly ошибки LLM-провайдеров
- [ ] Ранняя проверка API-ключа (до этапов обработки)

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
| test_qa_v28@example.com | TestPass1231 | **0/5 свободно** | **KEY-CHECK-001 VERIFIED на 3 провайдерах** |

---

## СТАТИСТИКА КАЧЕСТВА

| Метрика | Значение |
|---------|----------|
| Всего багов найдено (V1-V29) | 11 |
| Исправлено и подтверждено | 8 |
| Открытых багов приложения | 2 (KEY-CHECK-001, OPENAI-O4MINI) |
| Provider-side | 1 (GIGACHAT-001) |
| **Критичных (P1)** | **1 (KEY-CHECK-001)** ⬆️ |
| Средних (P2) | 0 |
| Низких (P3) | 1 (OPENAI-O4MINI) |
| Оценка V29 | **7.5/10** (снижена из-за KEY-CHECK-001) |
| Production ready | **❌ НЕТ — KEY-CHECK-001 блокирует ВСЕХ новых пользователей** |

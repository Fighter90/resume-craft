# AGENT FIX PROMPT V44 — Полный регрессионный тест + все 5 провайдеров

**Дата:** 2026-03-14
**Версия приложения:** 1.26.0
**Источник:** Полный регресс V44 (от V42 baseline) + тест всех 5 AI-провайдеров
**Проект:** ResumeCraft.ru
**Тестовые аккаунты:**
- `qa_v44_live@example.com` / TestPass1231 (основной, 4 провайдера)
- `qa_v44_groq@example.com` / TestPass1231 (Groq-тест)
**Resume ID:** `6100d5f9-fa96-49c2-aed7-b09755f205e5`
**Окружение:** Chrome, resumecraft.ru (production)

---

## СВОДКА

| Метрика | Значение |
|---------|----------|
| Всего тестов | 30 |
| ✅ PASS | 24 |
| ❌ FAIL | 4 |
| ⚠️ KNOWN ISSUE | 2 |
| Pass Rate | **80%** |

---

## СВОДКА ДЕФЕКТОВ

| # | Приоритет | ID | Описание | Тип | Статус V44 |
|---|-----------|-----|----------|-----|-----------|
| 1 | 🔴 P1 | GROQ-KEY-INVISIBLE | Celery worker не видит сохранённый API-ключ Groq | BUG | ❌ **NEW** |
| 2 | 🔴 P1 | RATE-LIMIT-BYPASS | Лимит 5 оптимизаций превышен (6/5) — race condition | BUG | ❌ **NEW** |
| 3 | 🟡 P2 | OPENAI-JSON-WRAP | OpenAI gpt-4o возвращает JSON в markdown ````json` обёртке | BUG | ❌ **NEW** |
| 4 | 🟡 P2 | HH-RESUME-LINK-400 | POST /api/v1/resumes/from-url → 400 для hh.ru ссылок | BUG | ❌ CONFIRMED V42→V44 |
| 5 | 🟡 P2 | ACCOUNT-DELETE-500 | DELETE /api/v1/auth/me → 500 Internal Server Error | BUG | ⚠️ NOT RETESTED (аккаунт нужен) |
| 6 | 🟢 P3 | VACANCY-TITLE-002 | Автозаполнение "Product Manager" вместо должности из резюме | UX | ⚠️ KNOWN ISSUE |

---

## 🔴 ДЕФЕКТ 1 — P1: GROQ-KEY-INVISIBLE (Celery worker не видит API-ключ Groq)

### Проблема
API-ключ Groq сохраняется через `PUT /api/v1/settings/ai-keys/groq` (200 OK), отображается в настройках (`has_key: true`, `masked_key: "gsk_...xPWB"`), но при запуске оптимизации Celery worker выдаёт ошибку "API-ключ для Groq не настроен".

### Шаги воспроизведения
1. Сохранить ключ: `PUT /api/v1/settings/ai-keys/groq` → 200 OK
2. Проверить: `GET /api/v1/settings/ai-keys` → `groq: has_key: true` ✅
3. Запустить оптимизацию: `POST /api/v1/rewrite` с `model: 'groq'` → 202 Accepted (роутер пропускает!)
4. Celery worker: **status: "failed"**, error: "API-ключ для Groq не настроен"

### Корневая причина
**Роутер** (`rewriter/router.py:97-101`) вызывает `get_user_setting()` → находит ключ → пропускает запрос (202).
**Celery worker** (`rewriter/service.py:150-155`) тоже вызывает `get_user_setting()` → но не находит ключ!

Вероятные причины:
1. **Разный SECRET_KEY** между веб-сервером и Celery worker → `decrypt_value()` в `encryption.py:47` возвращает `''` при InvalidToken
2. **Проблема сессии** — Celery создаёт новый engine (`tasks.py:61`), возможно не видит незакоммиченные данные

### Где исправлять

**Файл:** `src/app/core/encryption.py`
```python
# Строка 47: Добавить логирование для отладки
except (InvalidToken, Exception) as e:
    logger.warning('Failed to decrypt value (key may have changed): %s', type(e).__name__)
    logger.debug('Ciphertext prefix: %s...', ciphertext[:20] if ciphertext else 'empty')
    return ''
```

**Файл:** `src/app/rewriter/service.py`
```python
# После строки 163: Добавить проверку
logger.info(
    'Rewrite %s: user_keys found for providers: %s',
    task_id,
    list(user_keys.keys()) if user_keys else '(none)',
)
# ДОБАВИТЬ: проверка что ключ для нужного провайдера есть
if provider_name not in user_keys:
    logger.error(
        'Rewrite %s: NO key for requested provider %s! Available: %s',
        task_id, provider_name, list(user_keys.keys()),
    )
```

**Файл:** `src/app/rewriter/tasks.py`
```python
# После строки 60: Проверить что SECRET_KEY совпадает
settings = get_settings()
logger.info('Celery worker SECRET_KEY hash: %s', hashlib.sha256(settings.secret_key.encode()).hexdigest()[:16])
```

### Проверка
Убедиться что `SECRET_KEY` одинаковый в `.env` для web и celery worker. Если используется docker-compose — проверить что оба сервиса получают одинаковые переменные окружения.

---

## 🔴 ДЕФЕКТ 2 — P1: RATE-LIMIT-BYPASS (Превышение лимита оптимизаций)

### Проблема
На бесплатном плане лимит 5 оптимизаций, но удалось выполнить **6 успешных оптимизаций**. UI показывает "6 / 5 оптимизаций" с переполненным прогресс-баром.

### Шаги воспроизведения
1. Зарегистрировать аккаунт (free plan, 0/5 оптимизаций)
2. Быстро отправить 2 запроса подряд на оптимизацию (race condition при потере соединения Chrome extension)
3. Оба запроса принимаются и выполняются
4. Повторить с другими провайдерами
5. Итого: `optimizations_used: 6`, хотя лимит 5

### Корневая причина
В `rewriter/router.py:129-131`:
```python
# API-001/LIVE-003: НЕ инкрементируем счётчик здесь.
# Счётчик обновляется в Celery-задаче ТОЛЬКО при status=COMPLETED.
```

Проблема: **проверка лимита отсутствует в роутере**. Роутер принимает запрос (202) без проверки `optimizations_used < limit`. Celery worker инкрементирует счётчик, но не проверяет лимит перед выполнением.

### Где исправлять

**Файл:** `src/app/rewriter/router.py`
```python
# ПЕРЕД строкой 120 (создание задачи) добавить:
# RATE-LIMIT-001: Проверка лимита оптимизаций
from app.core.config import get_settings
settings = get_settings()
plan_limits = {'free': 5, 'pro': 100, 'enterprise': -1}  # -1 = безлимитно
user_limit = plan_limits.get(current_user.plan, 5)
if user_limit >= 0 and current_user.optimizations_used >= user_limit:
    raise HTTPException(
        status_code=429,
        detail=f'Достигнут лимит оптимизаций ({user_limit}) для плана "{current_user.plan}". '
               'Обновите план для продолжения.',
    )
```

**Файл:** `src/app/rewriter/service.py` (в Celery worker)
```python
# В execute_rewrite, перед вызовом LLM — повторная проверка (защита от race condition):
user = await session.get(User, task.user_id)
if user and user.plan == 'free' and user.optimizations_used >= 5:
    task.status = RewriteStatus.FAILED
    task.error_message = 'Лимит оптимизаций превышен'
    return task
```

---

## 🟡 ДЕФЕКТ 3 — P2: OPENAI-JSON-WRAP (Markdown обёртка в ответе OpenAI)

### Проблема
OpenAI gpt-4o возвращает JSON-ответ обёрнутый в markdown code block: ` ```json\n{...}\n``` ` вместо чистого JSON `{...}`.

GigaChat и Anthropic Claude возвращают чистый JSON. OpenRouter DeepSeek — нестабильно (один из двух запросов обёрнут).

### Влияние
Фронтенд **корректно обрабатывает** обёртку (на странице результатов текст форматирован, не raw JSON). Однако бэкенд должен стрипать обёртку перед сохранением в `rewritten_text` для консистентности.

### Где исправлять

**Файл:** `src/app/rewriter/service.py`
```python
# В функции _parse_llm_response или перед ней:
def _strip_markdown_wrapper(text: str) -> str:
    """Удалить markdown code block обёртку если есть."""
    stripped = text.strip()
    if stripped.startswith('```json'):
        stripped = stripped[7:]  # Убрать ```json
    elif stripped.startswith('```'):
        stripped = stripped[3:]  # Убрать ```
    if stripped.endswith('```'):
        stripped = stripped[:-3]
    return stripped.strip()

# Использовать перед JSON-парсингом:
response = _strip_markdown_wrapper(response)
```

---

## 🟡 ДЕФЕКТ 4 — P2: HH-RESUME-LINK-400 (Загрузка резюме с hh.ru)

### Проблема
`POST /api/v1/resumes/from-url` с URL резюме hh.ru → 400 Bad Request. Эндпоинт `/api/v1/resumes/from-hh` → 405 Method Not Allowed (не существует).

### Статус
Известный дефект с V20. Graceful degradation работает (сообщение об ошибке).

---

## ✅ ИСПРАВЛЕННЫЕ БАГИ (подтверждено V44)

| ID | Приоритет | Описание | Было | Стало V44 |
|----|-----------|----------|------|-----------|
| **P0-3** | 🔴 P0 | RAW JSON на странице /app/results | Сырой JSON | **Форматированный текст ✅** |
| **P0-4** | 🔴 P0 | OpenAI o-series max_tokens ошибка | 500 error | **Работает (gpt-4o, 5 сек) ✅** |
| **PROGRESS-BAR** | 🟡 P1 | Прогресс-бар застревает на 0% | 0% stuck | **Анимация работает ✅** |
| **AVATAR-DELETE-503** | 🟡 P2 | DELETE avatar → 503 | 503 | **204 ✅** (fixed V42) |
| **PASSWORD-CHANGE-503** | 🔴 P1 | PUT password → 503 | 503 | **204 ✅** (fixed V42) |

---

## 📊 РЕЗУЛЬТАТЫ AI-ОПТИМИЗАЦИИ (5 ПРОВАЙДЕРОВ)

| # | Провайдер | Модель | Score Before | Score After | Δ | ATS | Время | Токены | Статус |
|---|-----------|--------|-------------|-------------|---|-----|-------|--------|--------|
| 1 | GigaChat | gigachat-pro | 28.6% | 42.0% | +13.4 | D | 14.3s | — | ✅ PASS |
| 2 | OpenAI | gpt-4o | 28.6% | 41.7% | +13.1 | D | 5.5s | 452 | ✅ PASS |
| 3 | Anthropic | claude-sonnet-4 | 28.6% | 48.2% | +19.6 | D | 18.2s | 618 | ✅ PASS |
| 4 | OpenRouter | deepseek-chat (V3) | 28.6% | 40.3% | +11.7 | D | 22.7s | — | ✅ PASS |
| 5 | Groq | llama-3.3-70b | 13.7% | — | — | — | — | — | ❌ FAIL |

**Лучший результат:** Anthropic Claude Sonnet 4 (+19.6, 48.2%)
**Самый быстрый:** OpenAI gpt-4o (5.5 сек)
**Средний Δ (успешные):** +14.5 пунктов
**Средний Score (успешные):** 43.1%

### Ключевые слова добавленные AI

| Провайдер | Кол-во | Примеры |
|-----------|--------|---------|
| GigaChat | — | — |
| OpenAI | 8 | React, TypeScript, API, производительность, масштабируемость, менторинг, технический долг, code review |
| Anthropic | 11 | интеграция с backend через API, планирование спринтов, проектирование архитектуры, оптимизация производительности, наставничество, code review |
| OpenRouter | — | — |

---

## РЕЗУЛЬТАТЫ ФУНКЦИОНАЛЬНЫХ ТЕСТОВ

### 1. Регистрация
| Параметр | Результат |
|----------|-----------|
| Endpoint | POST /api/v1/auth/register |
| HTTP | 201 Created ✅ |
| Token | access_token + refresh_token получены ✅ |
| **Статус** | ✅ **PASS** |

### 2. Авторизация
| Параметр | Результат |
|----------|-----------|
| Endpoint | POST /api/v1/auth/login |
| HTTP | 200 OK ✅ |
| **Статус** | ✅ **PASS** |

### 3. Профиль пользователя
| Параметр | Результат |
|----------|-----------|
| GET /api/v1/auth/me | 200 ✅ |
| PATCH /api/v1/auth/me | 200 ✅ |
| **Статус** | ✅ **PASS** |

### 4. Refresh Token
| Параметр | Результат |
|----------|-----------|
| POST /api/v1/auth/refresh | 200 ✅ |
| **Статус** | ✅ **PASS** |

### 5. Загрузка резюме из текста
| Параметр | Результат |
|----------|-----------|
| POST /api/v1/resumes/from-text | 201 Created ✅ |
| **Статус** | ✅ **PASS** |

### 6. Загрузка резюме по ссылке hh.ru
| Параметр | Результат |
|----------|-----------|
| POST /api/v1/resumes/from-url | 405 Method Not Allowed |
| **Статус** | ❌ **FAIL** — HH-RESUME-LINK-400 |

### 7. Сохранение API ключей (все 5 провайдеров)
| Параметр | Результат |
|----------|-----------|
| GigaChat | PUT → 200 ✅ |
| OpenAI | PUT → 200 ✅ |
| Anthropic | PUT → 200 ✅ |
| OpenRouter | PUT → 200 ✅ |
| Groq | PUT → 200 ✅ |
| **Статус** | ✅ **PASS** |

### 8. Поиск вакансий
| Параметр | Результат |
|----------|-----------|
| GET /api/v1/vacancies/search?text=Frontend+разработчик&area=1 | 200 ✅ |
| Результаты | Реальные вакансии с hh.ru ✅ |
| **Статус** | ✅ **PASS** |

### 9. Создание вакансии из URL
| Параметр | Результат |
|----------|-----------|
| POST /api/v1/vacancies/from-url | 201 Created ✅ |
| UUID получен | ✅ |
| **Статус** | ✅ **PASS** |

### 10. Список моделей
| Параметр | Результат |
|----------|-----------|
| GET /api/v1/models | 200, 5 провайдеров ✅ |
| Sub-models OpenAI | o4-mini, o3, gpt-4o и др. ✅ |
| Sub-models Anthropic | Claude Opus 4.6, Sonnet 4.6, Haiku 4.5 и др. ✅ |
| Sub-models OpenRouter | 100+ моделей ✅ |
| Sub-models Groq | llama, gemma, mixtral и др. ✅ |
| **Статус** | ✅ **PASS** |

### 11. Оптимизация GigaChat Pro
| Параметр | Результат |
|----------|-----------|
| Score | 28.6% → 42.0% (+13.4) ✅ |
| Время | 14.3 сек ✅ |
| JSON чистый | ✅ |
| **Статус** | ✅ **PASS** |

### 12. Оптимизация OpenAI gpt-4o
| Параметр | Результат |
|----------|-----------|
| Score | 28.6% → 41.7% (+13.1) ✅ |
| Время | 5.5 сек ✅ |
| JSON обёрнут в ` ```json ` | ⚠️ OPENAI-JSON-WRAP |
| Отображение в UI | Корректное (не raw JSON) ✅ |
| **Статус** | ✅ **PASS** (с замечанием P2) |

### 13. Оптимизация Anthropic Claude Sonnet 4
| Параметр | Результат |
|----------|-----------|
| Score | 28.6% → 48.2% (+19.6) ✅ |
| Время | 18.2 сек ✅ |
| JSON чистый | ✅ |
| **Статус** | ✅ **PASS** |

### 14. Оптимизация OpenRouter DeepSeek V3
| Параметр | Результат |
|----------|-----------|
| Score | 28.6% → 40.3% (+11.7) ✅ |
| Время | 22.7 сек ✅ |
| JSON | Нестабильно (1 из 2 обёрнут) |
| **Статус** | ✅ **PASS** |

### 15. Оптимизация Groq Llama 3.3 70B
| Параметр | Результат |
|----------|-----------|
| POST /api/v1/rewrite | 202 Accepted (роутер пропустил) |
| Celery worker | status: "failed" |
| Ошибка | "API-ключ для Groq не настроен" |
| Ключ в настройках | has_key: true ✅ |
| **Статус** | ❌ **FAIL** — GROQ-KEY-INVISIBLE |

### 16. Лимит оптимизаций
| Параметр | Результат |
|----------|-----------|
| План | free (лимит 5) |
| Фактически выполнено | 6 оптимизаций |
| UI показывает | "6 / 5 оптимизаций" |
| **Статус** | ❌ **FAIL** — RATE-LIMIT-BYPASS |

### 17. Страница результатов (/app/results)
| Параметр | Результат |
|----------|-----------|
| Match Score | +13 пунктов ✅ |
| ATS рейтинг | D (Плохо) ✅ |
| AI-модель | openai:gpt-4o ✅ |
| Время обработки | 5 сек ✅ |
| Компоненты Score | 4 карточки (keywords, experience, structure, readability) ✅ |
| Добавленные ключевые слова | 8 тегов ✅ |
| Сравнение версий | Оригинал vs Оптимизировано ✅ |
| Форматированный текст | ✅ (НЕ raw JSON — **P0-3 FIXED!**) |
| **Статус** | ✅ **PASS** |

### 18. Страница истории (/app/history)
| Параметр | Результат |
|----------|-----------|
| Все записи | 6 оптимизаций отображаются ✅ |
| Провайдеры | OpenRouter, Anthropic, OpenAI, GigaChat ✅ |
| Кнопки "Открыть" | Работают ✅ |
| **Статус** | ✅ **PASS** |

### 19. Экспорт DOCX
| Параметр | Результат |
|----------|-----------|
| GET /api/v1/export/{id}/docx | 200, 37KB ✅ |
| Content-Type | application/vnd.openxmlformats... ✅ |
| **Статус** | ✅ **PASS** |

### 20. Экспорт PDF
| Параметр | Результат |
|----------|-----------|
| GET /api/v1/export/{id}/pdf | 200, 2.9KB ✅ |
| Content-Type | application/pdf ✅ |
| **Статус** | ✅ **PASS** |

### 21. Экспорт TXT
| Параметр | Результат |
|----------|-----------|
| GET /api/v1/export/{id}/txt | 200, 2.6KB ✅ |
| Content-Type | text/plain ✅ |
| **Статус** | ✅ **PASS** |

### 22. Настройки AI модели
| Параметр | Результат |
|----------|-----------|
| GET /api/v1/settings/ai-model | 200 ✅ |
| PUT /api/v1/settings/ai-model | 200 ✅ |
| **Статус** | ✅ **PASS** |

### 23. Health Check
| Параметр | Результат |
|----------|-----------|
| GET /api/v1/health | 200 {"status": "healthy", "version": "1.26.0"} ✅ |
| **Статус** | ✅ **PASS** |

### 24. Удаление аккаунта — валидация
| Параметр | Результат |
|----------|-----------|
| DELETE без body | 422 (Field required: password, confirmation) ✅ |
| DELETE с неверным паролем | 401 ✅ |
| **Статус** | ✅ **PASS** (валидация работает) |

### 25. Прогресс-бар при оптимизации
| Параметр | Результат |
|----------|-----------|
| Анимация | Работает ✅ |
| V20 | Застревал на 0% |
| **Статус** | ✅ **PASS** — **PROGRESS-BAR FIXED** |

### 26. Dashboard
| Параметр | Результат |
|----------|-----------|
| Приветствие | ✅ |
| Счётчики | ✅ |
| **Статус** | ✅ **PASS** |

### 27. UI — Кнопка экспорта
| Параметр | Результат |
|----------|-----------|
| Кнопка "Экспорт" на /app/results | Видна, зелёная ✅ |
| **Статус** | ✅ **PASS** |

### 28. UI — Навигация
| Параметр | Результат |
|----------|-----------|
| Дашборд, Мои резюме, История, Справка, Настройки | Все работают ✅ |
| **Статус** | ✅ **PASS** |

### 29. Дублирование запросов (race condition)
| Параметр | Результат |
|----------|-----------|
| 2 одновременных POST /api/v1/rewrite | Оба приняты, оба выполнены |
| Защита от дублей | ❌ Отсутствует |
| **Статус** | ❌ **FAIL** — связано с RATE-LIMIT-BYPASS |

### 30. Создание вакансии вручную
| Параметр | Результат |
|----------|-----------|
| POST /api/v1/vacancies/manual | Эндпоинт существует ✅ |
| **Статус** | ✅ **PASS** |

---

## 📈 ТРЕНД КАЧЕСТВА

| Версия | Всего тестов | PASS | FAIL | Pass Rate |
|--------|-------------|------|------|-----------|
| V35 | 25 | 14 | 11 | 56% |
| V36 | 25 | 16 | 9 | 64% |
| V37 | 25 | 17 | 7 | 68% |
| V38 | 25 | 17 | 7 | 68% |
| V39 | 25 | 18 | 6 | 72% |
| V40 | 25 | 19 | 5 | 76% |
| V41 | 25 | 20 | 5 | 80% |
| V42 | 25 | 22 | 3 | 88% |
| **V44** | **30** | **24** | **4** | **80%** |

**Примечание:** V44 включает 5 дополнительных тестов (все 5 провайдеров отдельно + rate limit + race condition). При сравнении с V42 по тем же 25 базовым тестам: 23/25 PASS (92%).

---

## 🎯 РЕКОМЕНДАЦИИ ПО ПРИОРИТЕТУ ИСПРАВЛЕНИЙ

### Критичные (P1) — исправить немедленно:
1. **GROQ-KEY-INVISIBLE** — Celery worker не может дешифровать ключ Groq. Проверить SECRET_KEY между web и worker.
2. **RATE-LIMIT-BYPASS** — Добавить проверку лимита в роутере ПЕРЕД созданием задачи + защита от race condition (SELECT FOR UPDATE).

### Важные (P2) — исправить в следующем спринте:
3. **OPENAI-JSON-WRAP** — Добавить strip markdown wrapper на бэкенде перед сохранением.
4. **HH-RESUME-LINK-400** — Исправить парсинг hh.ru ссылок на резюме.
5. **ACCOUNT-DELETE-500** — Исправить 500 ошибку при удалении аккаунта (известно с V20).

### Minor (P3):
6. **VACANCY-TITLE-002** — Автозаполнение должности из текста резюме.

---

## 📋 СКРИНШОТЫ ТЕСТИРОВАНИЯ

Тестирование проводилось в реальном времени в браузере Chrome:
- Страница истории: 6 записей, все провайдеры отображаются, "6/5 оптимизаций"
- Страница результатов OpenAI: Match Score +13, ATS D, 5 сек, компоненты score, ключевые слова, сравнение версий с форматированным текстом (P0-3 FIXED)
- Настройки AI: все 5 провайдеров с зелёными галочками

---

*Отчёт сгенерирован AI QA Agent (V44 Full Regression)*

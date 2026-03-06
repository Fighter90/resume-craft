# QA Report #03 — БАГИ БЭКЕНДА И API

**Проект:** ResumeCraft v1.5
**Дата:** 2026-03-06
**Тестировщик:** QA Engineer (10+ лет опыта)
**Метод:** Статический анализ кода роутеров, сервисов, Celery-задач

---

## API-001: Race Condition — счётчик оптимизаций увеличивается до завершения задачи

**Severity:** 🟠 HIGH
**Файл:** `src/app/rewriter/router.py` (строки 53–57)
**Категория:** CWE-362 (Race Condition)

### Описание
```python
# Обновление счётчика оптимизаций
current_user.optimizations_used += 1
await session.flush()

# Отправка в Celery (async)
execute_rewrite_task.delay(str(task.id))
```

Счётчик `optimizations_used` инкрементируется **до** выполнения Celery-задачи. Если задача упадёт:
- Пользователь потеряет одну попытку из лимита
- На тарифе Free (5 попыток) это 20% лимита

### Тест-кейс
1. Пользователь (Free, 4 из 5 использовано) запускает оптимизацию
2. Celery worker недоступен или задача падает
3. `optimizations_used` = 5, оптимизация не получена
4. Пользователь больше не может оптимизировать

### Ожидаемый результат
Счётчик увеличивается только при `status=COMPLETED`.

### Рекомендация
Инкрементировать счётчик в Celery-задаче при успешном завершении, или добавить механизм отката.

---

## API-002: Оптимизация позволяет пустой текст резюме

**Severity:** 🟡 MEDIUM
**Файл:** `src/app/rewriter/service.py` (строки 60–63)

### Описание
```python
original_text = resume.raw_text or ''
if not original_text.strip():
    logger.warning('Resume %s has no raw_text, using empty string', resume_id)
    # ... НО ПРОДОЛЖАЕТ ВЫПОЛНЕНИЕ!
```

Пустой текст отправляется в LLM, что:
- Тратит деньги на API-вызов
- Уменьшает счётчик оптимизаций
- Пользователь получает бессмысленный результат

### Рекомендация
Бросать `ValueError("Resume has no text to optimize")` вместо warning.

---

## API-003: Подсчёт токенов — грубая оценка

**Severity:** 🟢 LOW
**Файл:** `src/app/rewriter/service.py` (строка 148)

### Описание
```python
task.tokens_used = len(response.split()) * 2  # Грубая оценка
```

Для русского текста `split()` по пробелам не учитывает:
- Кириллическую токенизацию (1 слово ≈ 1.5–3 токена в GPT)
- Специфику разных моделей (GigaChat vs OpenAI vs Anthropic)

### Рекомендация
Использовать `tiktoken` для OpenAI или response metadata от провайдера (usage.total_tokens).

---

## API-004: Модель model_name усекается до 50 символов

**Severity:** 🟢 LOW
**Файл:** `src/app/rewriter/service.py` (строка 75)

### Описание
```python
model_name=effective_model[:50],  # VARCHAR(50) limit
```

Если `effective_model` длиннее 50 символов (напр. `openrouter:anthropic/claude-3.5-sonnet-20241022`), имя модели обрезается. Это может привести к невозможности определить, какая модель использовалась.

### Рекомендация
Увеличить VARCHAR(50) до VARCHAR(100) или использовать отдельные колонки provider/model.

---

## API-005: Health check не проверяет зависимости

**Severity:** 🟡 MEDIUM
**Файл:** `src/app/main.py` (строки 98–100)

### Описание
```python
@app.get('/health')
async def health():
    return {'status': 'healthy', 'version': settings.app_version}
```

Health check не проверяет:
- Подключение к PostgreSQL
- Подключение к Redis
- Подключение к RabbitMQ
- Доступность Celery workers

### Рекомендация
```python
@app.get('/health')
async def health(session=Depends(get_session)):
    await session.execute(text("SELECT 1"))  # DB check
    redis.ping()  # Redis check
    return {'status': 'healthy', 'db': 'ok', 'redis': 'ok'}
```

---

## API-006: Нет Content-Length в DOCX-экспорте

**Severity:** 🟢 LOW
**Файл:** `src/app/export/router.py` (строки 49–53)

### Описание
```python
return Response(
    content=docx_bytes,
    media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    headers={'Content-Disposition': f'attachment; filename="resume_{task_id}.docx"'},
    # Нет Content-Length!
)
```

Без `Content-Length` браузер не может показать прогресс скачивания.

### Рекомендация
Добавить `'Content-Length': str(len(docx_bytes))`.

---

## API-007: Celery worker создаёт новый event loop при каждой задаче

**Severity:** 🟡 MEDIUM
**Файл:** `src/app/rewriter/tasks.py`

### Описание
Celery-задача использует `asyncio.run()` или создаёт новый event loop для каждой задачи. Это:
- Потребляет дополнительные ресурсы
- Может вызвать утечки ресурсов при высокой нагрузке
- Не переиспользует DB-пулы

### Рекомендация
Использовать asgiref или celery-pool-asyncio для переиспользования event loop.

---

## API-008: TariffLimitExceeded не показывает текущее использование

**Severity:** 🟢 LOW
**Файл:** `src/app/rewriter/router.py` (строки 40–41)

### Описание
```python
if not current_user.can_optimize:
    raise TariffLimitExceeded()
```

`TariffLimitExceeded()` вызывается без параметров, хотя конструктор поддерживает `used` и `limit`:
```python
class TariffLimitExceeded(AppError):
    def __init__(self, used: int = 0, limit: int = 0):
```

Пользователь видит просто "Лимит исчерпан" без информации о текущем использовании.

### Рекомендация
```python
raise TariffLimitExceeded(
    used=current_user.optimizations_used,
    limit=current_user.optimization_limit or 0,
)
```

---

## API-009: Конфликт маршрутов /rewrite/history и /rewrite/{task_id}/status

**Severity:** 🟡 MEDIUM
**Файл:** `src/app/rewriter/router.py`

### Описание
Маршрут `/rewrite/history` определён **после** `/rewrite/{task_id}/status`. FastAPI матчит маршруты в порядке определения. Строка "history" может быть перехвачена как `{task_id}`, что вызовет ошибку валидации UUID.

### Тест-кейс
```bash
GET /api/v1/rewrite/history  # Ожидается: список истории
# Фактически: может попасть в /{task_id}/status и упасть с 422
```

### Рекомендация
Определить `/rewrite/history` **перед** `/rewrite/{task_id}/*` маршрутами. FastAPI обрабатывает маршруты в порядке объявления — статические маршруты должны идти первыми.

---

## API-010: UserAlreadyExists раскрывает наличие email

**Severity:** 🟡 MEDIUM
**Файл:** `src/app/core/exceptions.py` (строки 52–63)

### Описание
```python
class UserAlreadyExists(AppError):
    def __init__(self, email: str = ''):
        msg = f'Пользователь с email {email} уже существует' if email else ...
```

Ошибка при регистрации раскрывает, что конкретный email уже зарегистрирован. Это позволяет:
- Перечислять (enumerate) зарегистрированные email-адреса
- Использовать для фишинга / социальной инженерии

### Рекомендация
Возвращать общее сообщение: "Если этот email уже зарегистрирован, мы отправили вам письмо для входа."

---

## API-011: Prompt Injection — неполная защита

**Severity:** 🟡 MEDIUM
**Файл:** `src/app/ml/sanitize.py`

### Описание
Санитизация покрывает только 4 паттерна injection:
```python
_INJECTION_PATTERNS = [
    re.compile(r'ignore\s+(previous|above|all)\s+instructions', re.IGNORECASE),
    re.compile(r'system\s*:\s*', re.IGNORECASE),
    re.compile(r'<\|?(system|assistant|user)\|?>', re.IGNORECASE),
    re.compile(r'```\s*(system|prompt)', re.IGNORECASE),
]
```

Не покрыты:
- `[INST]...[/INST]` (Llama формат)
- `Human:` / `Assistant:` (Anthropic формат)
- Unicode-эквиваленты (гомоглифы)
- Multilingual injection (инструкции на других языках)

### Рекомендация
Расширить список паттернов и добавить нормализацию Unicode перед проверкой.

---

## Сводная таблица

| ID | Severity | Описание | Статус v1.6 |
|----|----------|----------|-------------|
| API-001 | 🟠 HIGH | Race condition — счётчик до завершения задачи | ✅ FIXED |
| API-002 | 🟡 MEDIUM | Оптимизация пустого текста | ✅ FIXED |
| API-003 | 🟢 LOW | Грубая оценка токенов | ⏳ Phase 2 |
| API-004 | 🟢 LOW | Усечение model_name | ⏳ Phase 2 |
| API-005 | 🟡 MEDIUM | Health check без проверки зависимостей | ✅ FIXED |
| API-006 | 🟢 LOW | Нет Content-Length при экспорте | ✅ FIXED |
| API-007 | 🟡 MEDIUM | Новый event loop в Celery | ⏳ Phase 2 |
| API-008 | 🟢 LOW | TariffLimitExceeded без деталей | ✅ FIXED |
| API-009 | 🟡 MEDIUM | Конфликт маршрутов /history vs /{task_id} | ✅ FIXED |
| API-010 | 🟡 MEDIUM | Email enumeration через регистрацию | ✅ FIXED |
| API-011 | 🟡 MEDIUM | Неполная защита от prompt injection | ✅ FIXED |

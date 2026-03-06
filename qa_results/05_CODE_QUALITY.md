# QA Report #05 — КАЧЕСТВО КОДА И АРХИТЕКТУРА

**Проект:** ResumeCraft v1.5
**Дата:** 2026-03-06
**Тестировщик:** QA Engineer (10+ лет опыта)
**Метод:** Анализ архитектуры, паттернов, конфигурации, инфраструктуры

---

## ARCH-001: Все порты инфраструктуры открыты на 0.0.0.0

**Severity:** 🟠 HIGH
**Файл:** `docker-compose.yml`

### Описание
Все сервисы привязаны к `0.0.0.0` (все интерфейсы):
```yaml
postgres:
  ports: ["5432:5432"]  # 0.0.0.0:5432
redis:
  ports: ["6379:6379"]  # 0.0.0.0:6379
rabbitmq:
  ports: ["5672:5672", "15672:15672"]  # 0.0.0.0:5672
```

На VPS/облачном сервере PostgreSQL, Redis и RabbitMQ доступны из интернета.

### Рекомендация
Привязать к `127.0.0.1`:
```yaml
ports: ["127.0.0.1:5432:5432"]
```
Или убрать `ports` совсем — Docker network обеспечит связность между сервисами.

---

## ARCH-002: RabbitMQ — дефолтные credentials guest/guest

**Severity:** 🟠 HIGH
**Файл:** `docker-compose.yml`

### Описание
RabbitMQ запущен без кастомных credentials:
```yaml
rabbitmq:
  image: rabbitmq:3-management
  ports: ["5672:5672", "15672:15672"]
  # Нет RABBITMQ_DEFAULT_USER / RABBITMQ_DEFAULT_PASS
```

В сочетании с ARCH-001: RabbitMQ management UI (`port 15672`) доступен из интернета с guest/guest.

### Рекомендация
Добавить environment-переменные для RabbitMQ и закрыть management UI.

---

## ARCH-003: Нет Alembic миграций в CI/CD

**Severity:** 🟡 MEDIUM
**Файл:** Анализ структуры проекта

### Описание
Проект использует Alembic для миграций, но:
- Нет `Makefile` или скрипта для автоматического применения миграций
- docker-compose не содержит `command` для миграций перед запуском backend
- Нет health check на совместимость схемы БД с кодом

### Рекомендация
Добавить entrypoint-скрипт:
```bash
#!/bin/sh
alembic upgrade head && uvicorn src.app.main:create_app --host 0.0.0.0
```

---

## ARCH-004: get_settings() вызывается без кэширования в LLM factory

**Severity:** 🟢 LOW
**Файл:** `src/app/ml/llm_factory.py`

### Описание
`get_settings()` вызывается при каждом создании LLM-клиента. Если это инстанцирует новый объект Settings (парсинг .env), это может быть неэффективно при высокой нагрузке.

### Рекомендация
Использовать `@lru_cache` на `get_settings()` или Depends-injection FastAPI.

---

## ARCH-005: Отсутствие type safety — массовое использование `any`

**Severity:** 🟡 MEDIUM
**Файл:** Практически все фронтенд-файлы

### Описание
Множество файлов начинаются с:
```typescript
/* eslint-disable @typescript-eslint/no-explicit-any */
```

Используются `any` типы для:
- Результатов API (`const res = await api.getRewriteResult(effectiveId) as any`)
- Состояния вакансий (`const [vacancy, setVacancy] = useState<any>(null)`)
- Пропсов компонентов

### Влияние
- Нет compile-time проверок типов
- Runtime-ошибки при изменении API-контракта
- Затрудняет рефакторинг

### Рекомендация
Определить интерфейсы для всех API-ответов и использовать их вместо `any`.

---

## ARCH-006: Нет структурированного логирования

**Severity:** 🟢 LOW
**Файл:** Бэкенд-код в целом

### Описание
Логирование через стандартный `logger.warning()`, `logger.info()` без:
- Correlation ID (request_id) для трейсинга
- Structured JSON для парсинга в ELK/Loki
- Уровней детализации для разных окружений

### Рекомендация
Использовать `structlog` или настроить JSON-формат для production.

---

## ARCH-007: Нет тестов

**Severity:** 🟠 HIGH
**Файл:** Отсутствие директории `tests/`

### Описание
В проекте не обнаружено:
- Unit-тестов (`pytest`, `jest`)
- Integration-тестов
- E2E-тестов
- Файлов конфигурации тестов (`pytest.ini`, `jest.config.ts`)

### Влияние
- Нет confidence при деплое
- Регрессии не ловятся
- Race condition (API-001) и логические ошибки невозможно покрыть без тестов

### Рекомендация
Минимальный набор:
1. Unit: scoring.py, sanitize.py, auth logic
2. Integration: API endpoints с test DB
3. E2E: Cypress/Playwright для wizard flow

---

## ARCH-008: .env файл в репозитории с реальными ключами

**Severity:** 🔴 CRITICAL
**Файл:** `.env` (присутствует в рабочей директории)

### Описание
Несмотря на наличие `.env` в `.gitignore`, файл присутствует в проекте с реальными API-ключами:
- GIGACHAT_CREDENTIALS
- OPENAI_API_KEY
- OPENROUTER_API_KEY
- ANTHROPIC_API_KEY
- SECRET_KEY (placeholder `super-secret-key-change-me`)

### Риски
- Если `.env` был когда-либо закоммичен, ключи в git history
- Placeholder SECRET_KEY в production → предсказуемые JWT токены

### Рекомендация
1. Ротировать все ключи немедленно
2. Проверить git history: `git log --all --full-history -- .env`
3. Использовать `.env.example` с пустыми значениями
4. Сгенерировать криптостойкий SECRET_KEY: `openssl rand -hex 32`

---

## ARCH-009: Inline-стили вместо CSS-модулей

**Severity:** 🟢 LOW
**Файл:** Все фронтенд-компоненты

### Описание
99% стилей заданы через inline `style={{...}}`:
```jsx
<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', padding: '2rem' }}>
```

### Влияние
- Невозможно переиспользовать стили
- Нет поддержки media queries (только через `<style>` блоки, как в AuthPage)
- Увеличение размера бандла из-за дублирования
- Затруднённая поддержка тёмной темы

### Рекомендация
Использовать CSS Modules, Tailwind CSS или styled-components.

---

## ARCH-010: Нет rate limiting на API

**Severity:** 🟠 HIGH
**Файл:** `src/app/main.py` (CORS middleware, но нет rate limiter)

### Описание
API не имеет защиты от брутфорса и DDoS:
- Эндпоинт `/auth/login` — без ограничений на количество попыток
- Эндпоинт `/rewrite` — без ограничений на частоту (кроме тарифного лимита)
- Эндпоинт `/resumes/upload` — без ограничений на размер/частоту

### Рекомендация
Использовать `slowapi` или Redis-based rate limiter:
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post('/auth/login')
@limiter.limit("5/minute")
async def login(request: Request, ...):
```

---

## ARCH-011: Нет graceful shutdown для Celery worker

**Severity:** 🟢 LOW
**Файл:** Docker Compose / Celery configuration

### Описание
При перезапуске контейнера celery_worker текущие задачи могут быть потеряны без механизма:
- SIGTERM handling
- Task acknowledgment strategy
- Dead letter queue

### Рекомендация
Настроить `acks_late=True` и `reject_on_worker_lost=True` для критичных задач.

---

## ARCH-012: Дублирование метода selectSearchVacancy и createVacancyFromUrl

**Severity:** 🟢 LOW
**Файл:** `frontend/src/services/api.ts` (строки 82–84, 199–203)

### Описание
```typescript
async createVacancyFromUrl(url: string) {
  return this.request<unknown>('POST', '/vacancies/from-url', { url })
}

async selectSearchVacancy(hhUrl: string) {
  return this.request<{ id: string }>(
    'POST', '/vacancies/from-url', { url: hhUrl }
  )
}
```

Два метода вызывают один и тот же эндпоинт с разной типизацией (`unknown` vs `{ id: string }`).

### Рекомендация
Удалить `selectSearchVacancy` или объединить в один метод с правильной типизацией.

---

## Сводная таблица

| ID | Severity | Описание | Статус v1.6 |
|----|----------|----------|-------------|
| ARCH-001 | 🟠 HIGH | Порты инфраструктуры открыты на 0.0.0.0 | ✅ FIXED |
| ARCH-002 | 🟠 HIGH | RabbitMQ с guest/guest | ✅ FIXED |
| ARCH-003 | 🟡 MEDIUM | Нет миграций в CI/CD | ⏳ Phase 2 |
| ARCH-004 | 🟢 LOW | get_settings() без кэша | ✅ FIXED |
| ARCH-005 | 🟡 MEDIUM | Массовое использование `any` | ⏳ Phase 2 |
| ARCH-006 | 🟢 LOW | Нет структурированного логирования | ⏳ Phase 2 |
| ARCH-007 | 🟠 HIGH | Нет тестов | ✅ INVALID (1000+ тестов) |
| ARCH-008 | 🔴 CRITICAL | .env с реальными ключами | ⏳ Operational |
| ARCH-009 | 🟢 LOW | Inline-стили | ⏳ Phase 2 |
| ARCH-010 | 🟠 HIGH | Нет rate limiting | ✅ FIXED |
| ARCH-011 | 🟢 LOW | Нет graceful shutdown Celery | ⏳ (has acks_late) |
| ARCH-012 | 🟢 LOW | Дублирование API-методов | ✅ FIXED |

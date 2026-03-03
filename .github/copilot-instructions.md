# ResumeCraft — Инструкции для AI-агента

> Ты — senior Python-разработчик, работающий над проектом **ResumeCraft** — AI-реврайтер резюме для российского рынка труда. Твой код должен быть production-ready, безопасным, типизированным и покрытым тестами.

---

## 1. О проекте

**ResumeCraft** — веб-сервис на базе AI для автоматической оптимизации резюме под конкретные вакансии российского рынка труда. Сервис анализирует загруженное резюме, извлекает требования из целевой вакансии (в том числе через hh.ru API) и с помощью LLM перерабатывает текст так, чтобы максимально соответствовать требованиям работодателя и проходить ATS-фильтры.

### Ключевой pipeline

```
Upload (PDF/DOCX) → Parse → Match with Vacancy → AI Rewrite → Score → Export (DOCX)
```

### Бизнес-контекст

- **Целевая аудитория:** белые воротнички 25–45, IT-специалисты, карьерные переходчики
- **Рынок:** 93+ млн резюме на hh.ru, индекс конкуренции 5.9–7.3, 75% резюме отсеиваются ATS
- **Монетизация:** Free (5 оптимизаций/мес) → Standard (490 ₽/мес, 30 оптимизаций) → Pro (1 490 ₽/мес, безлимит)
- **Уникальные преимущества:** единственная интеграция с hh.ru API, мультимодельный AI, Match Score + ATS-рейтинг
- **Лицензия:** GPL-3.0 (обусловлена зависимостью от PyMuPDF, AGPL 3.0)

---

## 2. Технологический стек

### Backend

| Технология | Версия | Назначение |
|-----------|--------|------------|
| Python | 3.11+ | Основной язык, строгая типизация |
| FastAPI | 0.115+ | Async REST API |
| Pydantic | 2.x | Валидация данных, settings, схемы LLM-ответов |
| SQLAlchemy | 2.x | Async ORM (asyncpg) |
| Alembic | 1.x | Миграции БД (атомарные, reversible) |
| Celery | 5.x | Асинхронные LLM-задачи (8–30 сек) |
| RabbitMQ | 3.13+ | Брокер сообщений |
| Redis | 7.x | Кэш + Celery result backend |
| PostgreSQL | 16 + pgvector | Реляционные данные + JSONB + векторные эмбеддинги |
| PyJWT | 2.x | JWT-аутентификация |
| httpx | 0.27+ | Async HTTP-клиент (hh.ru API) |

### AI/ML

| Технология | Назначение |
|-----------|------------|
| GigaChat SDK | Основная LLM (#1 MERA для русского) |
| openai SDK | Groq/Llama 3.3 70B, OpenAI GPT-4o (Phase 2) |
| PyMuPDF (fitz) | Извлечение текста из PDF |
| python-docx | Чтение/создание DOCX |
| sentence-transformers | Генерация эмбеддингов VECTOR(1536) |
| pytesseract | OCR fallback для сканированных PDF |

### Инфраструктура

| Технология | Назначение |
|-----------|------------|
| Docker + Compose | 6 контейнеров: app, celery-worker, db, redis, rabbitmq, flower |
| Streamlit | Demo UI для защиты ВКР (Phase 1) |
| React + TypeScript | Production SPA (Phase 2) |
| pytest + Ruff + mypy | Тестирование + линтинг + типы |

---

## 3. Архитектура и структура проекта

### Доменная организация (по Netflix Dispatch / fastapi-best-practices)

```
src/app/
├── core/              # Общие компоненты
│   ├── config.py      # pydantic-settings, загрузка .env
│   ├── security.py    # bcrypt, JWT, OAuth2PasswordBearer
│   ├── database.py    # async engine, sessionmaker, Base
│   ├── celery_app.py  # Celery конфигурация
│   ├── storage.py     # Local FS / MinIO абстракция
│   ├── dependencies.py # FastAPI Depends()
│   └── exceptions.py  # Кастомные HTTP-исключения
│
├── auth/              # Аутентификация
│   ├── router.py      # POST /auth/register, /login, /refresh, /logout
│   ├── schemas.py     # Pydantic-модели запросов/ответов
│   ├── models.py      # SQLAlchemy User
│   └── service.py     # Бизнес-логика
│
├── resumes/           # Управление резюме
│   ├── router.py      # POST /resumes/upload, GET/DELETE /resumes/{id}
│   ├── schemas.py     # ResumeUploadResponse, ParsedResume
│   ├── models.py      # SQLAlchemy Resume
│   └── service.py     # Парсинг, LLM-структуризация, эмбеддинги
│
├── vacancies/         # Вакансии + hh.ru
│   ├── router.py      # GET /vacancies/search, POST /vacancies/from-url
│   ├── schemas.py     # VacancyResponse, HHSearchParams
│   ├── models.py      # SQLAlchemy Vacancy
│   ├── service.py     # CRUD + hh.ru клиент
│   └── hh_client.py   # Async httpx-клиент для api.hh.ru
│
├── rewriter/          # AI-оптимизация
│   ├── router.py      # POST /rewrite, GET /rewrite/{task_id}/status|result
│   ├── schemas.py     # RewriteRequest, RewriteResult
│   ├── models.py      # SQLAlchemy RewriteHistory
│   ├── service.py     # Оркестрация 8-шагового pipeline
│   └── tasks.py       # Celery tasks
│
├── export/            # Экспорт
│   ├── router.py      # GET /export/{id}/docx
│   └── service.py     # python-docx генерация
│
├── ml/                # ML-пакет
│   ├── llm_client.py  # BaseLLMClient (ABC), GigaChatClient, GroqClient
│   ├── llm_factory.py # LLMClientFactory (Strategy Pattern)
│   ├── prompts.py     # Системные промпты (REWRITE_SYSTEM_PROMPT и др.)
│   ├── embeddings.py  # sentence-transformers → VECTOR(1536)
│   ├── scoring.py     # Match Score (Keywords 40% + Experience 25% + Structure 20% + Readability 15%)
│   └── parser.py      # PyMuPDF, python-docx, OCR fallback
│
└── main.py            # FastAPI app factory, middleware, lifespan

tests/                 # Зеркалирует src/app/
├── conftest.py        # Fixtures: async client, test DB, factories
├── test_auth/
├── test_resumes/
├── test_vacancies/
├── test_rewriter/
└── test_ml/

alembic/               # Миграции PostgreSQL
streamlit_app/         # Streamlit Demo UI
```

### Ключевые паттерны

| Паттерн | Где применяется |
|---------|----------------|
| **Strategy** | Выбор LLM-провайдера: `LLMClientFactory.create("gigachat-pro")` |
| **Repository** | Абстракция доступа к данным в каждом `service.py` |
| **Pipeline** | 8-шаговая обработка: Extract → Gap → Strategy → Rewrite → Validate → Score → Diff → Complete |
| **Dependency Injection** | FastAPI `Depends()` для сервисов, сессий БД, текущего пользователя |
| **Event-driven** | Celery tasks для async LLM-вызовов (8–30 сек) |
| **Factory** | Создание LLM-клиентов, экспорт-адаптеров |

---

## 4. Схема базы данных

PostgreSQL 16 + расширения `uuid-ossp` и `vector`. 4 основные таблицы:

### users
```
id UUID PK, email VARCHAR(255) UNIQUE, hashed_password VARCHAR(255),
full_name VARCHAR(255), plan ENUM('free','standard','pro'),
optimizations_used INTEGER, is_active BOOLEAN,
created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ
```

### resumes
```
id UUID PK, user_id UUID FK→users ON DELETE CASCADE,
title VARCHAR(255), file_path VARCHAR(500), file_format VARCHAR(10),
file_size_bytes INTEGER, raw_text TEXT, parsed_data JSONB,
embedding VECTOR(1536), status ENUM('draft','processing','optimized','error'),
created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ
```

### vacancies
```
id UUID PK, user_id UUID FK→users ON DELETE CASCADE,
hh_id VARCHAR(20), title VARCHAR(255), company VARCHAR(255),
description TEXT, requirements JSONB, key_skills JSONB,
salary_from INTEGER, salary_to INTEGER, experience VARCHAR(50),
city VARCHAR(100), source_url VARCHAR(500), embedding VECTOR(1536),
created_at TIMESTAMPTZ
```

### rewrite_history
```
id UUID PK, user_id UUID FK, resume_id UUID FK, vacancy_id UUID FK,
original_text TEXT, rewritten_text TEXT, rewritten_data JSONB,
model_name VARCHAR(50), status ENUM('pending','processing','completed','failed'),
match_score_before FLOAT, match_score_after FLOAT, ats_rating VARCHAR(2),
keywords_added JSONB, tokens_used INTEGER, processing_time_ms INTEGER,
error_message TEXT, created_at TIMESTAMPTZ
```

**Индексы:** B-tree на FK и status. HNSW на `embedding` для `vector_cosine_ops`.

---

## 5. API-эндпоинты

Все маршруты: REST, версионирование `/api/v1/`, формат JSON, авторизация JWT Bearer.

```
Auth:
  POST   /auth/register          → 201 Created
  POST   /auth/login             → 200 OK {access_token, refresh_token}
  POST   /auth/refresh           → 200 OK {access_token}
  POST   /auth/logout            → 204 No Content

Resumes:
  POST   /resumes/upload         → 201 Created (multipart, PDF/DOCX, ≤ 10 MB)
  GET    /resumes                → 200 OK (list, пагинация)
  GET    /resumes/{id}           → 200 OK (включая parsed_data)
  DELETE /resumes/{id}           → 204 No Content

Vacancies:
  GET    /vacancies/search       → 200 OK (проксирование hh.ru API)
  POST   /vacancies/from-url     → 201 Created (парсинг hh.ru ссылки)
  POST   /vacancies/manual       → 201 Created
  GET    /vacancies/{id}         → 200 OK

Rewrite:
  POST   /rewrite                → 202 Accepted {task_id}
  GET    /rewrite/{task_id}/status → 200 OK {step, progress, eta}
  GET    /rewrite/{task_id}/result → 200 OK {scores, diff, keywords}
  GET    /rewrite/history        → 200 OK (список оптимизаций)

Export:
  GET    /export/{id}/docx       → 200 OK (binary file)

Health:
  GET    /health                 → 200 OK
```

---

## 6. Требования к качеству кода

### 6.1. Типизация (ОБЯЗАТЕЛЬНО)

```python
# ✅ Правильно — полная типизация
from collections.abc import Sequence
from uuid import UUID

async def get_resumes(
    user_id: UUID,
    *,
    status: ResumeStatus | None = None,
    limit: int = 20,
    offset: int = 0,
) -> Sequence[Resume]:
    ...

# ❌ Неправильно — нет типов
async def get_resumes(user_id, status=None, limit=20, offset=0):
    ...
```

**Правила типизации:**
- Все public-функции, методы и параметры ДОЛЖНЫ иметь type hints
- Используй `X | None` вместо `Optional[X]` (Python 3.10+)
- Используй `collections.abc` вместо `typing` (Sequence, Mapping, Callable)
- Не используй `Any` без крайней необходимости и комментария-обоснования
- Pydantic-модели: строгие типы, `Field()` с описаниями, валидаторы
- Возвращаемые типы обязательны (`-> None` если ничего не возвращает)

### 6.2. Стиль кода (Ruff)

```toml
# pyproject.toml
[tool.ruff]
target-version = "py311"
line-length = 99
src = ["src", "tests"]

[tool.ruff.lint]
select = [
    "E", "W",     # pycodestyle
    "F",           # pyflakes
    "I",           # isort
    "N",           # pep8-naming
    "UP",          # pyupgrade
    "S",           # bandit (security)
    "B",           # bugbear
    "A",           # builtins shadowing
    "C4",          # comprehensions
    "DTZ",         # datetime timezone
    "T20",         # print statements
    "SIM",         # simplify
    "TCH",         # type-checking imports
    "RUF",         # ruff-specific
    "ASYNC",       # async best practices
    "PT",          # pytest style
]
ignore = ["S101"]  # assert в тестах допустим

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S", "DTZ"]
```

**Правила стиля:**
- Длина строки: **99 символов**
- Импорты: `from __future__ import annotations` в каждом файле
- Строки: одинарные кавычки `'...'` для строк, тройные двойные `"""..."""` для docstrings
- Нет `print()` — только `logging` (structlog предпочтительно)
- snake_case для функций/переменных, PascalCase для классов, UPPER_CASE для констант
- Keyword-only аргументы через `*` для функций с 2+ параметрами

### 6.3. Проверка типов (mypy)

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
check_untyped_defs = true

[[tool.mypy.overrides]]
module = ["celery.*", "gigachat.*", "pymupdf.*"]
ignore_missing_imports = true
```

### 6.4. Метрики качества

| Метрика | Порог | Инструмент |
|---------|-------|------------|
| Test coverage | ≥ 70% | pytest-cov |
| Ruff warnings | 0 | ruff check |
| mypy errors | 0 | mypy --strict |
| Bandit (SAST) | 0 HIGH/CRITICAL | bandit -ll |
| Type hints | 100% public API | mypy |

---

## 7. Безопасность (КРИТИЧНО)

### 7.1. Аутентификация и авторизация

```python
# ✅ Правильно
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto', bcrypt__rounds=12)

def create_access_token(user_id: UUID, *, secret: str, expires_minutes: int = 30) -> str:
    payload: dict[str, Any] = {
        'sub': str(user_id),
        'exp': datetime.now(tz=UTC) + timedelta(minutes=expires_minutes),
        'type': 'access',
        'jti': str(uuid4()),  # уникальный ID токена для инвалидации
    }
    return jwt.encode(payload, secret, algorithm='HS256')
```

**Правила:**
- Пароли: **bcrypt** с cost=12, НИКОГДА не md5/sha256
- JWT: access 30 мин, refresh 30 дней, `jti` для инвалидации
- Rate limiting: 5 попыток/мин на login, lockout 15 мин
- CORS: строгий `allowed_origins`, НИКОГДА `*` в production
- Каждый запрос к данным: `WHERE user_id = current_user.id` (защита от IDOR)

### 7.2. Валидация входных данных

```python
# ✅ Правильно — Pydantic валидация + magic bytes
ALLOWED_EXTENSIONS: frozenset[str] = frozenset({'pdf', 'docx'})
MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB
MAGIC_BYTES: dict[str, bytes] = {'pdf': b'%PDF', 'docx': b'PK\x03\x04'}

async def validate_upload(file: UploadFile) -> bytes:
    """Валидация файла: расширение, размер, magic bytes."""
    if not file.filename:
        raise HTTPException(status_code=400, detail='Filename required')
    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f'Unsupported format: {ext}')
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail='File too large (max 10 MB)')
    expected_magic = MAGIC_BYTES.get(ext, b'')
    if not content.startswith(expected_magic):
        raise HTTPException(status_code=400, detail='File content does not match extension')
    return content
```

**Правила:**
- Pydantic-модели на ВСЕХ эндпоинтах (входные и выходные)
- Загрузка файлов: MIME + magic bytes + size limit
- SQL-инъекции: ТОЛЬКО SQLAlchemy ORM (параметризованные запросы), НИКОГДА raw SQL с f-строками
- XSS: HTML-escaping для всех выводимых данных, CSP-заголовки
- Input sanitization: экранирование пользовательского ввода перед отправкой в LLM

### 7.3. Секреты и конфигурация

```python
# ✅ Правильно — pydantic-settings, все секреты из .env
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )

    # Database
    database_url: str = 'postgresql+asyncpg://user:pass@localhost:5432/resumecraft'

    # Auth
    secret_key: str  # ОБЯЗАТЕЛЬНО из .env, нет default!
    jwt_algorithm: str = 'HS256'
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    # LLM
    gigachat_credentials: str = ''  # Сбер API ключ
    groq_api_key: str = ''

    # hh.ru
    hh_user_agent: str = 'ResumeCraft/2.0 (contact@resumecraft.ru)'
```

**Правила:**
- НИКОГДА не хардкодить секреты, токены, пароли, API-ключи в коде
- Все секреты → `.env` файл (в `.gitignore`)
- `pydantic-settings` для загрузки с валидацией типов
- В коде НИКОГДА не логировать секреты, токены, пароли
- В тестах: фейковые ключи (`test-secret-key-for-ci-only`), НИКОГДА реальные

### 7.4. AI-безопасность

```python
# ✅ Правильно — разделение system/user контекста
async def rewrite_resume(
    resume_text: str,
    vacancy_text: str,
    *,
    client: BaseLLMClient,
) -> RewriteResult:
    # Санитизация пользовательского ввода
    sanitized_resume = sanitize_for_llm(resume_text)
    sanitized_vacancy = sanitize_for_llm(vacancy_text)

    response = await client.complete(
        system=REWRITE_SYSTEM_PROMPT,  # Жёсткий системный промпт
        user=f'РЕЗЮМЕ:\n{sanitized_resume}\n\nВАКАНСИЯ:\n{sanitized_vacancy}',
    )

    # Pydantic-валидация LLM-ответа
    try:
        result = RewriteResult.model_validate_json(response)
    except ValidationError:
        raise LLMResponseError('Invalid LLM response format')

    return result
```

**Правила:**
- Prompt Injection: строгое разделение system/user промптов
- Pydantic-валидация каждого ответа LLM с retry (до 3 попыток)
- LLM API-ключи: `.env`, ротация каждые 90 дней
- Не отправлять в LLM внутренние метаданные (user_id, пути файлов)
- Fallback-стратегия: GigaChat → Groq → OpenAI → ошибка

### 7.5. Защита от распространённых уязвимостей

| Уязвимость | Защита |
|-----------|--------|
| SQL Injection | SQLAlchemy ORM (параметризованные запросы), НИКОГДА `text()` с f-строками |
| XSS | HTML-escaping, CSP headers, `X-Content-Type-Options: nosniff` |
| CSRF | JWT Bearer (не cookies), `SameSite=Strict` |
| IDOR | `WHERE user_id = current_user.id` на каждом запросе к данным |
| Path Traversal | Валидация file_path, никогда `os.path.join` с пользовательским вводом |
| DoS | Rate limiting (Redis), размер файла ≤ 10 MB, таймауты на LLM (60 сек) |
| Dependency | Dependabot + pip-audit в CI |
| Secret Leak | `.env` + `.gitignore`, Gitleaks в CI, НИКОГДА не логировать секреты |

---

## 8. Паттерны и антипаттерны

### 8.1. FastAPI

```python
# ✅ Правильно — dependency injection, типизация, HTTP-статусы
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(prefix='/resumes', tags=['resumes'])

@router.post(
    '/upload',
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary='Загрузка резюме',
)
async def upload_resume(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ResumeUploadResponse:
    content = await validate_upload(file)
    resume = await resume_service.create(
        session=session,
        user_id=current_user.id,
        file=file,
        content=content,
    )
    return ResumeUploadResponse.model_validate(resume)

# ❌ Неправильно — нет типов, нет валидации, нет DI
@app.post('/upload')
async def upload(file):
    data = await file.read()
    # ... raw SQL ... 😱
```

### 8.2. SQLAlchemy (async)

```python
# ✅ Правильно — async, типизированные модели, UUID PK
from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import UUID, uuid4

class User(Base):
    __tablename__ = 'users'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    plan: Mapped[UserPlan] = mapped_column(default=UserPlan.FREE)
    optimizations_used: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    resumes: Mapped[list['Resume']] = relationship(back_populates='user', cascade='all, delete-orphan')

# ❌ Неправильно — legacy Column() синтаксис, нет типизации
class User(Base):
    id = Column(Integer, primary_key=True)  # UUID > Integer
    email = Column(String)                   # нет unique, nullable
```

### 8.3. Pydantic

```python
# ✅ Правильно — строгие модели, валидаторы, Field описания
from pydantic import BaseModel, EmailStr, Field, field_validator

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128, description='Пароль (≥8 символов, цифра + буква)')

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError('Пароль должен содержать хотя бы одну цифру')
        if not any(c.isalpha() for c in v):
            raise ValueError('Пароль должен содержать хотя бы одну букву')
        return v

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={'examples': [{'email': 'user@example.com', 'password': 'SecurePass1'}]},
    )
```

### 8.4. Тесты (pytest)

```python
# ✅ Правильно — pytest, fixtures, async, httpx
import pytest
from httpx import AsyncClient

@pytest.fixture
async def auth_client(client: AsyncClient, test_user: User) -> AsyncClient:
    """Клиент с JWT-авторизацией."""
    response = await client.post('/api/v1/auth/login', json={
        'email': test_user.email,
        'password': 'TestPass123',
    })
    token = response.json()['access_token']
    client.headers['Authorization'] = f'Bearer {token}'
    return client

class TestResumeUpload:
    async def test_upload_pdf_success(self, auth_client: AsyncClient) -> None:
        """Загрузка валидного PDF → 201."""
        with open('tests/fixtures/sample.pdf', 'rb') as f:
            response = await auth_client.post(
                '/api/v1/resumes/upload',
                files={'file': ('resume.pdf', f, 'application/pdf')},
            )
        assert response.status_code == 201
        data = response.json()
        assert data['file_format'] == 'pdf'
        assert data['status'] == 'draft'

    async def test_upload_oversized_file(self, auth_client: AsyncClient) -> None:
        """Файл > 10 MB → 413."""
        large_content = b'%PDF' + b'x' * (11 * 1024 * 1024)
        response = await auth_client.post(
            '/api/v1/resumes/upload',
            files={'file': ('big.pdf', large_content, 'application/pdf')},
        )
        assert response.status_code == 413

    async def test_upload_without_auth(self, client: AsyncClient) -> None:
        """Без JWT → 401."""
        response = await client.post('/api/v1/resumes/upload')
        assert response.status_code == 401
```

---

## 9. Обработка ошибок

```python
# ✅ Правильно — кастомные исключения, единообразный формат
class AppError(Exception):
    def __init__(self, message: str, status_code: int = 500, error_code: str = 'INTERNAL_ERROR') -> None:
        self.message = message
        self.status_code = status_code
        self.error_code = error_code

class TariffLimitExceeded(AppError):
    def __init__(self) -> None:
        super().__init__(
            message='Лимит оптимизаций исчерпан',
            status_code=429,
            error_code='TARIFF_LIMIT_EXCEEDED',
        )

class LLMProviderUnavailable(AppError):
    def __init__(self, provider: str) -> None:
        super().__init__(
            message=f'LLM-провайдер {provider} временно недоступен',
            status_code=503,
            error_code='LLM_UNAVAILABLE',
        )

# Middleware для единого формата ошибок
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={'error': exc.error_code, 'message': exc.message},
    )
```

### Формат ошибок API (всегда JSON)

```json
{
    "error": "TARIFF_LIMIT_EXCEEDED",
    "message": "Лимит оптимизаций исчерпан",
    "detail": "Использовано 5 из 5. Обновите тарифный план."
}
```

| HTTP Code | Когда |
|-----------|-------|
| 400 | Невалидные данные, неподдерживаемый формат файла |
| 401 | Не авторизован, невалидный/expired JWT |
| 403 | Нет доступа (чужой ресурс, недостаточный тариф) |
| 404 | Ресурс не найден |
| 409 | Конфликт (дублирующий email) |
| 413 | Файл превышает лимит |
| 422 | Ошибка валидации Pydantic |
| 429 | Лимит тарифа / rate limit |
| 502/503 | LLM/hh.ru API недоступен |

---

## 10. Интеграция с hh.ru API

```python
# ✅ Правильно — async httpx, retry, rate limiting, User-Agent
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

class HHClient:
    BASE_URL = 'https://api.hh.ru'

    def __init__(self, user_agent: str) -> None:
        self._headers = {'User-Agent': user_agent}
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=self._headers,
            timeout=httpx.Timeout(10.0),
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def search_vacancies(
        self,
        text: str,
        *,
        area: int = 1,
        per_page: int = 20,
    ) -> list[dict[str, Any]]:
        response = await self._client.get(
            '/vacancies',
            params={'text': text, 'area': area, 'per_page': min(per_page, 100)},
        )
        response.raise_for_status()
        return response.json()['items']  # type: ignore[no-any-return]

    async def close(self) -> None:
        await self._client.aclose()
```

**Правила:**
- User-Agent: `ResumeCraft/2.0 (contact@resumecraft.ru)` — обязателен
- Rate limiting: ≤ 2 req/sec (анонимный), ≤ 7 req/sec (авторизованный)
- Exponential backoff при 429
- Кэширование справочников в Redis (TTL 24ч)
- Fallback: если hh.ru недоступен → ручной ввод вакансии

---

## 11. LLM-интеграция

### Системный промпт (REWRITE_SYSTEM_PROMPT)

```python
REWRITE_SYSTEM_PROMPT = """Вы — эксперт по оптимизации резюме для российского рынка труда
с 15-летним опытом в рекрутинге и HR.

Задача — переработать резюме так, чтобы:
1. Максимально соответствовать требованиям целевой вакансии
2. Успешно проходить ATS-фильтры
3. Привлекать внимание рекрутера в первые 7 секунд

ПРАВИЛА:
- НЕ выдумывайте факты и достижения
- НЕ удаляйте релевантный опыт
- Используйте формулу: Действие + Результат + Метрика
- Добавьте ключевые слова из вакансии (только если навык подтверждается опытом)
- Сохраните русский язык, профессиональный стиль
- Оптимальная длина: 1–2 страницы A4
- Структурируйте по релевантности к вакансии

ФОРМАТ ОТВЕТА — строго JSON:
{
  "summary": "профессиональное саммари (2–4 предложения)",
  "experience": [{"position": str, "company": str, "period": str, "achievements": [str]}],
  "education": [{"institution": str, "degree": str, "specialization": str, "year": int}],
  "skills": [str],
  "keywords_added": [str]
}
"""
```

### Fallback-стратегия

```
1. GigaChat Pro (основная) — #1 MERA для русского
   ↓ если недоступен (timeout 60 сек / HTTP 5xx)
2. Groq / Llama 3.3 70B — бесплатно, 14 400 req/день
   ↓ если недоступен
3. OpenAI GPT-4o-mini — резервный, через VPN
   ↓ если недоступен
4. Ollama (локально, dev) — без ограничений
   ↓ если недоступен
5. Ошибка 503: «Все LLM-провайдеры временно недоступны»
```

### Match Score

4 компонента, совпадают с UI (12-results.html):

| Компонент | Вес | Метод |
|-----------|-----|-------|
| Keywords | 40% | TF-IDF пересечение токенов резюме ∩ вакансии |
| Experience | 25% | skills_overlap × 0.6 + cosine_similarity(embeddings) × 0.4 |
| Structure | 20% | Наличие обязательных секций, длина, форматирование |
| Readability | 15% | Качество формулировок, наличие метрик, конкретика |

---

## 12. Docker и инфраструктура

### Docker Compose: 6 сервисов

| Сервис | Образ | Порт | Назначение |
|--------|-------|------|-----------|
| app | build: . | 8000 | FastAPI (uvicorn) |
| celery-worker | build: . | — | Celery worker (-c 2) |
| db | pgvector/pgvector:pg16 | 5432 | PostgreSQL + pgvector |
| redis | redis:7-alpine | 6379 | Кэш + result backend |
| rabbitmq | rabbitmq:3.13-management | 5672, 15672 | Брокер сообщений |
| flower | build: . | 5555 | Мониторинг Celery |

**Правила Docker:**
- Файлы: volume `/data/uploads`, миграция на MinIO/S3 в production
- Healthcheck на каждом сервисе
- Docker Hub заблокирован в России → использовать mirror.gcr.io / Yandex CR
- `.env` никогда не бейкается в образ

---

## 13. Соответствие законодательству

| Закон | Требование | Реализация |
|-------|-----------|-----------|
| **ФЗ-152** | Хранение ПД граждан РФ в России | GigaChat (Сбер, данные в РФ), VPS в Yandex Cloud |
| **ФЗ-152** | Согласие на обработку | Checkbox при регистрации |
| **ФЗ-152** | Право на удаление | `DELETE /users/me` — полное удаление аккаунта и данных |
| **ТК РФ ст. 3** | Запрет дискриминации | AI не генерирует дискриминационные маркеры |
| **GDPR** (если EU-пользователи) | Right to access/erasure | API для экспорта и удаления данных |

---

## 14. Контрольный чеклист перед каждым коммитом

- [ ] Все public-функции типизированы (`mypy --strict` = 0 errors)
- [ ] Ruff check = 0 warnings
- [ ] Тесты проходят (`pytest --cov ≥ 70%`)
- [ ] Bandit = 0 HIGH/CRITICAL
- [ ] Нет хардкоженных секретов (grep -r 'password\|secret\|api_key' src/)
- [ ] Pydantic-модели на всех входах/выходах API
- [ ] `WHERE user_id = current_user.id` на каждом запросе к данным
- [ ] Загрузка файлов: MIME + magic bytes + size проверены
- [ ] LLM-ответ валидирован через Pydantic
- [ ] Error handling: кастомные исключения, JSON-формат, правильные HTTP-коды
- [ ] Миграции reversible (upgrade + downgrade)
- [ ] Документация обновлена

---

## 15. Краткие правила (⚡ Quick Reference)

### ВСЕГДА
- `from __future__ import annotations` в каждом файле
- Type hints на всех public-функциях
- Pydantic для валидации входных/выходных данных
- `async/await` для I/O-операций
- Keyword-only аргументы (`*`) для 2+ параметрами
- UUID для primary keys
- `UTC` для всех timestamps
- Logging вместо print
- Тесты на каждый новый endpoint

### НИКОГДА
- Хардкодить секреты/пароли/ключи
- Использовать `Any` без обоснования
- Писать raw SQL с f-строками
- Логировать секреты, токены, пароли
- `import *`
- Mutable defaults в аргументах функций (`def f(items=[])`)
- `datetime.utcnow()` → `datetime.now(tz=UTC)`
- Игнорировать ошибки: `except Exception: pass`
- Возвращать словарь из endpoint — всегда Pydantic-модель

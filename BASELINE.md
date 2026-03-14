# ResumeCraft — Baseline MVP

> **Версия:** 1.26.0 (V44)
> **Дата:** 14 марта 2026
> **Тип документа:** Техническая спецификация MVP  
> **Связанные документы:** README.md (обзор), ANALYSIS.md (аудитория), REFERENCES.md (источники)

---

## Содержание

1. [Введение](#1-введение)
2. [Определение MVP](#2-определение-mvp)
3. [Функциональные требования](#3-функциональные-требования)
4. [Нефункциональные требования](#4-нефункциональные-требования)
5. [Пользовательские истории](#5-пользовательские-истории)
6. [Архитектура MVP](#6-архитектура-mvp)
7. [Технический стек](#7-технический-стек)
8. [Схема данных](#8-схема-данных)
9. [API-спецификация](#9-api-спецификация)
10. [AI/ML Pipeline](#10-aiml-pipeline)
11. [React SPA Frontend](#11-react-spa-frontend)
12. [Интеграция с hh.ru API](#12-интеграция-с-hhru-api)
13. [Безопасность](#13-безопасность)
14. [Тестирование](#14-тестирование)
15. [Инфраструктура и деплой](#15-инфраструктура-и-деплой)
16. [Критерии приёмки](#16-критерии-приёмки)
17. [Управление рисками](#17-управление-рисками)
18. [Границы MVP](#18-границы-mvp)

---

## 1. Введение

### 1.1. Цели документа

| Цель | Описание |
|------|----------|
| **Scope** | Определить точные границы MVP |
| **Contract** | Зафиксировать функциональные и нефункциональные требования |
| **Blueprint** | Предоставить технические спецификации для реализации |
| **Verification** | Определить критерии приёмки (Definition of Done) |

### 1.2. Принципы MVP

1. **YAGNI** — реализуем только то, что нужно для demo и первых пользователей
2. **API-first** — backend API не зависит от UI; React SPA вызывает те же REST-эндпоинты
3. **Fail-safe** — при недоступности LLM → fallback, при ошибке парсинга → graceful degradation
4. **Data-driven** — решения основаны на данных рынка (ANALYSIS.md) и источниках (REFERENCES.md)
5. **Ship fast** — MVP за 8 недель, один full-stack разработчик

---

## 2. Определение MVP

**Value Proposition:** Загрузи резюме + выбери вакансию → получи AI-оптимизированную версию за 30 секунд.

**Формула MVP:**

```
Upload (PDF/DOCX) → Parse → Match with Vacancy → AI Rewrite → Score → Export (DOCX)
```

**Что НЕ входит в MVP:**
- OAuth hh.ru для соискателей (→ Phase 2, используем анонимный API)
- ЮKassa платежи (→ Phase 2, заменено на Робокассу)
- 2FA (→ Phase 2)
- Интерактивный WYSIWYG-редактор (→ Phase 2)
- Экспорт-шаблоны Creative/Professional (→ Phase 2)

**Реализовано сверх начального плана:**
- ✅ PDF-экспорт (reportlab) и TXT-экспорт
- ✅ Шаблон экспорта Minimal
- ✅ Email-верификация (JWT 24ч токен)
- ✅ GPT-4o через OpenAI SDK
- ✅ OpenRouter (100+ моделей)
- ✅ Модуль settings с шифрованием API-ключей (AES)
- ✅ Аватар пользователя (серверное хранение)
- ✅ Soft-delete аккаунтов и резюме с восстановлением
- ✅ DOCX-просмотр резюме (mammoth.js)
- ✅ 22 React-страницы (Privacy, Terms, About, Help, ResumeDetail)

---

## 3. Функциональные требования

### 3.1. Auth — Аутентификация

| ID | Приоритет | Требование |
|----|-----------|-----------|
| AUTH-01 | Must | Регистрация по email + пароль |
| AUTH-02 | Must | Вход по email + пароль → JWT |
| AUTH-03 | Must | Refresh token (30 дней) |
| AUTH-04 | Must | Logout (инвалидация refresh) |
| AUTH-05 | Should | Валидация пароля (≥8 символов, цифра, буква) |
| AUTH-06 | Could | Rate limiting (5 попыток/мин) |

### 3.2. Resumes — Управление резюме

| ID | Приоритет | Требование |
|----|-----------|-----------|
| RES-01 | Must | Загрузка PDF (≤ 10 МБ) |
| RES-02 | Must | Загрузка DOCX (≤ 10 МБ) |
| RES-03 | Must | MIME-валидация (magic bytes) |
| RES-04 | Must | Извлечение текста из PDF (PyMuPDF) |
| RES-05 | Must | Извлечение текста из DOCX (python-docx) |
| RES-06 | Must | LLM-структуризация (имя, опыт, навыки, образование) |
| RES-07 | Must | Генерация эмбеддинга (VECTOR 1536) |
| RES-08 | Must | Список загруженных резюме |
| RES-09 | Must | Просмотр деталей резюме |
| RES-10 | Must | Удаление резюме (+ файл из хранилища) |
| RES-11 | Could | OCR fallback для сканированных PDF |

### 3.3. Vacancies — Вакансии

| ID | Приоритет | Требование |
|----|-----------|-----------|
| VAC-01 | Must | Поиск вакансий через hh.ru API (анонимный) |
| VAC-02 | Must | Импорт вакансии по URL hh.ru |
| VAC-03 | Must | Ручной ввод вакансии |
| VAC-04 | Must | Извлечение требований и ключевых навыков |
| VAC-05 | Must | Генерация эмбеддинга вакансии |
| VAC-06 | Should | Кэширование справочников hh.ru (Redis) |

### 3.4. Rewriter — AI-оптимизация

| ID | Приоритет | Требование |
|----|-----------|-----------|
| RW-01 | Must | Оптимизация через GigaChat Pro |
| RW-02 | Must | Оптимизация через Anthropic Claude |
| RW-03 | Must | 8-шаговый pipeline (Extract → Complete) |
| RW-04 | Must | Match Score (до и после, 0–100) |
| RW-05 | Must | ATS-рейтинг (A+ – F) |
| RW-06 | Must | Diff: список изменений и ключевых слов |
| RW-07 | Must | Celery task с прогрессом (polling) |
| RW-08 | Must | Сохранение в rewrite_history |
| RW-09 | Must | Проверка лимитов тарифа |
| RW-10 | Should | Fallback GigaChat → Anthropic → OpenRouter → OpenAI → Groq |
| RW-11 | Should | Pydantic-валидация LLM-ответа + retry (до 3) |

### 3.5. Export — Экспорт

| ID | Приоритет | Требование | Статус |
|----|-----------|-----------|--------|
| EXP-01 | Must | Экспорт в DOCX (python-docx) | ✅ |
| EXP-02 | Should | Экспорт в PDF (reportlab) | ✅ |
| EXP-03 | Should | Экспорт в TXT (plain text) | ✅ |
| EXP-04 | Could | Шаблон «Minimal» | ✅ |

### 3.6. Settings — Настройки пользователя

| ID | Приоритет | Требование | Статус |
|----|-----------|-----------|--------|
| SET-01 | Must | Управление API-ключами LLM (зашифрованное хранение, AES) | ✅ |
| SET-02 | Must | Выбор AI-модели и подмодели | ✅ |
| SET-03 | Should | AI-настройки (toggles) | ✅ |
| SET-04 | Should | Загрузка/удаление аватара (серверное хранение) | ✅ |

### 3.7. Models — AI-модели

| ID | Приоритет | Требование | Статус |
|----|-----------|-----------|--------|
| MOD-01 | Must | Список доступных провайдеров с проверкой ключей | ✅ |
| MOD-02 | Should | Динамические подмодели через API провайдеров | ✅ |

---

## 4. Нефункциональные требования

### 4.1. Производительность

| Метрика | Требование |
|---------|-----------|
| API response (CRUD) | < 200 мс (p95) |
| Resume upload + parsing | < 10 сек |
| AI-оптимизация (Anthropic Claude) | < 15 сек |
| AI-оптимизация (GigaChat) | < 30 сек |
| Concurrent users | 100 (при 4 workers) |

### 4.2. Надёжность

| Метрика | Требование |
|---------|-----------|
| Uptime (локальная среда) | 99% |
| LLM fallback | Автоматический при ошибке |
| Data durability | PostgreSQL WAL + docker volume |

### 4.3. Безопасность

| Метрика | Требование |
|---------|-----------|
| Пароли | bcrypt (cost=12) |
| JWT | HS256, access 30 мин, refresh 30 дней |
| SQL injection | SQLAlchemy ORM (параметризованные запросы) |
| File upload | MIME + magic bytes + size limit |
| Secrets | .env (не в git) |

### 4.4. Качество кода

| Метрика | Требование | Факт |
|---------|-----------|------|
| Test coverage | ≥ 70% | **100%** |
| Ruff warnings | 0 | **0** |
| mypy errors | 0 | **0** |
| Type hints | Все public-функции | **100%** |
| Backend тестов | — | **691** |
| Frontend тестов | — | **525** |
| Всего тестов | — | **1216** |

---

## 5. Пользовательские истории

### 5.1. Epic: Аутентификация

**US-01:** Как новый пользователь, я хочу зарегистрироваться по email, чтобы получить доступ к сервису.

```
Given: Не авторизован
When:  POST /auth/register {email, password}
Then:  201 Created, получаю access + refresh tokens
```

**US-02:** Как зарегистрированный пользователь, я хочу войти, чтобы продолжить работу.

```
Given: Аккаунт существует
When:  POST /auth/login {email, password}
Then:  200 OK, получаю access + refresh tokens
```

**US-03:** Как авторизованный пользователь, я хочу обновить токен, чтобы не вводить пароль повторно.

```
Given: Есть валидный refresh token
When:  POST /auth/refresh {refresh_token}
Then:  200 OK, получаю новый access token
```

### 5.2. Epic: Загрузка и парсинг

**US-04:** Как соискатель, я хочу загрузить PDF-резюме, чтобы система могла его проанализировать.

```
Given: Авторизован, файл PDF ≤ 10 МБ
When:  POST /resumes/upload (multipart)
Then:  201 Created, текст извлечён (PyMuPDF), структура через LLM
```

**US-05:** Как соискатель, я хочу загрузить DOCX-резюме.

```
Given: Авторизован, файл DOCX ≤ 10 МБ
When:  POST /resumes/upload (multipart)
Then:  201 Created, текст извлечён (python-docx), структура через LLM
```

**US-06:** Как соискатель, я хочу видеть структурированные данные из резюме.

```
Given: Резюме загружено и обработано
When:  GET /resumes/{id}
Then:  200 OK, parsed_data: {full_name, experience[], skills[], education[]}
```

### 5.3. Epic: Вакансии

**US-07:** Как соискатель, я хочу найти вакансию через hh.ru.

```
Given: Авторизован
When:  GET /vacancies/search?text=маркетолог&area=1
Then:  200 OK, список вакансий с hh.ru API
```

**US-08:** Как соискатель, я хочу импортировать вакансию по ссылке hh.ru.

```
Given: URL вида hh.ru/vacancy/12345678
When:  POST /vacancies/from-url {url}
Then:  201 Created, вакансия с описанием и навыками
```

**US-09:** Как соискатель, я хочу ввести вакансию вручную.

```
Given: Вакансия не с hh.ru
When:  POST /vacancies/manual {title, description, skills}
Then:  201 Created
```

### 5.4. Epic: AI-оптимизация

**US-10:** Как соискатель, я хочу оптимизировать резюме под вакансию.

```
Given: Есть resume_id и vacancy_id
When:  POST /rewrite {resume_id, vacancy_id, model: "gigachat-pro"}
Then:  202 Accepted {task_id}, Celery задача запущена
```

**US-11:** Как соискатель, я хочу видеть прогресс оптимизации.

```
Given: Задача запущена
When:  GET /rewrite/{task_id}/status (polling, 2 сек)
Then:  {status, step: 1-8, progress: 0-100%}
```

**US-12:** Как соискатель, я хочу видеть результат: Match Score, diff, ключевые слова.

```
Given: Задача завершена
When:  GET /rewrite/{task_id}/result
Then:  {match_score_before, match_score_after, ats_rating, diff, keywords_added}
```

**US-13:** Как free-пользователь, я хочу получить ошибку при превышении лимита.

```
Given: Использовано 5 из 5 оптимизаций
When:  POST /rewrite
Then:  429, {error: "Лимит исчерпан", upgrade_url: "/subscription/upgrade"}
```

### 5.5. Epic: Экспорт

**US-14:** Как соискатель, я хочу скачать оптимизированное резюме в DOCX.

```
Given: Оптимизация завершена
When:  GET /export/{id}/docx
Then:  200 OK, binary DOCX file
```

---

## 6. Архитектура MVP

### 6.1. Компоненты

```
┌──────────────┐     ┌──────────────┐
│  React SPA   │────→│   FastAPI    │
│  (nginx)     │     │   (async)    │
│  :3000       │     │   :8000      │
└──────────────┘     └──────┬───────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
        ┌─────┴──┐   ┌─────┴──┐   ┌─────┴──────┐
        │Postgres│   │ Redis  │   │   Celery   │
        │  16 +  │   │  7.x   │   │   Worker   │
        │pgvector│   │        │   │            │
        └────────┘   └────────┘   └──────┬─────┘
                                         │
                                   ┌─────┴─────┐
                                   │ RabbitMQ  │
                                   │  3.13+    │
                                   └─────┬─────┘
                                         │
                                   ┌─────┴─────┐
                                   │ LLM APIs  │
                                   │ GigaChat  │
                                   │ Anthropic │
                                   │ OpenRouter│
                                   │ OpenAI    │
                                   └───────────┘
```

### 6.2. Принципы

1. **Монолит** — один репозиторий, один деплой, доменная организация (auth/, resumes/, vacancies/, rewriter/, ml/)
2. **API-first** — React SPA вызывает REST API через nginx-прокси (/api/ → FastAPI)
3. **Async everywhere** — FastAPI + asyncpg + httpx (async hh.ru клиент)
4. **Celery для long-running** — LLM-задачи 8–30 сек → фоновая обработка
5. **Single DB** — PostgreSQL для реляционных данных + JSONB + pgvector

### 6.3. Потоки данных

**Upload flow:**
```
React → POST /api/v1/resumes/upload (multipart)
FastAPI → validate → save to /data/uploads → PyMuPDF/python-docx → LLM structurize → embedding → save to DB
React ← 201 {id, title, status}
```

**Rewrite flow:**
```
React → POST /api/v1/rewrite {resume_id, vacancy_id, model}
FastAPI → check limits → create Celery task → 202 {task_id}
Celery → упрощённый pipeline: rewrite (LLM с retry до 3) → score → complete
  → Phase 2: полный 8-шаговый pipeline (extract → gap → strategy → rewrite → validate → score → diff → complete)
  → Save to rewrite_history
React → GET /api/v1/rewrite/{task_id}/status (polling, прогресс: 0/50/100)
React → GET /api/v1/rewrite/{task_id}/result
```

---

## 7. Технический стек

### 7.1. Обоснование ключевых решений

| Технология | Альтернативы | Причина выбора |
|-----------|-------------|----------------|
| **FastAPI** | Flask, Django REST | Async I/O (критично для LLM), автодокументация, Pydantic |
| **PostgreSQL + pgvector** | MongoDB, Qdrant | Единая БД для реляционных и векторных данных |
| **Celery + RabbitMQ + Redis** | BackgroundTasks, Dramatiq | Battle-tested, RabbitMQ — брокер, Redis — result backend |
| **GigaChat** | YandexGPT | #1 на MERA для русского, OpenAI-compatible SDK |
| **Anthropic Claude** | — | Отличный русский, 200K контекст |
| **Local FS** | MinIO, S3 | Docker volume /data/uploads, миграция на S3 в продакшене |
| **PyMuPDF** | pdfplumber | 10x быстрее альтернатив |
| **React + Vite** | Gradio, Next.js | Production SPA, TypeScript, быстрый HMR, nginx serving |

### 7.2. Версии зависимостей

```
# Core
python = "3.11+"           # runtime: 3.13 (Docker: 3.11)
fastapi = "0.115.6"
uvicorn[standard] = "0.34.0"
pydantic = "2.10.5"
pydantic-settings = "2.7.1"

# Database
sqlalchemy[asyncio] = "2.0.37"
asyncpg = "0.30.0"
alembic = "1.14.1"
pgvector = "0.3.6"

# Task Queue
celery[redis] = "5.4.0"
redis = "5.2.1"
flower = "2.0.1"

# Auth
PyJWT = "2.10.1"
bcrypt = "4.2.1"          # прямой bcrypt (не passlib)

# Encryption
cryptography = ">=42.0"    # AES-шифрование API-ключей

# HTTP
httpx = "0.28.1"
tenacity = "9.0.0"

# Rate Limiting
slowapi = "0.1.9"

# Document Parsing & Export
PyMuPDF = "1.25.3"
python-docx = "1.1.2"
reportlab = ">=4.0"        # PDF-экспорт

# AI/ML
openai = "1.59.9"
gigachat = "0.1.40"
anthropic = ">=0.40.0"
sentence-transformers = "3.3.1"

# Logging
structlog = "24.4.0"

# Testing & Quality (dev)
pytest = "8.3.*"
pytest-asyncio = "0.24.*"
ruff = "0.9.*"
mypy = "1.14.*"

# Frontend
vite = "6.x"
react = "19.x"
react-router-dom = "6.x"
typescript = "5.x"
vitest = "3.x"
```

---

## 8. Схема данных

### 8.1. Миграция 001: Initial Schema

```sql
-- Расширения
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Типы (в коде используется String + native_enum=False для portability)
CREATE TYPE user_plan AS ENUM ('free', 'standard', 'pro');
CREATE TYPE resume_status AS ENUM ('draft', 'processing', 'optimized', 'error');
CREATE TYPE rewrite_status AS ENUM ('pending', 'processing', 'completed', 'failed');

-- Пользователи
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    plan user_plan DEFAULT 'free' NOT NULL,
    optimizations_used INTEGER DEFAULT 0 NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE NOT NULL,     -- email-верификация (migration 003)
    avatar_url VARCHAR(500),                        -- путь к аватару (migration 005)
    deleted_at TIMESTAMPTZ,                         -- soft-delete (migration 004)
    scheduled_deletion TIMESTAMPTZ,                 -- дата окончательного удаления (migration 004)
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Резюме
CREATE TABLE resumes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    file_path VARCHAR(500) NOT NULL,
    file_format VARCHAR(10) NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    raw_text TEXT,
    parsed_data JSONB,
    embedding VECTOR(1536),
    status resume_status DEFAULT 'draft' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Вакансии
CREATE TABLE vacancies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    hh_id VARCHAR(20),
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255),
    description TEXT NOT NULL,
    requirements JSONB,
    key_skills JSONB,
    salary_from INTEGER,
    salary_to INTEGER,
    experience VARCHAR(50),
    city VARCHAR(100),
    source_url VARCHAR(500),
    embedding VECTOR(1536),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- История оптимизаций
CREATE TABLE rewrite_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    resume_id UUID NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
    vacancy_id UUID NOT NULL REFERENCES vacancies(id) ON DELETE CASCADE,
    original_text TEXT NOT NULL,
    rewritten_text TEXT,
    rewritten_data JSONB,
    model_name VARCHAR(50) NOT NULL,
    status rewrite_status DEFAULT 'pending' NOT NULL,
    match_score_before FLOAT,
    match_score_after FLOAT,
    ats_rating VARCHAR(2),
    keywords_added JSONB,
    tokens_used INTEGER,
    processing_time_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Пользовательские настройки (migration 005)
CREATE TABLE user_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL,       -- 'ai_keys', 'ai_toggles', 'ai_model'
    key VARCHAR(100) NOT NULL,           -- 'openai', 'anthropic', 'default_model' и т.д.
    value TEXT NOT NULL DEFAULT '',       -- значение (AES-зашифровано если is_encrypted)
    is_encrypted BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    UNIQUE(user_id, category, key)
);

-- Индексы
CREATE INDEX idx_resumes_user_id ON resumes(user_id);
CREATE INDEX idx_resumes_status ON resumes(status);
CREATE INDEX idx_vacancies_user_id ON vacancies(user_id);
CREATE INDEX idx_rewrite_history_user_id ON rewrite_history(user_id);
CREATE INDEX idx_rewrite_history_resume_id ON rewrite_history(resume_id);
CREATE INDEX idx_rewrite_history_created_at ON rewrite_history(created_at DESC);

-- HNSW-индексы для векторного поиска
CREATE INDEX idx_resumes_embedding ON resumes
    USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_vacancies_embedding ON vacancies
    USING hnsw (embedding vector_cosine_ops);
```

> **Примечание (Phase 1):**
> - Колонка `embedding VECTOR(1536)` добавляется через Alembic-миграцию, но **не включена в ORM-модели** SQLAlchemy (требуется pgvector + расширение).
> - Эмбеддинги генерируются моделью `all-MiniLM-L6-v2` (384 dims), паддинг до 1536 нулями — для совместимости с будущей миграцией на OpenAI `text-embedding-3-small` (1536 dims) в Phase 2.
> - В Phase 1 эмбеддинги сохраняются как метаданные в `parsed_data` (JSONB); миграция на VECTOR-колонку — Phase 2.
> - ATS-рейтинг: шкала `A+, A, B+, B, C, D` (без `F` — минимум `D`).

### 8.2. Ключевые Pydantic-модели

```python
# src/app/resumes/schemas.py
class ResumeUploadResponse(BaseModel):
    id: UUID
    title: str | None
    file_format: str
    file_size_bytes: int
    status: str
    created_at: datetime

class ParsedResume(BaseModel):
    full_name: str | None = None
    position: str | None = None
    summary: str | None = None
    experience: list[dict] = Field(default_factory=list)
    education: list[dict] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    contacts: dict = Field(default_factory=dict)

# src/app/rewriter/schemas.py
class RewriteRequest(BaseModel):
    resume_id: UUID
    vacancy_id: UUID
    model: str = "gigachat-pro"

class RewriteResult(BaseModel):
    id: UUID
    original_text: str
    rewritten_text: str
    match_score_before: float
    match_score_after: float
    ats_rating: str
    keywords_added: list[str]
    model_name: str
    processing_time_ms: int
```

---

## 9. API-спецификация

### 9.1. Полный список эндпоинтов (40+)

```
BASE_URL: /api/v1

Auth:
  POST   /auth/register          → 201 Created (rate limit 3/min)
  GET    /auth/verify/{token}    → 200 OK (email-верификация)
  POST   /auth/login             → 200 OK (rate limit 5/min)
  POST   /auth/refresh           → 200 OK
  POST   /auth/logout            → 204 No Content
  GET    /auth/me                → 200 OK (профиль текущего пользователя)
  PUT    /auth/me                → 200 OK (обновление профиля)
  PUT    /auth/me/password       → 200 OK (смена пароля)
  DELETE /auth/me                → 204 No Content (soft-delete, 30 дней, ФЗ-152)
  POST   /auth/me/restore       → 200 OK (восстановление аккаунта)
  POST   /auth/me/avatar        → 200 OK (загрузка аватара)
  DELETE /auth/me/avatar        → 200 OK (удаление аватара)

Resumes:
  POST   /resumes/upload         → 201 Created (PDF/DOCX, multipart)
  POST   /resumes/from-text      → 201 Created (текст → резюме)
  GET    /resumes                → 200 OK (list, пагинация)
  GET    /resumes/{id}           → 200 OK (включая parsed_data)
  PUT    /resumes/{id}           → 200 OK (обновление метаданных)
  DELETE /resumes/{id}           → 204 No Content (soft-delete)
  POST   /resumes/{id}/restore   → 200 OK (восстановление)
  GET    /resumes/{id}/file      → 200 OK (скачивание оригинала)
  GET    /resumes/{id}/preview   → 200 OK (данные для просмотрщика)

Vacancies:
  GET    /vacancies/search       → 200 OK (list from hh.ru)
  GET    /vacancies/hh/{hh_id}   → 200 OK (полные данные вакансии hh.ru)
  POST   /vacancies/from-url     → 201 Created
  POST   /vacancies/manual       → 201 Created
  GET    /vacancies/{id}         → 200 OK
  DELETE /vacancies/{id}         → 204 No Content

Rewrite:
  POST   /rewrite                → 202 Accepted (task_id, rate limit 10/час)
  GET    /rewrite/{task_id}/status → 200 OK
  GET    /rewrite/{task_id}/result → 200 OK
  GET    /rewrite/history        → 200 OK (список оптимизаций)

Export:
  GET    /export/{id}/docx       → 200 OK (binary DOCX)
  GET    /export/{id}/pdf        → 200 OK (binary PDF)
  GET    /export/{id}/txt        → 200 OK (plain text)

Models:
  GET    /models                 → 200 OK (список провайдеров + доступность)
  GET    /models/{provider}/sub-models → 200 OK (подмодели)

Settings:
  GET    /settings/ai-keys       → 200 OK (маскированные ключи)
  PUT    /settings/ai-keys/{provider} → 200 OK (сохранить ключ)
  DELETE /settings/ai-keys/{provider} → 204 No Content
  GET    /settings/ai-toggles    → 200 OK
  PUT    /settings/ai-toggles    → 200 OK
  GET    /settings/ai-model      → 200 OK
  PUT    /settings/ai-model      → 200 OK

Health:
  GET    /health                 → 200 OK
  MOUNT  /api/v1/uploads/        → StaticFiles (аватары, загрузки)
```

### 9.2. Примеры запросов

**Регистрация:**
```http
POST /api/v1/auth/register
Content-Type: application/json

{"email": "anna@example.com", "password": "SecurePass123"}

→ 201 Created
{"access_token": "eyJ...", "refresh_token": "eyJ...", "token_type": "bearer"}
```

**Запуск оптимизации:**
```http
POST /api/v1/rewrite
Authorization: Bearer eyJ...

{"resume_id": "550e8400-...", "vacancy_id": "660e8400-...", "model": "gigachat-pro"}

→ 202 Accepted
{"task_id": "celery-task-abc123"}
```

**Статус:**
```http
GET /api/v1/rewrite/celery-task-abc123/status

→ 200 OK
{"task_id": "celery-task-abc123", "status": "processing", "step": 3, "progress": 72.5}
```

---

## 10. AI/ML Pipeline

### 10.1. Системный промпт

```python
REWRITE_SYSTEM_PROMPT = """Вы — эксперт по оптимизации резюме для российского
рынка труда с 15-летним опытом в рекрутинге и HR.

Задача — переработать резюме так, чтобы:
1. Максимально соответствовать требованиям целевой вакансии
2. Успешно проходить ATS-фильтры
3. Привлекать внимание рекрутера в первые 7 секунд

ПРАВИЛА:
- НЕ выдумывайте факты и достижения
- Используйте формулу: Действие + Результат + Метрика
- Добавьте ключевые слова из вакансии (если навык подтверждается)
- Сохраните русский язык
- Оптимальная длина: 1–2 страницы A4

ФОРМАТ ОТВЕТА — JSON:
- summary: профессиональное саммари (2–4 предложения)
- experience: [{position, company, period, achievements: [str]}]
- education: [{institution, degree, specialization, year}]
- skills: [str]
- keywords_added: [str]
"""
```

### 10.2. Расчёт Match Score

```python
def calculate_match_score(
    resume_text: str,
    vacancy_text: str,
) -> MatchScoreResult:
    """Match Score (0–100). Компоненты совпадают с UI (12-results.html):
    - Ключевые слова — 40%  (TF-IDF пересечение токенов)
    - Опыт и релевантность — 25%  (token-based cosine similarity)
    - Структура документа — 20%  (наличие секций, длина, формат)
    - Читаемость — 15%  (метрики, формулировки, конкретика)

    Примечание: experience_score реализован как token-based cosine
    similarity (Counter-based), а не через pgvector embeddings.
    Миграция на embedding cosine запланирована для Phase 2.
    """
    keyword_score = len(resume_tokens & vacancy_tokens) / max(len(vacancy_tokens), 1)
    experience_score = _token_cosine_similarity(resume_text, vacancy_text)
    structure_score = evaluate_structure(resume_text)
    readability_score = evaluate_readability(resume_text)

    return round((
        keyword_score * 0.40 +
        experience_score * 0.25 +
        structure_score * 0.20 +
        readability_score * 0.15
    ) * 100, 1)
```

### 10.3. LLM-клиент (Strategy Pattern)

```python
class BaseLLMClient(ABC):
    @abstractmethod
    async def complete(self, system: str, user: str) -> str: ...

class GigaChatClient(BaseLLMClient): ...
class AnthropicClient(BaseLLMClient): ...
class OpenAIClient(BaseLLMClient): ...
class OpenRouterClient(BaseLLMClient): ...
class GroqClient(BaseLLMClient): ...

class LLMClientFactory:
    _clients = {
        "gigachat-pro": GigaChatClient,
        "gigachat-lite": GigaChatClient,
        "anthropic": AnthropicClient,
        "openrouter": OpenRouterClient,
        "openai": OpenAIClient,
        "groq": GroqClient,
    }

    FALLBACK_ORDER = ["gigachat-pro", "anthropic", "openrouter", "openai", "groq"]

    @classmethod
    def create(cls, model: str) -> BaseLLMClient:
        return cls._clients[model]()
```

---

## 11. React SPA Frontend

### 11.1. Архитектура

```
frontend/
├── Dockerfile         # node:20 build → nginx:1.27 serve
├── nginx.conf         # SPA routing + API proxy → app:8000
├── package.json       # Vite 6 + React 19 + TypeScript
├── index.html         # Entry point (lang="ru", Inter font)
└── src/
    ├── main.tsx           # BrowserRouter + AuthProvider
    ├── App.tsx            # Маршрутизация (react-router-dom v6)
    ├── contexts/
    │   └── AuthContext.tsx # JWT auth state + localStorage
    ├── services/
    │   └── api.ts         # HTTP-клиент (fetch + Bearer token)
    ├── data/
    │   └── demo.ts        # Демо-данные (резюме, вакансии, скоры)
    ├── styles/
    │   ├── shared-styles.css  # Дизайн-система из Prototype/
    │   └── app.css            # Дополнительные стили React
    ├── components/layout/
    │   ├── AppLayout.tsx      # Sidebar + main (авторизованные)
    │   ├── PublicLayout.tsx   # Navbar (публичные)
    │   └── CenteredLayout.tsx # Центрированный (auth/recovery/404)
    ├── pages/
    │   ├── LandingPage.tsx    # Лендинг (hero, features, FAQ, CTA)
    │   ├── PricingPage.tsx    # Тарифные планы
    │   ├── ErrorPage.tsx      # 404
    │   ├── auth/              # AuthPage, PasswordRecovery, EmailVerify
    │   ├── dashboard/         # DashboardPage (статистика)
    │   ├── resumes/           # ResumesPage (таблица + фильтры)
    │   ├── wizard/            # Upload→Vacancy→Models→Processing→Results→Editor→Export
    │   ├── history/           # HistoryPage (timeline)
    │   └── settings/          # SettingsLayout + 4 вкладки (Profile, AI, Subscription, Security)
    └── test/
        ├── setup.ts           # jest-dom setup
        ├── App.test.tsx       # 19 route tests
        ├── api.test.ts        # 7 API client tests
        └── demo.test.ts       # 7 demo data tests
```

### 11.2. Маршрутизация

| Путь | Layout | Компонент |
|------|--------|-----------|
| `/` | PublicLayout | LandingPage |
| `/pricing` | PublicLayout | PricingPage |
| `/auth` | CenteredLayout | AuthPage |
| `/password-recovery` | CenteredLayout | PasswordRecoveryPage |
| `/email-verify` | CenteredLayout | EmailVerifyPage |
| `/app/dashboard` | AppLayout | DashboardPage |
| `/app/resumes` | AppLayout | ResumesPage |
| `/app/upload` | AppLayout | UploadPage |
| `/app/vacancy` | AppLayout | VacancyPage |
| `/app/models` | AppLayout | ModelsPage |
| `/app/processing` | AppLayout | ProcessingPage |
| `/app/results` | AppLayout | ResultsPage |
| `/app/editor` | AppLayout | EditorPage |
| `/app/export` | AppLayout | ExportPage |
| `/app/history` | AppLayout | HistoryPage |
| `/app/settings/*` | AppLayout | SettingsLayout + 4 вкладки |
| `*` | — | ErrorPage (404) |

### 11.3. Демо-режим

Полностью функциональный UI с тестовыми данными (demo.ts):
- 5 резюме, 3 вакансии, 4 группы истории
- 5-шаговый wizard с анимацией прогресса
- Match Score circle (87%), ATS-рейтинг, diff comparison
- Экспорт (DOCX/PDF/hh.ru), настройки, безопасность

### 11.4. Seed-пользователь

При первом развёртывании (development) автоматически создаётся тестовый пользователь:
- Email: `test@example.com`
- Пароль: `TestPass123`
- Скрипт: `src/app/core/seed.py` (идемпотентный, вызывается в lifespan FastAPI)

### 11.5. Технический стек Frontend

| Технология | Версия | Назначение |
|-----------|--------|------------|
| Vite | 6.x | Сборщик (HMR, ESBuild) |
| React | 19.x | UI-библиотека |
| TypeScript | 5.x | Типизация |
| react-router-dom | 6.x | Клиентская маршрутизация |
| lucide-react | 0.576+ | Иконки |
| Vitest | 3.x | Тесты |
| nginx | 1.27 | Serving (production) |

---

## 12. Интеграция с hh.ru API

### 12.1. Используемые эндпоинты (MVP)

| Endpoint | Авторизация | Назначение |
|----------|:-----------:|------------|
| `GET /vacancies` | ❌ | Поиск вакансий |
| `GET /vacancies/{id}` | ❌ | Детали вакансии |
| `GET /dictionaries` | ❌ | Справочники |

### 12.2. Не используемые в MVP

- OAuth 2.0 авторизация соискателя (→ Phase 2)
- `GET /resumes/mine`, `PUT /resumes/{id}` (→ Phase 2)

### 12.3. Клиент

```python
class HHClient:
    BASE_URL = "https://api.hh.ru"

    def __init__(self, user_agent: str):
        self.headers = {"User-Agent": user_agent}

    async def search_vacancies(self, text: str, area: int = 1, per_page: int = 20):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/vacancies",
                params={"text": text, "area": area, "per_page": per_page},
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()["items"]
```

### 12.4. Ограничения

- **Rate limiting:** backoff с 3 retries при 429
- **Недоступность:** ручной ввод вакансии как fallback
- **User-Agent:** `ResumeCraft/2.0 (contact@resumecraft.ru)`

---

## 13. Безопасность

### 13.1. Аутентификация

```python
import bcrypt

_BCRYPT_ROUNDS = 12

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_access_token(user_id: UUID, *, secret: str, expires_minutes: int = 30) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(tz=UTC) + timedelta(minutes=expires_minutes),
        "type": "access",
    "jti": str(uuid4()),  # резерв для будущей инвалидации токенов через blacklist
    }
    return jwt.encode(payload, secret, algorithm="HS256")
```

### 13.2. Валидация файлов

```python
ALLOWED_EXTENSIONS = {"pdf", "docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAGIC_BYTES = {"pdf": b"%PDF", "docx": b"PK\x03\x04"}

def validate_upload(file: UploadFile) -> None:
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"Unsupported format: {ext}")
    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise ValidationError("File too large")
    if not content.startswith(MAGIC_BYTES.get(ext, b"")):
        raise ValidationError("Content does not match extension")
    file.file.seek(0)
```

### 13.3. Защита API

- **CORS:** ограничение `allowed_origins`, `allow_methods` (GET/POST/PUT/DELETE/OPTIONS/PATCH), `allow_headers` (Authorization/Content-Type/Accept/X-Request-ID)
- **Rate Limiting:** SlowAPI уже используется: register 3/min, login 5/min, rewrite 10/hour
- **Input Validation:** Pydantic-схемы на всех эндпоинтах
- **Secrets:** .env + .gitignore
- **AI Security:** санитизация пользовательского ввода перед отправкой в LLM (`sanitize_for_llm`)

---

## 14. Тестирование

### 14.1. Текущие метрики

| Метрика | Значение |
|---------|----------|
| **Backend тестов (unit + acceptance + coverage)** | 578 (pytest + pytest-asyncio) |
| **Backend тестов (acceptance)** | 52 (приёмочные, BASE_URL) |
| **Backend тестов (integration)** | 23 (реальные LLM API: 5 провайдеров) |
| **Backend тестов (E2E)** | 38 (Playwright) |
| **Backend тестов всего** | **691** |
| **Frontend тестов** | **525** (Vitest + @testing-library/react) |
| **Всего тестов** | **1216** |
| **Backend покрытие** | 100% (pytest-cov) |
| **Фреймворки** | pytest, Vitest |
| **БД в тестах** | SQLite (aiosqlite, in-memory) |
| **Ruff warnings** | 0 |
| **mypy errors** | 0 (strict mode) |

### 14.2. Стратегия

```
┌─────────────────────────────────────┐
│      Frontend Tests (Vitest)        │  ← 525 tests (43%)
├─────────────────────────────────────┤
│      Backend Unit + Acceptance      │  ← 578 tests (48%)
├─────────────────────────────────────┤
│   Integration + E2E (LLM + Browser) │  ← 113 tests (9%)
└─────────────────────────────────────┘
```

### 14.3. Распределение тестов по модулям

| Модуль | Тестов | Покрытие |
|--------|--------|----------|
| `test_auth/` | 64 | auth/models, schemas, router, service, avatar, soft-delete — 100% |
| `test_resumes/` | 65 | upload, from-text, CRUD, парсинг, soft-delete, preview, file — 100% |
| `test_vacancies/` | 55 | hh.ru клиент, from-url, manual, CRUD, retry, таймауты — 100% |
| `test_rewriter/` | 40 | Celery tasks, pipeline, статусы, LLM retry, history — 100% |
| `test_export/` | 38 | DOCX, PDF, TXT генерация (структурированные + plain) — 100% |
| `test_ml/` | 96 | LLM-клиенты (5 провайдеров), фабрика, роутер моделей, парсер, скоринг, эмбеддинги, санитизация, o-series — 100% |
| `test_core/` | 81 | config, security, database, storage, exceptions, deps, encryption, limiter, seed — 100% |
| `test_main*` | 7 | middleware, error handlers, lifespan, StaticFiles — 100% |
| `test_coverage_gaps` | 22 | edge-cases: embedding fallback, scoring, export |
| `test_coverage_100` | 40 | 100% покрытие: AnthropicClient, error paths, create_from_text, execute_rewrite, celery |
| `test_acceptance` | 52 | приёмочные: полные пользовательские сценарии |
| `test_v17_fixes` | 50 | v1.7 правки: верификация, шифрование, экспорт, soft-delete |
| `test_qa_fixes` | 19 | QA дефекты: email enum, LLM messages, tariff, sanitize |
| `test_integration_llm` | 23 | реальные вызовы 4 LLM-провайдеров |
| `test_e2e_browser` | 38 | Playwright browser-тесты |

### 14.4. Ключевые тесты

```python
class TestMatchScore:
    def test_perfect_match(self):
        score = calculate_match_score(perfect_resume, perfect_vacancy)
        assert score >= 90

    def test_no_match(self):
        score = calculate_match_score(irrelevant_resume, vacancy)
        assert score < 30

class TestAuthAPI:
    async def test_register_success(self, client):
        response = await client.post("/api/v1/auth/register",
            json={"email": "test@example.com", "password": "SecurePass123"})
        assert response.status_code == 201
        assert "access_token" in response.json()

    async def test_register_duplicate(self, client):
        # Повторная регистрация
        response = await client.post("/api/v1/auth/register",
            json={"email": "dup@example.com", "password": "Pass123"})
        assert response.status_code == 409
```

### 14.5. CI Pipeline

```yaml
stages: [lint, test, build]

lint:
  script:
    - ruff check src/ tests/
    - mypy src/ --strict

test:
  services: [postgres:16, redis:7-alpine, rabbitmq:3.13-management]
  script:
    - pytest --cov=src --cov-fail-under=70
```

---

## 15. Инфраструктура и деплой

### 15.1. Docker Compose (MVP)

```yaml
version: '3.9'
services:
  app:
    build: .
    ports: ["8000:8000"]
    env_file: .env
    depends_on:
      db: {condition: service_healthy}
      redis: {condition: service_healthy}
      rabbitmq: {condition: service_healthy}
    volumes: [uploads:/data/uploads]
    command: uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s

  celery-worker:
    build: .
    env_file: .env
    depends_on: [db, redis, rabbitmq]
    volumes: [uploads:/data/uploads]
    command: celery -A src.app.core.celery_app worker -l info -c 2

  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: resumecraft
      POSTGRES_PASSWORD: devpassword
      POSTGRES_DB: resumecraft
    ports: ["5432:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U resumecraft"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]

  rabbitmq:
    image: rabbitmq:3.13-management
    ports: ["5672:5672", "15672:15672"]
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "-q", "ping"]

  flower:
    build: .
    env_file: .env
    depends_on: [redis, rabbitmq]
    command: celery -A src.app.core.celery_app flower --port=5555
    ports: ["5555:5555"]

  frontend:
    build: ./frontend
    depends_on:
      app: {condition: service_healthy}
    ports: ["3000:80"]
    restart: unless-stopped

volumes:
  pgdata:
  uploads:
```

### 15.2. Локальный деплой (Docker Compose)

```
Docker Desktop → docker compose up -d
→ FastAPI :8000     → React SPA :3000
→ PostgreSQL :5432  → Redis :6379
→ RabbitMQ :5672    → Flower :5555
→ Local FS (Docker volume /data/uploads)
```

---

## 16. Критерии приёмки

### 16.1. Функциональные

| № | Критерий | Приоритет |
|---|---------|-----------|
| 1 | Регистрация + вход (JWT) | Must |
| 2 | Загрузка PDF ≤ 10 МБ | Must |
| 3 | Загрузка DOCX ≤ 10 МБ | Must |
| 4 | Извлечение текста (PyMuPDF / python-docx) | Must |
| 5 | LLM-структуризация → JSON | Must |
| 6 | Поиск вакансий через hh.ru API | Must |
| 7 | Импорт вакансии по URL | Must |
| 8 | Ручной ввод вакансии | Must |
| 9 | AI-оптимизация (GigaChat Pro) | Must |
| 10 | AI-оптимизация (Anthropic Claude) | Must |
| 11 | Match Score (до и после) | Must |
| 12 | ATS-рейтинг (A+–F) | Should |
| 13 | Diff (список изменений) | Must |
| 14 | Экспорт DOCX | Must |
| 15 | React SPA (полный workflow) | Must |
| 16 | Docker Compose (одна команда) | Must |

### 16.2. Качественные

| Критерий | Порог | Факт |
|---------|-------|------|
| Test coverage | ≥ 70% | **100%** ✅ |
| Ruff warnings | 0 | **0** ✅ |
| mypy errors | 0 | **0** ✅ |
| Тестов всего | — | **1216** (691 backend + 525 frontend) ✅ |

---

## 17. Управление рисками

| Риск | Вероятность | Влияние | Митигация |
|------|-----------|---------|-----------|
| GigaChat API недоступен | Средняя | Высокое | Fallback на Anthropic → OpenRouter → OpenAI → Groq |
| Anthropic rate limit исчерпан | Средняя | Среднее | При исчерпании → OpenRouter → OpenAI → Groq |
| hh.ru API блокирует | Низкая | Среднее | User-Agent + ручной ввод как fallback |
| LLM-ответы нестабильны | Средняя | Высокое | Pydantic-валидация + retry (до 3) |
| Не хватает времени | Средняя | Высокое | Приоритизация Must-требований |
| Docker Hub заблокирован | Высокая | Среднее | Зеркала: mirror.gcr.io, Yandex CR |

**Escalation при критических блокерах:**
- LLM полностью недоступен → Ollama (локально)
- PostgreSQL не работает → SQLite + FAISS (деградация)
- Не хватает времени → сократить до Upload + Manual Vacancy + Rewrite + Text Output

---

## 18. Границы MVP

### 18.1. В объёме (In Scope)

| Компонент | Объём |
|-----------|-------|
| Аутентификация | Email + пароль, JWT, email-верификация, soft-delete/restore, аватар |
| Резюме | PDF/DOCX/текст, парсинг, LLM-структуризация, soft-delete/restore, preview |
| Вакансии | hh.ru (анонимный), URL-импорт, ручной ввод, полные данные вакансии |
| AI-оптимизация | GigaChat Pro + Anthropic Claude + OpenRouter + OpenAI (5 провайдеров), Match Score, ATS |
| Экспорт | DOCX + PDF + TXT (3 формата) |
| Настройки | Зашифрованные API-ключи (AES), AI toggles, выбор модели/подмодели |
| Модели | Список провайдеров, динамические подмодели через API |
| UI | React SPA (22 страницы, 23+ маршрутов, модульная архитектура) |
| Инфраструктура | Docker Compose (7 сервисов), PostgreSQL + pgvector, Redis, RabbitMQ, Local FS |
| Тестирование | Unit + Integration + E2E + Frontend, **1216 тестов**, 100% backend coverage |

### 18.2. Вне объёма (Out of Scope → Future)

| Компонент | Фаза |
|-----------|------|
| OAuth hh.ru (соискатель) | Phase 2 |
| ЮKassa / платёжная система | Phase 2 |
| 2FA (TOTP) | Phase 2 |
| WYSIWYG-редактор | Phase 2 |
| Шаблоны экспорта (Professional, Creative) | Phase 2 |
| Telegram-бот | Phase 3 |
| Mobile app | Phase 3 |
| B2B API | Phase 3 |

---

*ResumeCraft MVP — минимальный функциональный продукт, покрывающий базовый pipeline AI-оптимизации резюме для российского рынка труда.*

# ResumeCraft — Baseline MVP

> **Версия:** 1.1  
> **Дата:** Февраль 2026  
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
11. [Streamlit Demo UI](#11-streamlit-demo-ui)
12. [Интеграция с hh.ru API](#12-интеграция-с-hhru-api)
13. [Безопасность](#13-безопасность)
14. [Тестирование](#14-тестирование)
15. [Инфраструктура и деплой](#15-инфраструктура-и-деплой)
16. [Критерии приёмки](#16-критерии-приёмки)
17. [Ресурсы и сроки](#17-ресурсы-и-сроки)
18. [Управление рисками](#18-управление-рисками)
19. [Границы MVP](#19-границы-mvp)

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
2. **API-first** — backend API не зависит от UI; Streamlit → React без переписывания backend
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
- React SPA (→ Phase 2, используем Streamlit)
- OAuth hh.ru для соискателей (→ Phase 2, используем анонимный API)
- ЮKassa платежи (→ Phase 2)
- PDF export с шаблонами (→ Phase 2, только DOCX)
- 2FA (→ Phase 2)
- Email verification (→ Phase 2)
- Интерактивный редактор (→ Phase 2)
- GPT-4o (→ Phase 2, только GigaChat Pro + Llama 3)

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
| RW-02 | Must | Оптимизация через Llama 3 (Groq) |
| RW-03 | Must | 8-шаговый pipeline (Extract → Complete) |
| RW-04 | Must | Match Score (до и после, 0–100) |
| RW-05 | Must | ATS-рейтинг (A+ – F) |
| RW-06 | Must | Diff: список изменений и ключевых слов |
| RW-07 | Must | Celery task с прогрессом (polling) |
| RW-08 | Must | Сохранение в rewrite_history |
| RW-09 | Must | Проверка лимитов тарифа |
| RW-10 | Should | Fallback GigaChat → Groq → OpenAI |
| RW-11 | Should | Pydantic-валидация LLM-ответа + retry (до 3) |

### 3.5. Export — Экспорт

| ID | Приоритет | Требование |
|----|-----------|-----------|
| EXP-01 | Must | Экспорт в DOCX (python-docx) |
| EXP-02 | Should | Экспорт в PDF (LibreOffice headless) |
| EXP-03 | Could | Шаблон «Minimal» |

---

## 4. Нефункциональные требования

### 4.1. Производительность

| Метрика | Требование |
|---------|-----------|
| API response (CRUD) | < 200 мс (p95) |
| Resume upload + parsing | < 10 сек |
| AI-оптимизация (Llama 3) | < 15 сек |
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
| Тестов | — | **352** |

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
│  Streamlit   │────→│   FastAPI    │
│  Demo UI     │     │   (async)    │
│  :8501       │     │   :8000      │
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
                                   │ Groq      │
                                   └───────────┘
```

### 6.2. Принципы

1. **Монолит** — один репозиторий, один деплой, доменная организация (auth/, resumes/, vacancies/, rewriter/, ml/)
2. **API-first** — Streamlit вызывает те же эндпоинты, что будущий React SPA
3. **Async everywhere** — FastAPI + asyncpg + httpx (async hh.ru клиент)
4. **Celery для long-running** — LLM-задачи 8–30 сек → фоновая обработка
5. **Single DB** — PostgreSQL для реляционных данных + JSONB + pgvector

### 6.3. Потоки данных

**Upload flow:**
```
Streamlit → POST /resumes/upload (multipart)
FastAPI → validate → save to /data/uploads → PyMuPDF/python-docx → LLM structurize → embedding → save to DB
Streamlit ← 201 {id, title, status}
```

**Rewrite flow:**
```
Streamlit → POST /rewrite {resume_id, vacancy_id, model}
FastAPI → check limits → create Celery task → 202 {task_id}
Celery → упрощённый pipeline: rewrite (LLM с retry до 3) → score → complete
  → Phase 2: полный 8-шаговый pipeline (extract → gap → strategy → rewrite → validate → score → diff → complete)
  → Save to rewrite_history
Streamlit → GET /rewrite/{task_id}/status (polling, прогресс: 0/50/100)
Streamlit → GET /rewrite/{task_id}/result
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
| **Llama 3 (Groq)** | Ollama | 14 400 бесплатных req/день |
| **Local FS** | MinIO, S3 | Docker volume /data/uploads, миграция на S3 в продакшене |
| **PyMuPDF** | pdfplumber | 10x быстрее альтернатив |
| **Streamlit** | Gradio, Flask | Минимум кода для функционального UI |

### 7.2. Версии зависимостей

```
# Core
python = "3.11"
fastapi = "0.115.*"
uvicorn = {extras = ["standard"], version = "0.30.*"}
pydantic = "2.9.*"

# Database
sqlalchemy = {extras = ["asyncio"], version = "2.0.*"}
asyncpg = "0.29.*"
alembic = "1.13.*"
pgvector = "0.3.*"

# Task Queue
celery = {extras = ["redis"], version = "5.4.*"}
redis = "5.1.*"

# Auth
pyjwt = "2.9.*"
passlib = {extras = ["bcrypt"], version = "1.7.*"}

# HTTP
httpx = "0.27.*"

# Document Parsing
pymupdf = "1.24.*"
python-docx = "1.1.*"

# AI/ML
openai = "1.40.*"
gigachat = "0.1.*"
sentence-transformers = "3.0.*"

# Demo UI
streamlit = "1.38.*"

# Testing & Quality
pytest = "8.3.*"
pytest-asyncio = "0.23.*"
ruff = "0.6.*"
mypy = "1.11.*"
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

### 9.1. Полный список эндпоинтов

```
BASE_URL: /api/v1

Auth:
  POST   /auth/register          → 201 Created
  POST   /auth/login             → 200 OK
  POST   /auth/refresh           → 200 OK
  POST   /auth/logout            → 204 No Content
  GET    /auth/me                → 200 OK (профиль текущего пользователя)
  PUT    /auth/me                → 200 OK (обновление профиля)
  PUT    /auth/me/password       → 200 OK (смена пароля)
  DELETE /auth/me                → 204 No Content (удаление аккаунта, ФЗ-152)

Resumes:
  POST   /resumes/upload         → 201 Created
  GET    /resumes                → 200 OK (list)
  GET    /resumes/{id}           → 200 OK
  PUT    /resumes/{id}           → 200 OK (обновление метаданных)
  DELETE /resumes/{id}           → 204 No Content

Vacancies:
  GET    /vacancies/search       → 200 OK (list from hh.ru)
  POST   /vacancies/from-url     → 201 Created
  POST   /vacancies/manual       → 201 Created
  GET    /vacancies/{id}         → 200 OK
  DELETE /vacancies/{id}         → 204 No Content

Rewrite:
  POST   /rewrite                → 202 Accepted (task_id)
  GET    /rewrite/{task_id}/status → 200 OK
  GET    /rewrite/{task_id}/result → 200 OK
  GET    /rewrite/history        → 200 OK (список оптимизаций пользователя)

Export:
  GET    /export/{id}/docx       → 200 OK (binary)

Health:
  GET    /health                 → 200 OK
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
class GroqClient(BaseLLMClient): ...

class LLMClientFactory:
    _clients = {
        "gigachat-pro": GigaChatClient,
        "llama-3": GroqClient,
    }

    @classmethod
    def create(cls, model: str) -> BaseLLMClient:
        return cls._clients[model]()
```

---

## 11. Streamlit Demo UI

### 11.1. Экраны

```
Page 1: 🏠 Главная — описание проекта
Page 2: 📄 Загрузка — file uploader (PDF/DOCX)
Page 3: 🎯 Вакансия — поиск hh.ru / URL / ручной ввод
Page 4: 🤖 Оптимизация — выбор модели, прогресс, результат
Page 5: 📥 Экспорт — download DOCX
```

### 11.2. Преимущества для MVP

- Полный UI за 1–2 дня (vs. 2–4 недели React)
- Python-only, без JS
- API-first: те же эндпоинты, что будущий React SPA

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
        "jti": str(uuid4()),  # уникальный ID токена для инвалидации
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
- **Rate Limiting:** запланирован для Phase 2 (Redis, 10 req/сек на пользователя, 5 попыток/мин на login)
- **Input Validation:** Pydantic-схемы на всех эндпоинтах
- **Secrets:** .env + .gitignore
- **AI Security:** санитизация пользовательского ввода перед отправкой в LLM (`sanitize_for_llm`)

---

## 14. Тестирование

### 14.1. Текущие метрики

| Метрика | Значение |
|---------|----------|
| **Всего тестов** | 353 |
| **Покрытие кода** | 100% (1473 statements, 0 uncovered) |
| **Фреймворк** | pytest + pytest-asyncio |
| **БД в тестах** | SQLite (aiosqlite, in-memory) |
| **Ruff warnings** | 0 |
| **mypy errors** | 0 (strict mode) |

### 14.2. Стратегия

```
┌─────────────────────────────────────┐
│         E2E Tests (Streamlit)       │  ← 5% (ручные)
├─────────────────────────────────────┤
│       Integration Tests (API)       │  ← 25%
├─────────────────────────────────────┤
│          Unit Tests (Logic)         │  ← 70%
└─────────────────────────────────────┘
```

### 14.3. Распределение тестов по модулям

| Модуль | Тестов | Покрытие |
|--------|--------|----------|
| `test_auth/` | 55 | auth/models, schemas, router, service — 100% |
| `test_resumes/` | 39 | upload, CRUD, парсинг, эмбеддинги — 100% |
| `test_vacancies/` | 42 | hh.ru клиент, CRUD, retry, таймауты, HTTP-ошибки — 100% |
| `test_rewriter/` | 40 | Celery tasks, pipeline, статусы, LLM retry, raw_text=None — 100% |
| `test_export/` | 11 | DOCX-генерация — 100% |
| `test_ml/` | 62 | LLM-клиенты, фабрика, скоринг — 100% |
| `test_core/` | 74 | config, security, database, storage, exceptions, deps — 100% |
| `test_main*` | 7 | middleware, error handlers, lifespan — 100% |
| `test_coverage_gaps` | 22 | edge-cases: embedding fallback, scoring, export |
| `test_health` | 1 | GET /health — 100% |

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

  streamlit:
    build: .
    env_file: .env
    depends_on: [app]
    command: streamlit run streamlit_app/app.py --server.port=8501
    ports: ["8501:8501"]

volumes:
  pgdata:
  uploads:
```

### 15.2. Деплой для защиты

```
Docker Desktop → docker compose up -d
→ FastAPI :8000     → Streamlit :8501
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
| 10 | AI-оптимизация (Llama 3 / Groq) | Must |
| 11 | Match Score (до и после) | Must |
| 12 | ATS-рейтинг (A+–F) | Should |
| 13 | Diff (список изменений) | Must |
| 14 | Экспорт DOCX | Must |
| 15 | Streamlit demo (полный workflow) | Must |
| 16 | Docker Compose (одна команда) | Must |

### 16.2. Качественные

| Критерий | Порог | Факт |
|---------|-------|------|
| Test coverage | ≥ 70% | **100%** ✅ |
| Ruff warnings | 0 | **0** ✅ |
| mypy errors | 0 | **0** ✅ |
| Тестов всего | — | **352** |
| API response (CRUD) | < 200 мс | — |
| Оптимизация (Llama 3) | < 15 сек | — |
| Match Score improvement | +20%+ для 80% тестов | — |

---

## 17. Ресурсы и сроки

### 17.1. Timeline

```
Неделя 1–2: Фундамент
  Auth, Database, Migrations, Docker, Local FS

Неделя 3–4: Core Pipeline
  Resume upload + parsing, Vacancy module, Embeddings

Неделя 5–6: AI Rewriting
  Celery pipeline, GigaChat + Groq, Match Score, ATS, Diff

Неделя 7: Export + Streamlit
  DOCX export, Streamlit UI, E2E testing

Неделя 8: Polish
  Bug fixes, coverage 70%+, docs, demo preparation
```

### 17.2. Зависимости

| Зависимость | Срок |
|-------------|------|
| GigaChat API ключ (developers.sber.ru) | Неделя 1 |
| Groq API ключ (console.groq.com) | Неделя 1 |
| hh.ru App регистрация (dev.hh.ru) | Неделя 1 |
| Тестовые резюме (10+) | Неделя 3 |

---

## 18. Управление рисками

| Риск | Вероятность | Влияние | Митигация |
|------|-----------|---------|-----------|
| GigaChat API недоступен | Средняя | Высокое | Fallback на Llama 3 (Groq) |
| Groq rate limit исчерпан | Средняя | Среднее | 14 400 req/день. При исчерпании → GigaChat |
| hh.ru API блокирует | Низкая | Среднее | User-Agent + ручной ввод как fallback |
| LLM-ответы нестабильны | Средняя | Высокое | Pydantic-валидация + retry (до 3) |
| Не хватает времени | Средняя | Высокое | Приоритизация Must-требований |
| Docker Hub заблокирован | Высокая | Среднее | Зеркала: mirror.gcr.io, Yandex CR |

**Escalation при критических блокерах:**
- LLM полностью недоступен → Ollama (локально)
- PostgreSQL не работает → SQLite + FAISS (деградация)
- Не хватает времени → сократить до Upload + Manual Vacancy + Rewrite + Text Output

---

## 19. Границы MVP

### 19.1. В объёме (In Scope)

| Компонент | Объём |
|-----------|-------|
| Аутентификация | Email + пароль, JWT |
| Резюме | PDF/DOCX, парсинг, LLM-структуризация |
| Вакансии | hh.ru (анонимный), URL-импорт, ручной ввод |
| AI-оптимизация | GigaChat Pro + Llama 3, Match Score, ATS |
| Экспорт | DOCX |
| UI | Streamlit Demo (20 прототипов, модульная архитектура) |
| Инфраструктура | Docker Compose, PostgreSQL, Redis, RabbitMQ, Local FS |
| Тестирование | Unit + Integration, 352 теста, 100% coverage |

### 19.2. Вне объёма (Out of Scope → Future)

| Компонент | Фаза |
|-----------|------|
| React SPA | Phase 2 |
| OAuth hh.ru | Phase 2 |
| ЮKassa | Phase 2 |
| 2FA | Phase 2 |
| GPT-4o | Phase 2 |
| PDF export + шаблоны | Phase 2 |
| WYSIWYG-редактор | Phase 2 |
| Email verification | Phase 2 |
| Telegram-бот | Phase 3 |
| Mobile app | Phase 3 |
| B2B API | Phase 3 |

---

*ResumeCraft MVP — минимальный функциональный продукт, покрывающий базовый pipeline AI-оптимизации резюме для российского рынка труда.*

# ResumeCraft — AI-реврайтер резюме для российского рынка труда

![Version](https://img.shields.io/badge/version-1.2.0-blueviolet)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/framework-FastAPI-009688)
![PostgreSQL](https://img.shields.io/badge/database-PostgreSQL_16-336791)
![GigaChat](https://img.shields.io/badge/AI-GigaChat_Pro-ff6600)
![Anthropic](https://img.shields.io/badge/AI-Claude_Sonnet_4-cc785c)
![License](https://img.shields.io/badge/license-GPL--3.0-green)
![Status](https://img.shields.io/badge/status-MVP-orange)

**Интеллектуальный сервис оптимизации резюме под конкретные вакансии российского рынка труда.**
Интеграция с HeadHunter API · Мультимодельная AI-архитектура · ATS-оптимизация · Match Score · Мультиформатный экспорт

> **Версия:** 1.2  
> **Дата:** Март 2026  
> **Проект:** ResumeCraft — AI-реврайтер резюме для российского рынка труда  
> **Лицензия:** GPL-3.0 (обусловлена зависимостью от PyMuPDF, AGPL 3.0)

---

## Содержание

1. [О проекте](#1-о-проекте)
2. [Проблема и мотивация](#2-проблема-и-мотивация)
3. [Ключевые возможности](#3-ключевые-возможности)
4. [Демонстрация интерфейса](#4-демонстрация-интерфейса)
5. [Архитектура системы](#5-архитектура-системы)
6. [Технологический стек](#6-технологический-стек)
7. [Структура проекта](#7-структура-проекта)
8. [Схема базы данных](#8-схема-базы-данных)
9. [API-эндпоинты](#9-api-эндпоинты)
10. [Интеграция с HeadHunter API](#10-интеграция-с-headhunter-api)
11. [AI/ML-компоненты](#11-aiml-компоненты)
12. [Pipeline обработки резюме](#12-pipeline-обработки-резюме)
13. [Тарифные планы](#13-тарифные-планы)
14. [Установка и запуск](#14-установка-и-запуск)
15. [Переменные окружения](#15-переменные-окружения)
16. [Docker](#16-docker)
17. [Тестирование](#17-тестирование)
18. [HTML-прототип](#18-html-прототип)
19. [Безопасность](#19-безопасность)
20. [Лицензия](#20-лицензия)

---

## 1. О проекте

**ResumeCraft** — веб-сервис на базе AI для автоматической оптимизации резюме под конкретные вакансии российского рынка труда. Сервис анализирует загруженное резюме, извлекает требования из целевой вакансии (в том числе через hh.ru API) и с помощью LLM перерабатывает текст так, чтобы максимально соответствовать требованиям работодателя и проходить ATS-фильтры.

Проект создан как ВКР и одновременно является коммерческим MVP, готовым к запуску. Архитектурные решения и функциональные требования обоснованы данными рынка и анализом конкурентов.

### 1.1. Миссия

Помочь каждому соискателю представить профессиональный опыт максимально выгодно, повысив шансы на приглашение на собеседование. ResumeCraft устраняет барьер между реальными компетенциями кандидата и формальными требованиями ATS-фильтров, которые отсеивают до 75% потенциально подходящих резюме.

**Ключевая ценность:** среднестатистический соискатель тратит 3–6 часов на ручную адаптацию резюме под одну вакансию. ResumeCraft выполняет это за 10–30 секунд.

### 1.2. Целевые метрики

| Метрика | Значение |
|---------|----------|
| Средний рост Match Score | +34% |
| Время оптимизации | 10–30 сек |
| ATS-совместимость | A+ |
| Время до первого результата | < 3 минут |
| Конверсия Free → Standard | 8–12% |

### 1.3. Целевая аудитория

| Сегмент | Боль | Готовность платить |
|---------|------|-------------------|
| **Белые воротнички** 25–45 лет | Индекс hh 5,9–7,3, ATS отсеивает 75% | 490–1 490 ₽/мес |
| **IT-специалисты** | Слабые soft skills в резюме | 1 490 ₽/мес |
| **Карьерные переходчики** | Невозможно «перевести» опыт на язык новой отрасли | 490 ₽/мес |
| **Студенты и начинающие** | Нет опыта написания резюме | Free / 490 ₽/мес |

> Подробный анализ аудитории (персоны, CJM, JTBD, TAM/SAM/SOM) — см. `ANALYSIS.md`.

---

## 2. Проблема и мотивация

### 2.1. Рыночная ситуация

Россия переживает парадокс: при рекордно низкой безработице (2,3%) наблюдается рост конкуренции среди белых воротничков. Количество офисных вакансий сократилось на 25%, число активных резюме выросло на 25%, а индекс hh.ru вырос с 3,7 до 7,3.

**HeadHunter** — абсолютный лидер (64,3% трафика, 93,3 млн резюме, 50+ млн уникальных пользователей). Интеграция с hh.ru API — стратегическое преимущество, отсутствующее у всех конкурентов.

### 2.2. Проблемы соискателей

1. **Обязанности вместо достижений** — соискатели перечисляют должностные инструкции вместо количественных результатов
2. **Незнание ATS** — 75% резюме отсеиваются автоматически из-за отсутствия ключевых слов, неправильного формата
3. **Шаблонность** — треть работодателей не рассматривают типовые резюме без персонализации
4. **Размытые заголовки** — «Менеджер» вместо точного названия целевой позиции

### 2.3. Gap на рынке

**Глобальные лидеры** (Rezi.ai, Jobscan, Resume Worded) недоступны: нет русского языка, нет hh.ru, невозможна оплата из РФ.

**Российские аналоги** ограничены: Cvator.ru — непредсказуемое качество AI; Rezumus.com — нельзя загрузить существующее резюме; hh.ru AI-ассистент — только для работодателей.

| Сервис | Русский | hh.ru | Загрузка CV | Оплата из РФ |
|--------|:-------:|:-----:|:-----------:|:------------:|
| Rezi.ai ($29/мес) | ❌ | ❌ | ✅ | ❌ |
| Jobscan ($49/мес) | ❌ | ❌ | ✅ | ❌ |
| Cvator.ru | ✅ | ❌ | ✅ | ✅ |
| Rezumus.com | ✅ | ❌ | ❌ | ✅ |
| **ResumeCraft** (490 ₽/мес) | ✅ | ✅ | ✅ | ✅ |

> Подробные данные рынка — см. `ANALYSIS.md` и `REFERENCES.md`.  
> Детальное описание MVP — см. `BASELINE.md`.

---

## 3. Ключевые возможности

### 3.1. AI-реврайтинг резюме

Глубокая переработка текста с помощью LLM с учётом целевой вакансии, ключевых слов для ATS, метрик достижений (формат «Действие + Результат + Метрика») и стандартов российского рынка.

**Пример:**

| До | После |
|----|-------|
| Управлял командой | Руководил кросс-функциональной командой из 12 человек, увеличив MAU на 40% |
| Работал с аналитикой | Внедрил data-driven подход: A/B-тестирование 30+ гипотез, рост конверсии на 35% |

**Принципы:** не выдумывать факты, не удалять релевантный опыт, адаптировать под вакансию, структурировать по релевантности.

### 3.2. Интеграция с hh.ru

Три способа указания целевой вакансии:

| Способ | Описание |
|--------|----------|
| 🔍 **Поиск** | Встроенный интерфейс с фильтрами (название, город, зарплата, опыт) |
| 🔗 **URL** | Вставка ссылки на вакансию hh.ru → автопарсинг |
| ✏️ **Ручной ввод** | Произвольное описание вакансии с любого сайта |

### 3.3. Match Score (0–100%)

Интеллектуальная система скоринга по четырём компонентам:

| Компонент | Вес | Описание |
|-----------|-----|----------|
| **Ключевые слова** | 40% | Совпадение терминов и навыков с вакансией |
| **Опыт и релевантность** | 25% | Semantic similarity эмбеддингов + skills overlap |
| **Структура** | 20% | Наличие обязательных секций, ATS-совместимость |
| **Читаемость** | 15% | Качество формулировок, наличие метрик |

Типичный результат: рост с 45–55% до 78–92% (+34 п.п. в среднем).

### 3.4. ATS-оптимизация

| Рейтинг | Баллы | Описание |
|---------|-------|----------|
| **A+** | 90–100 | Отличная совместимость ✅ |
| **A** | 80–89 | Хорошая, минимальные улучшения ✅ |
| **B+** | 70–79 | Хорошая, есть что улучшить ✅ |
| **B** | 60–69 | Удовлетворительная ⚠️ |
| **C** | 50–59 | Средняя, пробелы ⚠️ |
| **D** | < 50 | Плохая ❌ |

### 3.5. Выбор AI-модели

| Модель | Качество | Скорость | Доступ |
|--------|----------|----------|--------|
| **GigaChat Pro** | 95% | ~12 сек | Все планы |
| **Anthropic Claude** | 93% | ~10 сек | Standard+ |
| **OpenAI GPT-4o** | 92% | ~18 сек | Standard+ |
| **OpenRouter** ¹ | 90–98% | ~15 сек | Все планы |

GigaChat Pro — рекомендованная модель: #1 на MERA для русского языка, данные в РФ, оплата в рублях. Для OpenAI, Anthropic и OpenRouter доступен двухшаговый выбор: провайдер → конкретная модель (список получается динамически через API).

> ¹ OpenRouter — мульти-провайдер, доступ к Claude, Gemini, Mistral и др. через единый API.
> В MVP подключены **4 LLM-провайдера**: GigaChat Pro, Anthropic Claude, OpenRouter, OpenAI.

### 3.6. Экспорт и редактор

- **Форматы:** DOCX (все планы), PDF (Phase 2, Standard+), hh.ru (Phase 2, Pro)
- **Шаблоны:** Minimal (все планы), Professional (Phase 2, Standard+), Creative (Phase 2, Pro)
- **Интерактивный редактор** (Phase 2) — 5 секций с drag & drop, AI-подсказки в реальном времени
- **Diff-сравнение** — параллельное отображение оригинала и оптимизированной версии с цветовой подсветкой
- **История оптимизаций** — полная хронология с возможностью возврата к любой версии

---

## 4. Демонстрация интерфейса

Полнофункциональный кликабельный прототип из 20 HTML-экранов с дизайн-системой ResumeCraft Design System v2.0.

### 4.1. Карта экранов

```
Публичные:
  01 — Landing       02 — Auth          03 — Password Recovery
  04 — Email Verify  05 — Pricing       20 — Error 404

Основной поток:
  06 — Dashboard     07 — My Resumes    08 — Upload
  09 — Vacancy       10 — AI Models     11 — Processing
  12 — Results       13 — Editor        14 — Export
  15 — History

Настройки:
  16 — Profile       17 — AI Settings   18 — Subscription
  19 — Security
```

### 4.2. Основной пользовательский поток

```
Landing ──→ Auth ──→ Dashboard ──→ Upload
  (01)      (02)      (06)         (08)
                                     │
Export ←── Results ←── Processing ←── Vacancy
 (14)      (12)        (11)         (09)
             │                        │
           Editor                  Models
            (13)                    (10)
```

### 4.3. Дизайн-система

| Параметр | Значение |
|----------|----------|
| Шрифт | Inter (Google Fonts) |
| Основной цвет | #565ADD (Indigo) |
| Градиент | #4F46E5 → #7C3AED |
| Скругления | 20px / 12px / 8px |
| Breakpoint | 768px (Desktop → Mobile) |

Прототип не требует сборки — чистый HTML/CSS/JavaScript. Общая стилизация в `shared-styles.css`, навигация в `shared-nav.js`.

---

## 5. Архитектура системы

### 5.1. Высокоуровневая архитектура

```
┌──────────────────────────────────────────────────────┐
│                 КЛИЕНТСКИЙ УРОВЕНЬ                   │
│                                                      │
│              React SPA (Vite + TypeScript)            │
│                                                      │
└──────────────────────┬───────────────────────────────┘
                       │ HTTPS
┌──────────────────────┼───────────────────────────────┐
│             ┌───────┴───────┐                        │
│             │     Nginx     │  Reverse Proxy, SSL    │
│             └───────┬───────┘                        │
│                     │                                │
│  ┌──────────────────┴─────────────────────────────┐  │
│  │       FastAPI Application (async)              │  │
│  │                                                │  │
│  │  Auth · Resumes · Vacancies · Rewriter · ML    │  │
│  │                                                │  │
│  │  Middleware: CORS, Rate Limiter, Auth Guard     │ │
│  └──┬─────────┬─────────┬─────────┬───────────────┘  │
│     │         │         │         │                  │
│  ┌──┴───┐ ┌──┴───┐ ┌──┴───┐ ┌──┴──────────────┐      │
│  │Postgr│ │Local │ │Redis │ │  Celery Workers  │     │
│  │SQL 16│ │FS    │ │ 7.x  │ │  LLM tasks      │      │
│  │+pgvec│ │Docker│ │cache+│ │                  │     │
│  │tor   │ │volume│ │result│ └────────┬─────────┘     │
│  └──────┘ └──────┘ └──────┘          │               │
│                              ┌───────┴────────┐      │
│                              │   RabbitMQ     │      │
│                              │   3.13+        │      │
│                              │   broker       │      │
│                              └───────┬────────┘      │
│                                      │               │
│                              ┌───────┴────────┐      │
│                              │   LLM APIs     │      │
│                              │   GigaChat     │      │
│                              │   Anthropic    │      │
│                              │   OpenRouter   │      │
│                              │   OpenAI       │      │
│                              └────────────────┘      │
│                  СЕРВЕРНЫЙ УРОВЕНЬ                   │
└──────────────────────────────────────────────────────┘
```

### 5.2. Компоненты системы

| Компонент | Назначение |
|-----------|-----------|
| **FastAPI** | Async REST API. 4 бизнес-модуля: Auth, Resumes, Vacancies, Rewriter + ML-пакет |
| **PostgreSQL 16 + pgvector** | Реляционные данные + JSONB + векторные эмбеддинги — всё в одной БД |
| **Celery + RabbitMQ** | Асинхронная обработка LLM-задач (8–30 сек). RabbitMQ — брокер, 3 очереди: default, hh_api, export |
| **Redis 7.x** | Кэш (справочники hh.ru, TTL 1–24ч) + Celery result backend |
| **Local FS** | Docker volume `/data/uploads` для PDF/DOCX файлов. Миграция на MinIO/S3 в продакшене |
| **LLM API Layer** | Strategy Pattern: GigaChat / Anthropic / OpenRouter / OpenAI с автоматическим fallback |

### 5.3. Ключевые паттерны

| Паттерн | Применение |
|---------|-----------|
| **Domain-driven design** | Код по бизнес-доменам: auth, resumes, vacancies, rewriter |
| **Strategy pattern** | Выбор LLM-провайдера в runtime |
| **Event-driven** | Celery tasks для async LLM-вызовов |
| **Repository pattern** | Абстракция доступа к данным |
| **Pipeline pattern** | Последовательная 8-шаговая обработка: parse → analyze → rewrite → score |
| **Dependency injection** | FastAPI `Depends()` для сервисов и сессий |

**Архитектурные решения:**
- **Монолит** (не микросервисы) — скорость разработки, простота отладки, доменная организация позволяет выделить модули позже
- **Celery** (не BackgroundTasks) — отдельный процесс, горизонтальное масштабирование, retry-логика, Flower мониторинг
- **React SPA** (Vite + TypeScript) — типизированный фронтенд, nginx-прокси к API

---

## 6. Технологический стек

### 6.1. Backend

| Технология | Версия | Назначение |
|-----------|--------|------------|
| **Python** | 3.11+ | Основной язык |
| **FastAPI** | 0.115+ | Async веб-фреймворк |
| **Pydantic** | 2.x | Валидация данных |
| **SQLAlchemy** | 2.x | ORM (async mode) |
| **Alembic** | 1.x | Миграции БД |
| **Celery** | 5.x | Асинхронные задачи |
| **RabbitMQ** | 3.13+ | Брокер сообщений |
| **Redis** | 7.x | Кэш + result backend |
| **PostgreSQL** | 16 | Реляционная БД |
| **pgvector** | 0.7+ | Векторный поиск |
| **Local FS** | Docker volume | Файловое хранилище |
| **PyJWT** | 2.x | JWT-токены |
| **httpx** | 0.27+ | Async HTTP-клиент |

### 6.2. AI/ML

| Технология | Назначение |
|-----------|------------|
| **GigaChat SDK** | Интеграция с GigaChat API (Сбер) |
| **anthropic** (SDK) | Прямая интеграция с Anthropic Claude |
| **openai** (SDK) | OpenAI, OpenRouter — единый SDK |
| **PyMuPDF** (fitz) | Извлечение текста из PDF (AGPL 3.0) |
| **python-docx** | Чтение и создание DOCX |
| **LibreOffice headless** | Конвертация DOCX → PDF |
| **sentence-transformers** | Генерация эмбеддингов |
| **pytesseract** | OCR для сканов |

### 6.3. Frontend и DevOps

| Технология | Назначение |
|-----------|------------|
| **HTML5 / CSS3 / JS** | Прототип (20 экранов) |
| **React 19 + TypeScript** | SPA Frontend |
| **Vite 6** | Сборка frontend |
| **Vitest + Testing Library** | Тесты frontend (198 тестов) |
| **Docker + Compose** | Контейнеризация, 7 сервисов |
| **Nginx** 1.27 | Serving SPA + API proxy |
| **GitHub Actions** | CI/CD (lint, test, build, deploy) |
| **pytest + Ruff + mypy** | Тестирование + линтинг |

---

## 7. Структура проекта

### 7.1. Дерево каталогов

```
src/app/
├── __init__.py
├── main.py                # FastAPI app factory, middleware, lifespan
├── core/                  # Общие компоненты
│   ├── config.py          # pydantic-settings, .env
│   ├── security.py        # bcrypt, JWT, OAuth2PasswordBearer
│   ├── database.py        # async engine, sessionmaker, Base
│   ├── celery_app.py      # Celery конфигурация
│   ├── storage.py         # Local FS / MinIO абстракция
│   ├── dependencies.py    # FastAPI Depends()
│   └── exceptions.py      # Кастомные HTTP-исключения
├── auth/                  # Аутентификация
│   ├── router.py          # POST /auth/register, /login, /refresh, /logout
│   ├── schemas.py         # Pydantic-модели
│   ├── models.py          # SQLAlchemy User
│   └── service.py         # Бизнес-логика
├── resumes/               # Управление резюме
│   ├── router.py          # POST /resumes/upload, GET/DELETE /resumes/{id}
│   ├── schemas.py         # ResumeUploadResponse, ParsedResume
│   ├── models.py          # SQLAlchemy Resume
│   └── service.py         # Парсинг, LLM-структуризация
├── vacancies/             # Вакансии + hh.ru
│   ├── router.py          # GET /vacancies/search, POST /vacancies/from-url
│   ├── schemas.py         # VacancyResponse, HHSearchParams
│   ├── models.py          # SQLAlchemy Vacancy
│   ├── service.py         # CRUD + hh.ru клиент
│   └── hh_client.py       # Async httpx-клиент для api.hh.ru
├── rewriter/              # AI-оптимизация
│   ├── router.py          # POST /rewrite, GET /rewrite/{task_id}/*
│   ├── schemas.py         # RewriteRequest, RewriteResult
│   ├── models.py          # SQLAlchemy RewriteHistory
│   ├── service.py         # Оркестрация pipeline
│   └── tasks.py           # Celery tasks
├── export/                # Экспорт
│   ├── router.py          # GET /export/{id}/docx
│   └── service.py         # python-docx генерация
└── ml/                    # ML-пакет
    ├── llm_client.py      # BaseLLMClient (ABC), GigaChat, Anthropic, OpenAI, OpenRouter
    ├── llm_factory.py     # LLMClientFactory (Strategy Pattern)
    ├── prompts.py         # Системные промпты
    ├── embeddings.py      # sentence-transformers → VECTOR(1536)
    ├── scoring.py         # Match Score (4 компонента)
    └── parser.py          # PyMuPDF, python-docx, OCR fallback

tests/                     # Зеркалирует src/app/
├── conftest.py            # Fixtures: async client, test DB, factories
├── test_auth/             # 55 тестов
├── test_resumes/          # 39 тестов
├── test_vacancies/        # 42 теста
├── test_rewriter/         # 40 тестов
├── test_export/           # 11 тестов
├── test_ml/               # 71 тест
├── test_core/             # 79 тестов
├── test_main.py           # 3 теста (middleware, health)
├── test_main_extra.py     # 4 теста (error handlers, lifespan)
├── test_health.py         # 1 тест
├── test_coverage_gaps.py  # 22 теста (edge-cases)
├── test_integration_llm.py # 24 теста (реальные LLM API)
└── test_e2e_browser.py    # 38 тестов (Playwright E2E)

alembic/                   # Миграции PostgreSQL

frontend/                  # React SPA Frontend
├── Dockerfile             # node:20 build → nginx:1.27 serve
├── nginx.conf             # SPA routing + API proxy → app:8000
├── package.json           # Vite 6 + React 19 + TypeScript
├── index.html             # Entry point
└── src/
    ├── main.tsx           # BrowserRouter + AuthProvider
    ├── App.tsx            # Маршрутизация (23 routes)
    ├── contexts/          # AuthContext (JWT + localStorage)
    ├── services/          # API-клиент (fetch + Bearer)
    ├── data/              # Демо-данные
    ├── styles/            # CSS из Prototype/ + app.css
    ├── components/layout/ # AppLayout, PublicLayout, CenteredLayout
    ├── pages/             # 23 page components (+PrivacyPage, TermsPage, AboutPage)
    └── test/              # 198 тестов (Vitest + Testing Library)

Prototype/                 # 20 HTML-прототипов (все реализованы в React SPA)
```

### 7.2. Принципы организации кода

Доменная организация по модели Netflix Dispatch и рекомендациям **fastapi-best-practices** (24.8k ★):

| Принцип | Реализация |
|---------|-----------|
| **Домены изолированы** | auth, resumes, vacancies, rewriter — самодостаточные пакеты |
| **Единая структура** | Каждый домен: router.py, schemas.py, models.py, service.py |
| **core/** | Общие компоненты: config, security, database, celery, storage |
| **ml/** | Выделенный ML-пакет: LLM-клиент, промпты, парсер, скоринг |
| **tests/ зеркалируют src/** | Тесты рядом с тестируемым модулем |

---

## 8. Схема базы данных

4 таблицы в MVP + 3 дополнительные в Phase 2. PostgreSQL 16 + расширения `uuid-ossp` и `vector`:

**MVP (Phase 1) — 4 таблицы:**

| Таблица | Назначение | Ключевые поля |
|---------|-----------|---------------|
| **users** | Пользователи | email, hashed_password, plan, optimizations_used |
| **resumes** | Загруженные резюме | user_id FK, file_path, raw_text, parsed_data JSONB, embedding VECTOR(1536), status |
| **vacancies** | Вакансии | user_id FK, hh_id, title, description, key_skills JSONB, embedding VECTOR(1536) |
| **rewrite_history** | История оптимизаций | resume_id FK, vacancy_id FK, original_text, rewritten_text, model_name, match_score_before/after, ats_rating |

**Phase 2 — 3 таблицы:**

| Таблица | Назначение | Ключевые поля |
|---------|-----------|---------------|
| **user_profiles** | Профили (1:1) | user_id FK, first_name, last_name, position, skills JSONB |
| **subscriptions** | Подписки (ЮKassa) | user_id FK, plan_type, status, expires_at, auto_renew |
| **payments** | Платежи (ЮKassa) | user_id FK, subscription_id FK, amount, status, yukassa_payment_id |

**Индексы:** B-tree на FK и status-полях, HNSW на VECTOR(1536) для косинусного сходства.

**Миграции:** Alembic — атомарные, reversible, в CI/CD перед деплоем.

> Полная SQL-схема и Pydantic-модели — см. `BASELINE.md` §8.

---

## 9. API-эндпоинты

Все эндпоинты: REST, версионирование `/api/v1/`, формат JSON, авторизация JWT Bearer.

### 9.1. Аутентификация

| Метод | Путь | Auth | Описание |
|-------|------|:----:|----------|
| POST | `/auth/register` | ❌ | Регистрация (email + пароль) |
| POST | `/auth/login` | ❌ | Вход → access (30 мин) + refresh (30 дней) |
| POST | `/auth/refresh` | 🔄 | Обновление access-токена |
| POST | `/auth/logout` | ✅ | Выход |
| POST | `/auth/password-reset` | ❌ | Запрос сброса пароля |
| POST | `/auth/verify-email` | ❌ | Подтверждение email |
| POST | `/auth/2fa/enable` | ✅ | Включение 2FA (QR-код) ² |
| POST | `/auth/2fa/verify` | ✅ | Верификация 2FA-кода ² |

> ² 2FA и email verification подключаются в Phase 2.

### 9.2. Пользователь

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/users/me` | Профиль текущего пользователя |
| PUT | `/users/me` | Обновление профиля |
| PUT | `/users/me/password` | Смена пароля |
| DELETE | `/users/me` | Удаление аккаунта |

### 9.3. Резюме

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/resumes/upload` | Загрузка (multipart, PDF/DOCX, ≤ 10 МБ) |
| GET | `/resumes` | Список (пагинация, фильтры) |
| GET | `/resumes/{id}` | Детали (включая parsed_data) |
| PUT | `/resumes/{id}` | Обновление данных |
| DELETE | `/resumes/{id}` | Удаление (+ файл) |

### 9.4. Вакансии

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/vacancies/search` | Поиск через hh.ru API |
| POST | `/vacancies/from-url` | Импорт по URL hh.ru |
| POST | `/vacancies/manual` | Ручной ввод |
| GET | `/vacancies/{id}` | Детали |
| DELETE | `/vacancies/{id}` | Удаление |

### 9.5. Оптимизация

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/rewrite` | Запуск (resume_id, vacancy_id, model) → 202 Accepted |
| GET | `/rewrite/{task_id}/status` | Статус: step, progress %, ETA |
| GET | `/rewrite/{task_id}/result` | Результат: score, diff, keywords |
| GET | `/rewrite/history` | История оптимизаций |

### 9.6. Экспорт

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/export/{id}/pdf` | Экспорт в PDF (LibreOffice headless) ³ |
| GET | `/export/{id}/docx` | Экспорт в DOCX (python-docx) |
| POST | `/export/hh` | Публикация на hh.ru (OAuth) ³ |

> ³ PDF-экспорт и публикация на hh.ru подключаются в Phase 2. В MVP доступен экспорт в DOCX.

### 9.7. Подписка

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/subscription` | Текущий план и лимиты |
| POST | `/subscription/upgrade` | Обновление → ЮKassa |
| POST | `/subscription/cancel` | Отмена подписки |
| POST | `/subscription/webhook` | Webhook от ЮKassa |

### 9.8. Примеры запросов и ответов

**Регистрация:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "SecurePass1"}'
# → 201 Created {"access_token": "eyJ...", "refresh_token": "eyJ...", "token_type": "bearer"}
```

**Загрузка резюме:**
```bash
curl -X POST http://localhost:8000/api/v1/resumes/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@resume.pdf"
# → 201 Created {"id": "uuid", "file_format": "pdf", "status": "draft"}
```

**Запуск оптимизации:**
```bash
curl -X POST http://localhost:8000/api/v1/rewrite \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"resume_id": "uuid", "vacancy_id": "uuid", "model": "gigachat-pro"}'
# → 202 Accepted {"task_id": "uuid"}
```

**Проверка статуса:**
```bash
curl http://localhost:8000/api/v1/rewrite/<task_id>/status \
  -H "Authorization: Bearer <token>"
# → 200 OK {"step": "rewrite", "progress": 55, "status": "processing"}
```

---

## 10. Интеграция с HeadHunter API

### 10.1. Обзор

Официальный API: `https://api.hh.ru` (REST, JSON, OAuth 2.0). Документация: **github.com/hhru/api** (~590 ★).

| Характеристика | Значение |
|----------------|----------|
| Rate Limits | ~7 req/sec (auth), ~2 req/sec (anon) |
| Пагинация | `page` + `per_page` (макс. 100) |
| User-Agent | `ResumeCraft/2.0 (contact@resumecraft.ru)` |

### 10.2. Используемые эндпоинты

| Endpoint | Авторизация | Назначение |
|----------|:-----------:|------------|
| `GET /vacancies` | ❌ | Поиск вакансий |
| `GET /vacancies/{id}` | ❌ | Детали вакансии |
| `GET /dictionaries` | ❌ | Справочники |
| `GET /professional_roles` | ❌ | Профессиональные роли |
| `GET /areas` | ❌ | Регионы и города |
| `GET /resumes/mine` | ✅ OAuth | Резюме пользователя на hh.ru |
| `PUT /resumes/{id}` | ✅ OAuth | Публикация на hh.ru (Pro) |

### 10.3. OAuth 2.0

- **Анонимный** — поиск вакансий, справочники (80% функционала MVP)
- **Соискатель** (scope `user:write`) — публикация резюме на hh.ru (Pro-тариф)
- Регистрация приложения на **dev.hh.ru**

### 10.4. Ограничения и fallback

- **Rate limiting** → Exponential backoff + Redis-кэширование справочников
- **Недоступность hh.ru** → Ручной ввод вакансии как fallback
- **Парсинг URL** → regex `r'hh\.ru/vacancy/(\d+)'`

---

## 11. AI/ML-компоненты

### 11.1. LLM-стратегия

Мультипровайдерная архитектура (Strategy Pattern) с единым интерфейсом `BaseLLMProvider`:

| Характеристика | GigaChat Pro | Claude Sonnet 4 | GPT-4o-mini | OpenRouter (100+ моделей) |
|----------------|-------------|-----------------|------------|--------------------------|
| Контекст | 32K tokens | 200K tokens | 128K tokens | Зависит от модели |
| Цена input | ~$1.2/1M tok | $3.00/1M tok | $0.15/1M tok | Зависит от модели |
| Скорость | ~12 сек | ~10 сек | ~18 сек | Зависит от модели |
| Русский язык | ✅ #1 MERA | ✅ Отлично | ⚠️ Хорошо | Зависит от модели |
| Данные в РФ | ✅ | ❌ | ❌ | ❌ |
| Лимиты | По тарифу Сбера | По тарифу Anthropic | По тарифу OpenAI | По тарифу OpenRouter |

**4 LLM-провайдера** в MVP: GigaChat Pro, Anthropic Claude, OpenRouter (100+ моделей), OpenAI. Для OpenAI, Anthropic и OpenRouter реализован 2-ступенчатый выбор модели с динамической загрузкой доступных суб-моделей через API.

### 11.2. Match Score

Расчёт как взвешенная комбинация: Keywords (40%) + Experience (25%) + Structure (20%) + Readability (15%). Компоненты совпадают с UI (12-results.html).

- **Keywords** — TF-IDF токенизация, пересечение множеств
- **Experience** — skills overlap × 0.6 + cosine similarity эмбеддингов × 0.4
- **Structure** — наличие обязательных секций, длина, формат
- **Readability** — качество формулировок, наличие метрик

### 11.3. Промпт-инженерия

Системный промпт содержит 5 блоков: роль эксперта, правила (не выдумывать факты, формула «Действие + Результат + Метрика»), формат JSON-ответа, ограничения, контекст вакансии. Каждый ответ LLM проходит Pydantic-валидацию с retry до 3 попыток.

### 11.4. Fallback-стратегия

```
1. GigaChat Pro (основная)
   ↓ если недоступен
2. Anthropic Claude
   ↓ если недоступен
3. OpenRouter (100+ моделей)
   ↓ если недоступен
4. OpenAI GPT-4o
   ↓ если недоступен
5. Ошибка: «Все LLM-провайдеры временно недоступны»
```

Fallback автоматический с уведомлением пользователя. JSON-парсер LLM-ответов включает многоуровневую коррекцию: `strict=False` → regex-исправление пропущенных запятых → regex-извлечение `{...}`.

---

## 12. Pipeline обработки резюме

### 12.1. Восемь шагов обработки

| Шаг | Название | Описание | Прогресс | Время |
|-----|----------|----------|----------|-------|
| 1 | **Extract** | Чтение данных резюме и вакансии из БД | 0–10% | ~1 сек |
| 2 | **Gap Analysis** | Сравнение навыков, выявление пробелов | 10–20% | ~2 сек |
| 3 | **Strategy** | Стратегия оптимизации: что усилить, какие слова добавить | 20–35% | ~2 сек |
| 4 | **Rewrite** | LLM API call с системным промптом + контекст | 35–55% | 5–20 сек |
| 5 | **Validate** | Pydantic-валидация ответа, факт-чекинг | 55–70% | ~1 сек |
| 6 | **Score** | Match Score (до/после) + ATS-рейтинг | 70–82% | ~2 сек |
| 7 | **Diff** | Генерация diff оригинал ↔ оптимизированный | 82–92% | ~1 сек |
| 8 | **Complete** | Сохранение в rewrite_history, обновление счётчиков | 92–100% | ~1 сек |

**Общее время:** 10–30 секунд. UI (экран 11) показывает анимированный прогресс-бар.

### 12.2. Жизненный цикл задачи

1. `POST /rewrite` → FastAPI валидирует лимиты → создаёт Celery task → `202 Accepted {task_id}`
2. Celery Worker выполняет 8 шагов, обновляет прогресс в Redis
3. Frontend polling `GET /rewrite/{task_id}/status` каждые 2 секунды
4. `GET /rewrite/{task_id}/result` → полный результат

### 12.3. Обработка ошибок

| Ошибка | Обработка |
|--------|-----------|
| LLM timeout (60 сек) | Retry с альтернативным провайдером |
| Невалидный JSON от LLM | Retry (до 3 раз) с уточнённым промптом |
| Rate limit API | Exponential backoff (2, 4, 8 сек) |
| Парсинг не удался | OCR fallback → ошибка пользователю |
| Лимит тарифа | 429 + предложение upgrade |

---

## 13. Тарифные планы

| Параметр | Free | Standard | Pro |
|----------|------|----------|-----|
| **Цена** | 0 ₽ | 490 ₽/мес | 1 490 ₽/мес |
| **Цена/год** | — | 3 990 ₽ (−32%) | 11 990 ₽ (−33%) |
| **Оптимизаций/мес** | 5 | 30 | Безлимит |
| **AI-модели** | OpenRouter | GigaChat Pro + Claude + OpenRouter | Все (+ GPT-4o) |
| **Экспорт** | DOCX | PDF + DOCX | Все + hh.ru |
| **Шаблоны** | 1 (Minimal) | 3 | Все + кастом |

> В MVP подключены **4 LLM-провайдера**: GigaChat Pro, Anthropic Claude, OpenRouter, OpenAI.

**Позиционирование:** в 5–9x дешевле глобальных аналогов (Rezi $29, Jobscan $49) с нативной интеграцией hh.ru.

---

## 14. Установка и запуск

### 14.1. Системные требования

| Компонент | Минимум | Рекомендуется |
|-----------|---------|---------------|
| OS | macOS 13+ / Ubuntu 22.04+ / Windows 11 (WSL2) | Ubuntu 24.04 |
| Python | 3.11 | 3.12+ |
| PostgreSQL | 16 + pgvector 0.7 | 17 + pgvector 0.8 |
| RAM | 4 ГБ | 8 ГБ+ |
| Docker | 24.0+ | 27.0+ |
| Docker Compose | v2.20+ | v2.30+ |

### 14.2. Установка (локальная разработка)

```bash
# 1. Клонирование
git clone https://github.com/your-org/resumecraft.git
cd resumecraft

# 2. Python виртуальное окружение
python3.11 -m venv .venv
source .venv/bin/activate      # Linux/macOS
# .venv\Scripts\activate       # Windows

# 3. Зависимости
pip install -r requirements-dev.txt

# 4. Переменные окружения
cp .env.example .env
# Отредактируйте .env — минимум SECRET_KEY и DATABASE_URL

# 5. PostgreSQL + pgvector (если без Docker)
createdb resumecraft
psql resumecraft -c 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp"; CREATE EXTENSION IF NOT EXISTS "vector";'

# 6. Миграции БД
alembic upgrade head

# 7. Запуск FastAPI
uvicorn app.main:app --app-dir src --reload --port 8000

# 8. Запуск Celery worker (отдельный терминал)
cd src && celery -A app.core.celery_app:celery_app worker --loglevel=info

# 9. Frontend (отдельный терминал)
cd frontend && npm install && npm run dev
```

### 14.3. Быстрый старт с Docker

```bash
# 1. Скопировать .env
cp .env.example .env
# Отредактировать SECRET_KEY

# 2. Запуск всех сервисов
docker compose up -d

# 3. Миграции
docker compose exec app alembic upgrade head

# 4. Проверка
curl http://localhost:8000/health
# → {"status": "healthy"}

# Сервисы:
#   API:      http://localhost:8000
#   Flower:   http://localhost:5555
#   RabbitMQ: http://localhost:15672 (guest/guest)
```

### 14.4. Проверка

```bash
# Тесты
pytest --cov --cov-report=term-missing

# Линтинг
ruff check src/ tests/

# Типы
mypy src/

# Безопасность
bandit -r src/ -ll

# Health check
curl http://localhost:8000/health
```

---

## 15. Переменные окружения

Все настройки в `.env` (не коммитится), загрузка через `pydantic-settings`:

| Переменная | Обязательна | По умолчанию | Описание |
|-----------|:-----------:|-------------|----------|
| `SECRET_KEY` | ✅ | — | Ключ для JWT (64+ символов) |
| `DATABASE_URL` | ✅ | `postgresql+asyncpg://...` | PostgreSQL connection string |
| `REDIS_URL` | ⚠️ | `redis://localhost:6379/0` | Redis для кэша |
| `CELERY_BROKER_URL` | ⚠️ | `amqp://guest:guest@localhost:5672//` | RabbitMQ брокер |
| `CELERY_RESULT_BACKEND` | ⚠️ | `redis://localhost:6379/1` | Celery result backend |
| `GIGACHAT_CREDENTIALS` | ❌ | — | API-ключ GigaChat (Сбер) |
| `OPENAI_API_KEY` | ❌ | — | API-ключ OpenAI |
| `ANTHROPIC_API_KEY` | ❌ | — | API-ключ Anthropic Claude |
| `OPENROUTER_API_KEY` | ❌ | — | API-ключ OpenRouter |
| `HH_USER_AGENT` | ❌ | `ResumeCraft/2.0 (...)` | User-Agent для hh.ru |
| `UPLOAD_DIR` | ❌ | `./uploads` | Директория загрузок |
| `CORS_ORIGINS` | ❌ | `["http://localhost:*"]` | CORS origins |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | ❌ | `30` | Время жизни access token |
| `REFRESH_TOKEN_EXPIRE_DAYS` | ❌ | `30` | Время жизни refresh token |

Пример: `.env.example` в корне проекта.

---

## 16. Docker

### 16.1. Сервисы Docker Compose

7 контейнеров: `app` (FastAPI), `celery-worker`, `db` (pgvector/pgvector:pg16), `redis` (redis:7-alpine), `rabbitmq` (rabbitmq:3.13-management), `flower` (мониторинг Celery), `frontend` (React SPA, nginx).

Файлы хранятся в Docker volume `/data/uploads`.

### 16.2. Запуск

```bash
# Запуск всех 7 сервисов
docker compose up -d

# Проверка статуса
docker compose ps

# Миграции БД
docker compose exec app alembic upgrade head

# Логи FastAPI
docker compose logs -f app

# Остановка
docker compose down

# Остановка + удаление данных
docker compose down -v
```

**Порты:**

| Сервис | URL |
|--------|-----|
| React SPA | http://localhost:3000 |
| FastAPI | http://localhost:8000 |
| Flower | http://localhost:5555 |
| RabbitMQ Management | http://localhost:15672 |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

---

## 17. Тестирование

### 17.1. Обзор

| Метрика | Значение |
|---------|----------|
| **Backend тестов (unit)** | 416 (pytest + pytest-asyncio) |
| **Backend тестов (integration)** | 23 (реальные LLM API: GigaChat, Anthropic, OpenRouter, OpenAI) |
| **Backend тестов (E2E)** | 38 (Playwright) |
| **Frontend тестов** | 198 (Vitest + @testing-library/react) |
| **Всего тестов** | 675 |
| **Backend покрытие** | 100% |
| **БД в тестах** | SQLite (aiosqlite, in-memory) |

### 17.2. Запуск тестов

```bash
# Backend — все тесты
pytest

# Backend — с покрытием
pytest --cov --cov-report=term-missing

# Backend — конкретный модуль
pytest tests/test_auth/ -v

# Frontend — все тесты
cd frontend && npm test

# Frontend — watch mode
cd frontend && npm run test:watch
```

### 17.3. Структура тестов

| Модуль | Тестов | Что покрывается |
|--------|--------|----------------|
| `test_auth/` | 55 | Регистрация, логин, refresh, logout, модели, схемы, сервис, edge-cases |
| `test_resumes/` | 39 | Upload, CRUD, парсинг PDF/DOCX, валидация, эмбеддинги |
| `test_vacancies/` | 42 | hh.ru клиент, from-url, manual, CRUD, retry, таймауты, HTTP-ошибки |
| `test_rewriter/` | 40 | Celery tasks, pipeline, статусы, история, LLM retry |
| `test_export/` | 11 | DOCX-генерация, структурированные/plain данные |
| `test_ml/` | 71 | LLM-клиенты (GigaChat, Anthropic, OpenRouter, OpenAI), фабрика, парсер, скоринг, эмбеддинги, санитизация |
| `test_core/` | 79 | Config, security, database, storage, exceptions, dependencies |
| `test_main*` | 7 | Middleware, error handlers, lifespan, health |
| `test_coverage_gaps` | 22 | Edge-cases: scoring, embedding fallback, export |
| `test_integration_llm` | 24 | Интеграция: реальные вызовы 4 LLM-провайдеров (GigaChat, Anthropic, OpenRouter, OpenAI) |
| `test_e2e_browser` | 38 | E2E: Playwright browser-тесты (навигация, формы, wizard, настройки) |

### 17.4. Инструменты проверки качества

```bash
# Линтинг (0 warnings)
ruff check src/ tests/

# Типы (strict)
mypy src/

# Безопасность (0 HIGH/CRITICAL)
bandit -r src/ -ll

# Аудит зависимостей
pip-audit
```

---

## 18. HTML-прототип

20 экранов в директории `Prototype/`:

| # | Файл | Экран |
|---|------|-------|
| 01 | `01-landing.html` | Лендинг |
| 02 | `02-auth.html` | Авторизация / регистрация |
| 03 | `03-password-recovery.html` | Восстановление пароля |
| 04 | `04-email-verify.html` | Подтверждение email |
| 05 | `05-pricing.html` | Тарифные планы |
| 06 | `06-dashboard.html` | Дашборд |
| 07 | `07-resumes.html` | Список резюме |
| 08 | `08-upload.html` | Загрузка (drag & drop) |
| 09 | `09-vacancy.html` | Выбор вакансии |
| 10 | `10-models.html` | Выбор AI-модели |
| 11 | `11-processing.html` | Обработка (4 визуальных шага / 8 шагов backend) |
| 12 | `12-results.html` | Результаты (Match Score, diff) |
| 13 | `13-editor.html` | WYSIWYG-редактор |
| 14 | `14-export.html` | Экспорт (PDF/DOCX) |
| 15 | `15-history.html` | История оптимизаций |
| 16 | `16-settings-profile.html` | Настройки профиля |
| 17 | `17-settings-ai.html` | Настройки AI |
| 18 | `18-settings-subscription.html` | Управление подпиской |
| 19 | `19-settings-security.html` | Безопасность |
| 20 | `20-error-404.html` | Ошибка 404 |

Интерактивные элементы: drag & drop загрузка, live search, прогресс-бар, diff-просмотрщик, WYSIWYG-редактор, табы навигации.

---

## 19. Безопасность

### 19.1. Аутентификация

- JWT: access token (30 мин, HS256) + refresh token (30 дней)
- Пароли: bcrypt (cost=12)
- 2FA: TOTP (Google Authenticator) — Pro-тариф
- Rate limiting: 5 попыток/мин на логин, lockout 15 мин

### 19.2. Защита данных

- SQL-инъекции: SQLAlchemy ORM (параметризованные запросы)
- XSS: HTML-escaping, CSP headers
- IDOR: `WHERE user_id = current_user.id` в каждом запросе
- Загрузка файлов: MIME-валидация, magic bytes, размер ≤ 10 МБ
- CORS: ограничение `allowed_origins`
- Секреты: `.env` (не в git), secrets manager в production

### 19.3. AI-безопасность

- Prompt Injection: разделение system/user промптов, input sanitization
- LLM API-ключи: `.env`, ротация

### 19.4. Соответствие

- GigaChat Pro: данные обрабатываются на серверах Сбера в РФ
- Right to delete: пользователь может удалить все данные через настройки

---

## 20. Лицензия

Проект лицензирован под **GNU General Public License v3.0** (GPL-3.0).

Причина: зависимость от [PyMuPDF](https://pymupdf.readthedocs.io/) (AGPL-3.0) обязывает распространять код под совместимой copyleft-лицензией.

Полный текст: [LICENSE](LICENSE)

---

**ResumeCraft** — AI-оптимизация резюме для российского рынка труда

[О проекте](#1-о-проекте) · [Быстрый старт](#14-установка-и-запуск) · [Тестирование](#17-тестирование) · [Docker](#16-docker) · [Лицензия](#20-лицензия)


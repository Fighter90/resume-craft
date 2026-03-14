# ResumeCraft — AI-реврайтер резюме для российского рынка труда

![Version](https://img.shields.io/badge/version-1.26.0-blueviolet)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/framework-FastAPI-009688)
![PostgreSQL](https://img.shields.io/badge/database-PostgreSQL_16-336791)
![GigaChat](https://img.shields.io/badge/AI-GigaChat_Pro-ff6600)
![Anthropic](https://img.shields.io/badge/AI-Claude_Sonnet_4-cc785c)
![License](https://img.shields.io/badge/license-GPL--3.0-green)
![Status](https://img.shields.io/badge/status-MVP-orange)

**Интеллектуальный сервис оптимизации резюме под конкретные вакансии российского рынка труда.**
Интеграция с HeadHunter API · Мультимодельная AI-архитектура · ATS-оптимизация · Match Score · Мультиформатный экспорт

> **Версия:** 1.26.0 (V44)
> **Дата:** 14 марта 2026
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

### Команда № 42

> Емельянов Сергей
CTO, Product Manager
Техническая реализация (архитектура, выбор ПО, код), руководство командой
@sergey_in_job

> Фаритова Дилара
Product Manager
Концепт идеи, план работ
@dilara_faritova

> Пономарева Александра
Аналитик / UX-ресечер
Составление персон, анализ ЦА, пользовательский путь, анализ рынка
@ponomarevva

> Винокуров Александр
Аналитик
Анализ конкурентов
@ShepardCS

> Кожокарь Алина
Аналитик
Проработка baseline, проверка качества реврайтинга
@alinadmitrakova

> Филаткина Юлия
Тестировщик
Тестирование, работа с фокус-группой
@yulk0

> Дизайн создан с помощью [https://variant.com](https://variant.com)

**Группа МУПИТБ251 • НИУ ВШЭ • «Управление продуктом в IT-бизнесе»**

### Презентация проекта

[Смотреть](ResumeCraft_MVP_DataScience-3.pdf)

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
| **GigaChat Pro** | 95% | ~12 сек | Все планы † |
| **Anthropic Claude** | 93% | ~10 сек | Standard+ |
| **OpenAI GPT-4o** | 92% | ~18 сек | Standard+ |
| **OpenRouter** ¹ | 90–98% | ~15 сек | Все планы |
| **Groq** ² | 90–95% | ~3 сек | Все планы |

GigaChat Pro — рекомендованная модель: #1 на MERA для русского языка, данные в РФ, оплата в рублях. Для OpenAI, Anthropic и OpenRouter доступен двухшаговый выбор: провайдер → конкретная модель (список получается динамически через API провайдеров). Локально установленные API-ключи автоматически определяются и активируют соответствующих провайдеров.

> ¹ OpenRouter — мульти-провайдер, доступ к Claude, Gemini, Mistral и др. через единый API.
> ² Groq — быстрый inference на LPU (Llama, Mixtral, Gemma).
> † GigaChat требует активную подписку Сбер с положительным балансом.
> В MVP подключены **5 LLM-провайдеров**: GigaChat Pro, Anthropic Claude, OpenRouter, OpenAI, Groq.

### 3.6. Экспорт и редактор

- **Форматы:** DOCX, PDF, TXT (все планы)
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
| **openai** (SDK) | OpenAI, OpenRouter и Groq через OpenAI-совместимый API |
| **PyMuPDF** (fitz) | Извлечение текста из PDF (AGPL 3.0) |
| **python-docx** | Чтение и создание DOCX |
| **reportlab** | Генерация PDF (≥4.0) |
| **anthropic** (SDK) | Интеграция с Anthropic Claude |
| **sentence-transformers** | Генерация эмбеддингов |
| **pytesseract + Pillow** (optional) | OCR fallback для сканов при отдельной установке |

### 6.3. Frontend и DevOps

| Технология | Назначение |
|-----------|------------|
| **HTML5 / CSS3 / JS** | Прототип (20 экранов) |
| **React 19 + TypeScript** | SPA Frontend |
| **Vite 6** | Сборка frontend |
| **Vitest + Testing Library** | Тесты frontend (580+ тестов) |
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
│   ├── exceptions.py      # Кастомные HTTP-исключения
│   ├── encryption.py      # AES-шифрование API-ключей (Fernet)
│   ├── limiter.py         # Rate limiting (slowapi + Redis)
│   └── seed.py            # Seed данные для разработки
├── auth/                  # Аутентификация
│   ├── router.py          # POST /auth/register, /login, /refresh, /logout, GET /auth/verify/{token}
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
│   ├── router.py          # GET /export/{id}/{docx,pdf,txt}
│   └── service.py         # python-docx, reportlab, txt генерация
├── settings/              # Настройки пользователя
│   ├── router.py          # GET/PUT/DELETE /settings/ai-keys, ai-toggles, ai-model
│   ├── schemas.py         # AIKeyResponse, AITogglesUpdate, AIModelSettings
│   ├── models.py          # SQLAlchemy UserSetting
│   └── service.py         # AES-шифрование, CRUD
└── ml/                    # ML-пакет
    ├── llm_client.py      # BaseLLMClient (ABC), GigaChat, Anthropic, OpenAI, OpenRouter
    ├── llm_factory.py     # LLMClientFactory (Strategy Pattern)
    ├── prompts.py         # Системные промпты
    ├── embeddings.py      # sentence-transformers → VECTOR(1536)
    ├── scoring.py         # Match Score (4 компонента)
    ├── parser.py          # PyMuPDF, python-docx, OCR fallback
    ├── router.py          # GET /models, /models/{provider}/sub-models
    └── sanitize.py        # Sanitization для LLM input

tests/                     # Зеркалирует src/app/
├── conftest.py            # Fixtures: async client, test DB, factories
├── test_auth/             # 64 теста
├── test_resumes/          # 65 тестов
├── test_vacancies/        # 55 тестов
├── test_rewriter/         # 40 тестов
├── test_export/           # 38 тестов
├── test_ml/               # 96 тестов
├── test_core/             # 81 тест
├── test_main.py           # 3 теста (middleware, health)
├── test_main_extra.py     # 4 теста (error handlers, lifespan)
├── test_health.py         # 1 тест
├── test_coverage_gaps.py  # 22 теста (edge-cases)
├── test_coverage_100.py   # 40 тестов (100% покрытие)
├── test_integration_llm.py # 23 теста (реальные LLM API)
├── test_e2e_browser.py    # 38 тестов (Playwright E2E)
├── test_acceptance.py     # 52 теста (приёмочные)
├── test_v17_fixes.py      # 50 тестов (покрытие v1.7 правок)
├── test_v20_fixes.py      # 34 теста (покрытие v1.8 правок)
├── test_v23_fixes.py      # 30 тестов (покрытие v1.9 правок)
├── test_v24_fixes.py      # 25 тестов (покрытие v1.9 правок)
├── test_v26_fixes.py      # 13 тестов (покрытие v1.10 правок)
├── test_v27_fixes.py      # 36 тестов (покрытие v1.11 правок)
├── test_v28_fixes.py      # 27 тестов (покрытие v1.12 правок)
├── test_v30_fixes.py      # 10 тестов (покрытие v1.13 правок)
├── test_v37_fixes.py      # 14 тестов (покрытие v1.22 правок)
├── test_v39_fixes.py      # 13 тестов (покрытие v1.23 правок)
└── test_full_coverage.py  # 66 тестов (100% покрытие)

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
    └── test/              # 580+ тестов (Vitest + Testing Library)

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

5 таблиц в MVP + 3 дополнительные в Phase 2. PostgreSQL 16 + расширения `uuid-ossp` и `vector`:

**MVP — 5 таблиц:**

| Таблица | Назначение | Ключевые поля |
|---------|-----------|---------------|
| **users** | Пользователи | email, hashed_password, plan, optimizations_used, is_verified, avatar_url, deleted_at, scheduled_deletion |
| **resumes** | Загруженные резюме | user_id FK, file_path, raw_text, parsed_data JSONB, embedding VECTOR(1536), status |
| **vacancies** | Вакансии | user_id FK, hh_id, title, description, key_skills JSONB, embedding VECTOR(1536) |
| **rewrite_history** | История оптимизаций | resume_id FK, vacancy_id FK, original_text, rewritten_text, model_name, match_score_before/after, ats_rating |
| **user_settings** | Настройки (AES) | user_id FK, category, key, value, is_encrypted; UNIQUE(user_id, category, key) |

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
| GET | `/auth/verify/{token}` | ❌ | Подтверждение email по токену |
| POST | `/auth/resend-verification` | ✅ | Повторная отправка письма подтверждения |

> ² 2FA подключается в Phase 2.

### 9.2. Пользователь

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/auth/me` | Профиль текущего пользователя |
| PUT | `/auth/me` | Обновление профиля |
| PUT | `/auth/me/password` | Смена пароля |
| DELETE | `/auth/me` | Soft-delete аккаунта (требуется пароль, 30 дней) |
| POST | `/auth/me/restore` | Восстановление удалённого аккаунта |
| POST | `/auth/me/avatar` | Загрузка аватара (multipart, ≤ 2 МБ) |
| DELETE | `/auth/me/avatar` | Удаление аватара |

### 9.3. Резюме

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/resumes/upload` | Загрузка (multipart, PDF/DOCX, ≤ 10 МБ) |
| POST | `/resumes/from-text` | Создание резюме из текста |
| GET | `/resumes` | Список (пагинация, фильтры) |
| GET | `/resumes/{id}` | Детали (включая parsed_data) |
| PUT | `/resumes/{id}` | Обновление данных |
| DELETE | `/resumes/{id}` | Soft-delete (пометка deleted_at) |
| POST | `/resumes/{id}/restore` | Восстановление удалённого резюме |
| GET | `/resumes/{id}/file` | Скачивание оригинального файла |
| GET | `/resumes/{id}/preview` | Данные для просмотрщика |

### 9.4. Вакансии

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/vacancies/search` | Поиск через hh.ru API |
| GET | `/vacancies/hh/{hh_id}` | Полные данные вакансии с hh.ru |
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
| GET | `/export/{id}/docx` | Экспорт в DOCX (python-docx) |
| GET | `/export/{id}/pdf` | Экспорт в PDF (reportlab) |
| GET | `/export/{id}/txt` | Экспорт в TXT (plain text) |

### 9.7. Настройки (Settings)

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/settings/ai-keys` | Маскированные API-ключи |
| PUT | `/settings/ai-keys/{provider}` | Сохранить ключ (AES-шифрование) |
| DELETE | `/settings/ai-keys/{provider}` | Удалить ключ |
| GET | `/settings/ai-toggles` | Состояния провайдеров (on/off) |
| PUT | `/settings/ai-toggles` | Обновить toggles |
| GET | `/settings/ai-model` | Модель по умолчанию |
| PUT | `/settings/ai-model` | Установить модель по умолчанию |

### 9.8. Модели (Models)

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/models` | Список провайдеров + доступность |
| GET | `/models/health` | Статус доступности всех провайдеров (пинг API) |
| GET | `/models/{provider}/sub-models` | Подмодели провайдера (динамически через API) |

### 9.9. Подписка (Phase 2)

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/subscription` | Текущий план и лимиты |
| POST | `/subscription/upgrade` | Обновление → ЮKassa |
| POST | `/subscription/cancel` | Отмена подписки |

### 9.10. Примеры запросов и ответов

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

### 10.3. OAuth 2.0

- **Текущий MVP** использует только анонимный режим hh.ru API для поиска и получения деталей вакансий
- **Соискательский OAuth** (scope `user:write`) рассматривается как future enhancement для публикации резюме на hh.ru
- Регистрация приложения на **dev.hh.ru** потребуется при переходе к OAuth-сценарию

### 10.4. Ограничения и fallback

- **Rate limiting** → Exponential backoff + Redis-кэширование справочников
- **Недоступность hh.ru** → Ручной ввод вакансии как fallback
- **Парсинг URL** → regex `r'hh\.ru/vacancy/(\d+)'`

---

## 11. AI/ML-компоненты

### 11.1. LLM-стратегия

Мультипровайдерная архитектура (Strategy Pattern) с единым интерфейсом `BaseLLMProvider`:

| Характеристика | GigaChat Pro | Claude Sonnet 4 | GPT-4o-mini | OpenRouter (100+ моделей) | Groq |
|----------------|-------------|-----------------|------------|--------------------------|------|
| Контекст | 32K tokens | 200K tokens | 128K tokens | Зависит от модели | Зависит от модели |
| Цена input | ~$1.2/1M tok | $3.00/1M tok | $0.15/1M tok | Зависит от модели | Зависит от модели |
| Скорость | ~12 сек | ~10 сек | ~18 сек | Зависит от модели | ~3 сек |
| Русский язык | ✅ #1 MERA | ✅ Отлично | ⚠️ Хорошо | Зависит от модели | ⚠️ Зависит от модели |
| Данные в РФ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Лимиты | По тарифу Сбера | По тарифу Anthropic | По тарифу OpenAI | По тарифу OpenRouter | По тарифу Groq |

**5 LLM-провайдеров** в MVP: GigaChat Pro, Anthropic Claude, OpenRouter (100+ моделей), OpenAI и Groq. Для OpenAI, Anthropic, OpenRouter и Groq реализован 2-ступенчатый выбор модели с динамической загрузкой доступных суб-моделей через API.

### 11.2. Match Score

Расчёт как взвешенная комбинация: Keywords (40%) + Experience (25%) + Structure (20%) + Readability (15%). Компоненты совпадают с UI (12-results.html).

- **Keywords** — токенизация, фильтрация стоп-слов и пересечение множеств
- **Experience** — token-based cosine similarity по тексту резюме и вакансии
- **Structure** — наличие обязательных секций, длина, формат
- **Readability** — качество формулировок, наличие метрик

### 11.3. Промпт-инженерия

Системный промпт содержит 5 блоков: роль эксперта, правила (не выдумывать факты, формула «Действие + Результат + Метрика»), формат JSON-ответа, ограничения, контекст вакансии. Каждый ответ LLM проходит Pydantic-валидацию с retry до 3 попыток.

### 11.4. Fallback-стратегия (будет реализована в следующей версии релиза)

```
1. GigaChat Pro (основная)
   ↓ если недоступен
2. Anthropic Claude
   ↓ если недоступен
3. OpenRouter (100+ моделей)
   ↓ если недоступен
4. Groq
   ↓ если недоступен
5. OpenAI GPT-4o
  ↓ если недоступен
6. Ошибка: «Все LLM-провайдеры временно недоступны»
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
| **Экспорт** | DOCX, TXT | PDF + DOCX + TXT | Все форматы |
| **Шаблоны** | 1 (Minimal) | 3 | Все + кастом |

> В MVP подключены **5 LLM-провайдеров**: GigaChat Pro, Anthropic Claude, OpenRouter, OpenAI, Groq.

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
| **Backend тестов** | 950+ (pytest + pytest-asyncio, acceptance, integration, E2E) |
| **Frontend тестов** | 580+ (Vitest + @testing-library/react) |
| **Всего тестов** | **1500+** |
| **Backend покрытие** | 100% (2540 statements, 0 uncovered) |
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
| `test_auth/` | 64 | Регистрация, логин, refresh, logout, верификация, аватар, soft-delete, модели, схемы |
| `test_resumes/` | 65 | Upload, CRUD, парсинг PDF/DOCX, валидация, soft-delete, restore, preview |
| `test_vacancies/` | 55 | hh.ru клиент, from-url, manual, CRUD, retry, таймауты, HTTP-ошибки, hh детали |
| `test_rewriter/` | 40 | Celery tasks, pipeline, статусы, история, LLM retry |
| `test_export/` | 38 | DOCX/PDF/TXT-генерация, структурированные/plain данные, Content-Disposition |
| `test_ml/` | 96 | LLM-клиенты (5 провайдеров), фабрика, роутер моделей, парсер, скоринг, эмбеддинги, санитизация |
| `test_core/` | 81 | Config, security, database, storage, exceptions, dependencies, encryption |
| `test_main*` | 7 | Middleware, error handlers, lifespan, health |
| `test_coverage_gaps` | 22 | Edge-cases: scoring, embedding fallback, export |
| `test_coverage_100` | 40 | 100% покрытие: AnthropicClient, _handle_llm_error, create_from_text, execute_rewrite, celery preload |
| `test_integration_llm` | 23 | Интеграция: реальные вызовы 4 LLM-провайдеров |
| `test_e2e_browser` | 38 | E2E: Playwright browser-тесты |
| `test_acceptance` | 52 | Приёмочные тесты |
| `test_v17_fixes` | 50 | Покрытие v1.7 правок |
| `test_v20_fixes` | 34 | Покрытие v1.8 правок: аватар, o-series, dropdown z-index |
| `test_v23_fixes` | 30 | Покрытие v1.9 правок: health-check, Claude parser, Groq |
| `test_v24_fixes` | 25 | Покрытие v1.9 правок: LLM health, avatar initials |
| `test_v26_fixes` | 13 | Покрытие v1.10: NAV regression, email verification |
| `test_v27_fixes` | 36 | Покрытие v1.11: RESET-001, o-series regex |
| `test_v28_fixes` | 27 | Покрытие v1.12: KEY-CHECK-001, commit before delay |
| `test_v31_fixes` | 15 | Покрытие регрессионных исправлений v31 |
| `test_v32_fixes` | 4 | Покрытие регрессионных исправлений v32 |
| `test_v33_fixes` | 4 | Покрытие регрессионных исправлений v33 |
| `test_v34_fixes` | 18 | Покрытие регрессионных исправлений v34 |
| `test_v30_fixes` | 10 | Покрытие v1.13: scoring determinism, nginx config |
| `test_full_coverage` | 66 | 100% покрытие: все непокрытые строки |

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

## Changelog

### v1.26.0 (14 марта 2026) — V44: Model Mapping Fix + hh.ru Parser + Delete Hardening

**Устранение регрессий из QA Report #40 (V43):**

- **OPENAI-MODEL-MAPPING / ANTHROPIC-MODEL-MAPPING (P1):** исправлена утечка `subModel` state — при переключении провайдера `subModel` сбрасывается синхронно. Ранее GigaChat-Pro отправлялся OpenAI/Anthropic.
- **ACCOUNT-DELETE-500-REGRESSION (P1):** `logger` перенесён в начало файла, весь handler обёрнут в try/except для перехвата любых ошибок (flush, commit, FK constraints).
- **GROQ-ALLAM-502 (P2):** keywords ужесточены — вместо широкого `'not found'` теперь 4 точных паттерна.
- **HH-RESUME-LINK-400 (P2):** добавлен модуль `hh_parser.py` — парсинг резюме с hh.ru через Playwright (headless browser) с graceful fallback.

**Тесты:** 46 новых тестов (`test_v44_fixes.py`). Всего: 1002 passed.

Подробности: `CHANGELOG.md`.

### v1.25.0 (14 марта 2026) — V43: Delete Account Fix + Model Detection + UX

**Устранение оставшихся дефектов из QA Report #39 (V42):**

- **ACCOUNT-DELETE-500-REGRESSION (P1):** `session.commit()` в `delete_me` handler обёрнут в try/except — raw SQLAlchemy ошибки теперь возвращают `DELETE_ACCOUNT_FAILED`, а не `INTERNAL_ERROR`.
- **GROQ-ALLAM-502 (P2):** расширена детекция model-not-found — обрабатываются `does not exist`, `invalid model`, `model not active`, `no such model` (Groq возвращает 400, не 404).
- **VACANCY-TITLE-002 (P3):** извлечение должности из `raw_text` резюме (паттерны «Должность:», «Позиция:») как fallback.
- **URL-VALIDATION-RAW-JSON (P3):** Pydantic validation arrays в ошибках отображаются как читаемые сообщения, а не raw JSON.

**Тесты:** 27 новых тестов (`test_v43_fixes.py`).

Подробности: `CHANGELOG.md`.

### v1.24.0 (13 марта 2026) — V42: Explicit Commit Fix + Model Validation

**Устранение корневой причины 503/500 и улучшения:**

- **PASSWORD-CHANGE-503 (P1):** explicit `session.commit()` перед отправкой Response(204) — ранее commit в dependency cleanup после ответа вызывал 503 через Nginx proxy_buffering.
- **AVATAR-DELETE-503 / AVATAR-UPLOAD-503 (P2):** аналогичный fix — explicit commit before response.
- **ACCOUNT-DELETE-500-REGRESSION (P1):** explicit commit в `delete_me` handler после `soft_delete_account()`.
- **GROQ-ALLAM-502 (P2):** обработчик 404 model-not-found в `_handle_llm_error()` → 400 с user-friendly сообщением.
- **VACANCY-TITLE-002 (P3):** фильтрация filename-like значений (e.g. `resume.pdf`) при автозаполнении должности.

**Тесты:** 24 новых теста (`test_v42_fixes.py`). Всего: 951 passed.

Подробности: `CHANGELOG.md`.

### v1.23.0 (13 марта 2026) — V39: Systemic 503 Fix + Soft-Delete

**Системное исправление паттерна 503 и новые фичи:**

- **PASSWORD-CHANGE-503 / AVATAR-DELETE-503 / LOGOUT-503 (P1-P3):** устранена корневая причина — убраны двойные commit из обработчиков, связи User model переведены на `lazy='noload'` (было `selectin`).
- **ACCOUNT-DELETE-HARD-vs-SOFT (P2):** `DELETE /me` теперь выполняет soft-delete с 30-дневным grace period. Вход восстанавливает аккаунт.
- **VACANCY-URL-OBJECT-ERROR (P3):** frontend корректно извлекает текст ошибки вместо `[object Object]`.
- **VACANCY-TITLE-002 (P3):** автозаполнение должности из имени файла резюме + предзаполнение поиска.

**Тесты:** 13 новых тестов (`test_v39_fixes.py`). Всего: 927 passed.

Подробности: `CHANGELOG.md`.

### v1.22.0 (13 марта 2026) — V37: Focus Group Improvements

**Исправления по итогам обратной связи от фокус-группы:**

- **AVATAR-DELETE-503 (P2):** исправлена обработка ошибок в `DELETE /api/v1/auth/me/avatar` — при сбое БД выполняется rollback и возвращается JSON-ответ с сообщением вместо необработанного исключения.
- **VACANCY-URL-500 (P3):** добавлена серверная валидация URL вакансии — невалидный URL теперь возвращает 400 с понятным сообщением вместо 500.
- **GROQ-MODEL-NAME-HISTORY (P4):** провайдер Groq добавлен в условие сохранения sub-model — в истории отображается полное имя модели.
- **SECURITY-AUTOFILL (P4):** исправлены `autocomplete` атрибуты полей паролей на странице безопасности.
- **AVATAR-DELETE-BTN-UX (P4):** кнопка «Удалить» аватар скрыта, если аватар не загружен.

**Тесты:** 14 новых тестов (`test_v37_fixes.py`).

Подробности: `CHANGELOG.md`, `IMPROVEMENTS.md`, `TESTS.md`.

### v1.21.0 (11 марта 2026) — V35.1: Regression Fix Pack

**Исправления дефектов V35:**

- **AVATAR-DELETE-503 (P2):** усилена устойчивость `DELETE /api/v1/auth/me/avatar` при ошибках storage backend (graceful fallback + корректная очистка `avatar_url`).
- **PROFILE-AVATAR-SIDEBAR (P4):** улучшена консистентность отображения аватара после upload/delete через явный `commit/refresh` в avatar-flow и синхронизацию UI-состояния профиля.
- **DELETE-FORM-NO-VALIDATION-MSG (P4):** форма удаления аккаунта теперь показывает явные сообщения валидации при пустом пароле/подтверждении.
- **SECURITY-AUTOFILL (P4):** ужесточены `autocomplete/name` атрибуты в полях смены/удаления пароля для снижения нежелательного browser autofill.
- **PHONE-MASK-FORMAT (P4 NEW):** добавлено форматирование номера в профиле (`+7 (XXX) XXX-XX-XX`) и нормализация до цифр при сохранении.

**Проверки:**

- Backend: `pytest tests/test_v34_fixes.py::TestAvatarDeletionGraceful tests/test_resumes/test_resumes_router.py::TestResumeFromUrl -q`.
- Frontend: `vitest run src/test/settings-pages.test.tsx` (добавлены/актуализированы кейсы под V35.1).

Подробности: `CHANGELOG.md`.

### v1.20.0 (11 марта 2026) — QA V35: Full Regression Round, Stability Improvements

**Подтверждённые исправления (по итогам QA #33):**

- **ACCOUNT-DELETE-500 (P1):** удаление аккаунта работает стабильно в production, GDPR-flow подтверждён.
- **PROFILE-PHONE-SAVE / PROFILE-CITY-SAVE (P2):** телефон и город сохраняются и читаются после перезагрузки профиля.
- **PROFILE-EMAIL-VERIFY (P3):** подтверждён доступ к повторной отправке письма через кнопку "Отправить повторно".
- Подтверждена работоспособность всех 5 AI-провайдеров: `GigaChat`, `OpenAI`, `Anthropic`, `OpenRouter`, `Groq`.
- Подтверждён экспорт в `DOCX`, `PDF`, `TXT`.

**Known issues (перенесены в следующий фикс-пакет):**

- `AVATAR-DELETE-503 (P2)` — удаление аватара периодически возвращает `503`.
- `PROFILE-AVATAR-SIDEBAR (P4)` — sidebar не всегда отображает avatar URL.
- `DELETE-FORM-NO-VALIDATION-MSG (P4)` — нет явных сообщений валидации формы удаления.
- `SECURITY-AUTOFILL (P4)` — автозаполнение полей пароля в security settings.
- `PHONE-MASK-FORMAT (P4 NEW)` — отображаются сырые цифры вместо форматированного номера.

Подробности: `qa_results/33_FULL_REGRESSION_V35.md` и `qa_results/AGENT_FIX_PROMPT_V35.md`.

### v1.19.0 (10 марта 2026) — QA V34: 15 Fixes (P1-P4), Profile Persistence, hh.ru Resume URL

**Ключевые исправления:**

- **ACCOUNT-DELETE-500 (P1):** `DELETE /api/v1/auth/me` теперь требует `password + confirmation: "УДАЛИТЬ"` и корректно выполняет каскадное удаление данных.
- **PROFILE-PHONE-SAVE / PROFILE-CITY-SAVE (P2):** поля `phone` и `city` сохраняются в БД и обрабатываются через `PUT /api/v1/auth/me`.
- **HH-RESUME-LINK-405 (P2):** добавлен `POST /api/v1/resumes/from-url` с валидацией hh.ru URL и fallback-сообщением при невозможности парсинга.
- **PDF-PARSE-502 (P2):** ошибки парсинга PDF/DOCX возвращаются как user-friendly `400`, а не `502`.
- **PROFILE-EMAIL-VERIFY (P3):** добавлен `POST /api/v1/auth/resend-verification` для повторной отправки письма подтверждения.
- **P4 UI/UX fixes:** исправлены формат истории моделей, валидация формы удаления, отображение аватара, autofill для смены пароля.

**Тесты и качество:**

- Добавлен набор интеграционных тестов `tests/test_v34_fixes.py`.
- Обновлены тесты `test_resumes_router.py`, `test_resumes_service.py`, `test_v20_fixes.py` под новый контракт удаления аккаунта.
- Версия синхронизирована до `1.19.0` во всех ключевых точках проекта.

Подробности: `CHANGELOG.md`.

### v1.18.0 (Март 2026) — QA V32: Limits Reset Endpoint, Pricing Sync, History Counter Clarity

**Bug Fixes & Infra:**

- **QA-LIMIT-001 (INFRA):** добавлен защищённый endpoint `POST /api/v1/admin/reset-optimization-limit` (через `X-Admin-Key`) для QA-сброса лимитов.
- **PRICING-MISMATCH-001 (P3):** тарифы синхронизированы между Landing, Pricing и Settings/Subscription; единая формулировка `Все AI-модели (BYOK)`.
- **HISTORY-COUNT-001 (P4 INFO):** на dashboard добавлена явная метрика `Успешных: X из Y`.

**Тесты:**

- +4 backend-теста (`test_v32_fixes.py`), +2 frontend-теста (`fixes-v32.test.tsx`)
- Backend: **951 collected** (без integration-LLM), Frontend: **579 тестов**, Всего: **1530**

### v1.16.0 (Март 2026) — QA V33: P0 KEY-CHECK Fix For New Accounts

**Bug Fixes:**

- **KEY-CHECK-001 (P0 BLOCKER):** убран client-side pre-check API-ключа в `ModelsPage`; запуск оптимизации теперь всегда идёт через backend.
- **VACANCY-PLACEHOLDER-001 (P3):** на `/app/vacancy` поле "Название должности" предзаполняется из данных резюме.
- **GROQ-CASE-001 (P4):** ошибки показывают корректное имя провайдера `Groq`.

**Тесты:**

- +4 backend-теста (`test_v33_fixes.py`), +2 frontend-теста (`fixes-v33.test.tsx`)
- Backend: **951 collected** (без integration-LLM в CI), Frontend: **577 тестов**, Всего: **1528**

### v1.15.0 (Март 2026) — QA V31: KEY-CHECK-001 Critical Fix, Error Sanitization, File Upload Fix

**Bug Fixes:**

- **KEY-CHECK-001** (P1 CRITICAL): Celery worker — свежий `create_async_engine` на каждую задачу, рефакторинг маппинга API-ключей
- **HISTORY-RAW-ERROR-001** (P2 MEDIUM): Санитизация ошибок LLM — сырые URL/JSON/HTTP-коды больше не попадают в UI
- **FILE-UPLOAD-001** (P3 LOW): File input скрыт через `opacity: 0` вместо `display: none` (исправление для WebKit)

**Тесты:**

- +15 backend-тестов (`test_v31_fixes.py`), +17 frontend-тестов (`fixes-v31.test.tsx`)
- Backend: **834 unit-тестов**, Frontend: **575 тестов**, Всего: **1522**

### v1.14.0 (Март 2026) — 100% Backend Coverage, 558 Frontend Tests, Documentation Refresh

**Backend тесты: 100% покрытие (2540/2540 statements)**

- +66 новых тестов (`test_full_coverage.py`): покрытие всех непокрытых строк
  - AnthropicClient edge cases, _handle_llm_error branches, create_from_text/url, execute_rewrite_task
  - Celery preload, database engine cleanup, seed data, lifespan events
  - Storage edge cases, config validation, encryption corner cases
- Backend: **819 unit-тестов passed** (было 578), **90 skipped** (integration LLM)
- Coverage: **2540 statements, 0 uncovered** (было 1722)

**Frontend тесты: 558 тестов (все passing)**

- Исправлены 32 сломанных теста в 6 файлах:
  - `pages.test.tsx`: адаптация к миграции localStorage→server API, password requirements
  - `fixes-v2.test.tsx`: обновление mock-структур для серверных ответов
  - `fixes-v3.test.tsx`: актуализация под текущие компоненты
  - `fixes-v5.test.tsx`: исправление model count assertions
  - `qa-fixes.test.tsx`: обновление текстовых проверок
  - `settings-pages.test.tsx`: удаление 2FA-тестов, адаптация к AI-настройкам
- Добавлен `@vitest/coverage-v8` для coverage-отчётов

**Качество кода:**

- `ruff format --check .` — 0 ошибок (124 файла)
- Форматирование: `test_v30_fixes.py`, `test_full_coverage.py`

**Версионирование:**

- `pyproject.toml`: 0.1.0 → 1.14.0 (синхронизация с app_version)
- `frontend/package.json`: 0.0.0 → 1.14.0
- Все 4 источника версии синхронизированы: config.py, pyproject.toml, package.json, README badge

**Документация:**

- README.md: обновлены метрики тестов (819 unit, 558 frontend, 1490 всего, 2540 statements)
- README.md: обновлена структура тестов (добавлены v23–v30, test_full_coverage)
- Создан CHANGELOG.md с полной историей версий

### v1.13.0 (Март 2026) — QA Retest V30 FINAL: все 5 провайдеров ✅, готово к релизу

**Статус: ГОТОВО К РЕЛИЗУ**

Полный QA retest подтвердил работоспособность всех 5 AI-провайдеров на свежем аккаунте:

| Провайдер | Модель | Match Score | ATS | Время |
|-----------|--------|-------------|-----|-------|
| GigaChat Pro | gigachat-pro | +13 (58→71) | B+ | 12 сек |
| OpenAI | o4-mini-2025-04-16 | +13 (56→69) | B | 29 сек |
| Anthropic Claude | claude-sonnet-4-6 | +24 (52→76) | B+ | 18 сек |
| OpenRouter | ai21/jamba-large-1.7 | +18 (52→70) | B+ | 14 сек |
| Groq | allam-2-7b | +19 (52→71) | B+ | 2 сек |

**Исправленные баги:**
- ✅ KEY-CHECK-001 (P1 CRITICAL): Optimization engine видит все API-ключи на свежих аккаунтах
- ✅ MODEL-SELECT-001 (P2 MEDIUM): Dropdown корректно показывает модели выбранного провайдера
- ✅ NAV-001 (P3 LOW): Навигация полностью работоспособна

**Оставшиеся замечания (не блокируют релиз):**
- ~~FILE-UPLOAD-001 (P3 LOW)~~: **ИСПРАВЛЕНО** — auth fallback + 401 retry + серверный парсинг ошибок + nginx `client_max_body_size 12m`
- SCORE-VARIANCE-001 (P4 INFO): Базовый скор ±6 пунктов — **ожидаемое поведение** (алгоритм детерминирован, разница из-за ввода текста)

**Фиксы V30 (patch 1.13.0):**

*Frontend (2 файла):*
- `api.ts` `uploadResume()`: добавлен `localStorage.getItem('access_token')` fallback, 401→`tryRefreshToken()`→retry, парсинг серверных ошибок вместо generic throw
- `nginx.conf`: добавлен `client_max_body_size 12m` в `location /api/` (ранее default 1MB блокировал файлы >1MB)

*Backend:*
- `config.py`: version bump 1.12.0 → 1.13.0

*Тесты V30:*
- Backend: 10 тестов (scoring determinism ×4, source checks ×4, nginx config ×2)
- Frontend: 5 тестов (localStorage auth, 401 retry, server error parsing, non-JSON fallback, no Content-Type)

**Документация:**
- REFERENCES.md: добавлена описательная часть с методологией отбора источников и обоснованием полноты (61 источник)
- DEPLOYMENT.md: добавлен Groq API в список внешних сервисов и production .env
- BASELINE.md: обновлён до 5 провайдеров (GigaChat + Anthropic + OpenRouter + OpenAI + Groq)
- README.md: version bump 1.12 → 1.13, changelog V30

**QA-артефакты:**
- `qa_results/QA_RETEST_V30_FINAL.md` — финальный отчёт
- `qa_results/AGENT_FIX_PROMPT_V30.md` — промт для исправления 2 minor-замечаний

### v1.12.0 (Март 2026) — QA v8: KEY-CHECK-001, NAV-001, isAuthError

**Backend (2 исправления):**
- KEY-CHECK-001 (P2 MEDIUM): Race condition — `session.commit()` теперь вызывается ДО `execute_rewrite_task.delay()`, гарантируя что Celery worker видит данные задачи и API-ключи пользователя
- KEY-CHECK-001 (groq): Добавлен `groq` в оба маппинга router pre-check (`_model_to_db_provider`, `_model_to_env_field`)

**Frontend (2 исправления):**
- NAV-001 (P3 LOW): Ссылка «Обновить до Pro →» — убран `preventDefault()` и `stopPropagation()`, оставлен чистый `<Link>` с `onClick` только для закрытия sidebar
- isAuthError: Сужена проверка ошибок — убраны generic `'unavailable'` и `'auth'`, оставлены точные маркеры (`api-ключ`, `не настроен`, `unauthorized`, `провайдер all`)

**Тесты:**
- Backend: 27 тестов (commit before delay, groq mappings, user_keys flow, factory fallback, Link regression)
- Frontend: 7 тестов (Link as `<a>`, no programmatic navigate, plan visibility, isAuthError precision)
- V27 тесты обновлены для совместимости с V28

**Документация:**
- README/BASELINE: version bump 1.11 → 1.12
- Changelog V28

### v1.11.0 (Март 2026) — QA v7: RESET-001, NAV-001, OPENAI-O4MINI

**Frontend (2 исправления):**
- RESET-001 (P1 HIGH): Кнопка «Сбросить» на странице AI-настроек больше НЕ удаляет сохранённые API-ключи — сбрасывает только тогглы и модель, с сохранением дефолтов на сервер
- NAV-001 (P3): Ссылка «Обновить до Pro →» — добавлен explicit onClick с navigate() для гарантии навигации при физическом клике

**Backend (1 исправление):**
- OPENAI-O4MINI (P3): Определение моделей o-серии усилено — regex `^o\d` вместо startswith tuple, корректно покрывает o1/o3/o4-mini и будущие o2/o5

**Тесты:**
- Backend: 28 тестов (regex o-series detection, max_completion_tokens vs max_tokens, factory resolution, source checks)
- Frontend: 6 тестов (navigate onClick, deleteAIKey not called, saveAIToggles/saveSelectedModel confirmation)

**Документация:**
- README/BASELINE: version bump 1.10 → 1.11
- Changelog V27

### v1.10.0 (Март 2026) — QA v6: NAV-001 regression fix, email verification consistency

**Frontend (2 исправления):**
- NAV-001 (REGRESSION): Ссылка «Обновить до Pro →» в sidebar — заменён `NavLink` на `Link`, добавлен CSS `pointer-events: auto; z-index: 2` для гарантии кликабельности
- EMAIL-VERIFY-001: Статус верификации email на странице профиля теперь динамический — показывает «Подтверждён» ✅ или «Не подтверждён» ⚠️ в зависимости от `user.is_verified`

**Backend:**
- GIGACHAT-001: Обработка ошибки биллинга GigaChat — подтверждена корректной (русское сообщение, кнопки fallback, слот не расходуется)

**Документация:**
- README/BASELINE: version bump 1.9 → 1.10
- Таблица провайдеров: GigaChat помечен `†` (требуется активная подписка Сбер)
- Changelog V26

**Тесты:**
- Backend: 15 тестов (email verification consistency, CSS checks, billing error handling)
- Frontend: 6 тестов (Link vs NavLink, dynamic verification badge, banner consistency)

**Known Issues:**
- ⚠️ GIGACHAT-001: GigaChat Pro требует пополнения баланса на developers.sber.ru (не баг приложения)

### v1.9.0 (Март 2026) — QA v5: 6 дефектов, health-check провайдеров, тесты

**Frontend (4 исправления):**
- P0-3-CLAUDE: Универсальный парсер ответа LLM — strip markdown code blocks (` ```json `), prefer `rewritten_data`, поддержка полей `name`/`position`/`contacts` (ResultsPage)
- GROQ-KEY: Groq добавлен в 3 пропущенные точки SettingsAiPage (post-save clear, reset clear, reset delete loop)
- AVATAR-001: Инициалы аватара в профиле теперь динамические из `firstName`/`lastName` (ранее захардкожено «АП»)
- LOGOUT-001 + NAV-001: Верифицировано — уже исправлены в V23 (logout в dropdown, NavLink для «Обновить до Pro»)

**Backend (1 новый эндпоинт):**
- GIGACHAT-001: `GET /models/health` — health-check всех LLM-провайдеров (пинг API, проверка ключа, детекция billing/auth ошибок)
- Ping-функции для GigaChat, OpenAI, Anthropic, OpenRouter, Groq

**Документация:**
- README: 4→5 провайдеров (добавлен Groq), таблица провайдеров, API docs `/models/health`
- Changelog V24

**Тесты:**
- Backend: тесты health-check эндпоинта, GROQ-KEY сохранение
- Frontend: тесты парсера Claude JSON, аватар инициалы, Groq key reset

### v1.8.0 (Март 2026) — QA v3 + v4: 28 FIX-пакетов, hh.ru export removal, 120 новых тестов, аудит документации

**Backend — QA v3 (8 исправлений):**
- P0-2: Match Score ×100 (Dashboard, Results, History, Export)
- P0-3: `GET /auth/me` и `GET /rewrite/history` возвращают JSON вместо неформатированного текста
- P0-4: OpenAI/OpenRouter o-series модели используют `max_completion_tokens` вместо `max_tokens`
- P1-2: `soft_delete_account` возвращает JSON-ошибку при неверном пароле (не HTML)
- P1-4: Обновлён список моделей OpenRouter (deepseek-r1, llama-4 и др.)
- P1-6: Аватар мигрирован из localStorage на сервер (POST/DELETE `/auth/me/avatar`)
- Login: поддержка JSON + form-data
- OpenRouter: search + optgroup-группировка моделей

**Backend — V19: парсинг и экспорт (4 новых возможности):**
- `GET /resumes/{id}/file` — скачивание оригинального файла резюме
- `GET /resumes/{id}/preview` — preview текста резюме (Markdown/HTML)
- `GET /export/{id}/txt` — экспорт результата в TXT
- Content-Disposition: RFC 5987 кодировка для кириллических имён файлов (UnicodeEncodeError fix)

**Frontend — QA v3 (8 исправлений):**
- P0-2: Match Score ×100 в Dashboard, Results, History, Export
- P0-3: RAW JSON → форматированный текст в ResultsPage
- P1-1: Выпадающее меню подмоделей: z-index=1000 и overflow-visible
- P1-6: Аватар на сервере (upload/delete через API) вместо localStorage
- P2-1: Прогресс-бар с плавной CSS-анимацией (transition 0.5s ease-in-out)
- P2-2: Корректное отображение diff с пробелами и `\n`
- P2-3: Очистка avatar в localStorage при миграции
- P3-1: OpenRouter search + optgroup-группировка

**Frontend — V19: hh.ru export removal + viewer (3 изменения):**
- Удалён формат hh.ru из ExportPage (карточка, ExternalLink, hh download logic)
- DOCX описание: «рекомендуем для hh.ru» → «рекомендуемый формат»
- ResumeViewerModal: модальный просмотр файла резюме (DOCX/PDF/TXT)

**Инфраструктура:**
- Alembic 007: `avatar_url VARCHAR(500)` → users
- Alembic 006: Исправлен `down_revision` для портативности
- Deps: `openai` 1.59.9 → 2.24.0, `python-docx` 1.1.2 → 1.2.0
- CI: ruff format + lint все файлы

**Документация:**
- Полный аудит кодовой базы vs документации
- BASELINE.md: схема БД (5 таблиц), API (40+ эндпойнтов), зависимости, границы MVP
- README.md: схема БД, API пути, дерево каталогов, метрики тестов, секции Settings/Models API

**Тесты:**
- +34 новых backend-тестов (`test_v20_fixes.py`): аватар (12), o-series (8), soft-delete (3), JSON (4), OpenRouter (3), LLM edge cases (4)
- +50 новых backend-тестов (V19): TXT export (27), resume file preview (23)
- +36 новых frontend-тестов (`export-v19.test.tsx`): unit, functional, integration, acceptance
- +8 новых backend-тестов (V18): o-series (4), form-data (3), json (1)
- Итого: **757 backend-тестов**, **534 frontend-тестов**, **1291 всего**

### v1.7.0 (Март 2026) — QA v2: 12 FIX пакетов, 50 новых тестов

**Безопасность (4 исправления):**
- API-ключи LLM перенесены из localStorage в зашифрованное хранилище БД — Fernet (AES-128-CBC) + SHA-256 derived key (FIX-001)
- openapi.json закрыт в production (`openapi_url=None`) — предотвращает утечку API-схемы (FIX-012)
- Rate limiting: login 5/min, register 3/min, rewrite 10/hour через slowapi + Redis (FIX-005)
- Защита от email enumeration: единый ответ 201 при регистрации (FIX-008/LIVE-013)

**Backend API (5 исправлений):**
- Новые эндпоинты экспорта: `GET /export/{id}/pdf` (reportlab) и `GET /export/{id}/txt` (FIX-003)
- LLM-провайдеры читают API-ключи пользователя из БД + проверка перед оптимизацией (FIX-002)
- Эндпоинт скачивания оригинального файла резюме: `GET /resumes/{id}/file` (FIX-011)
- Email-верификация: `GET /auth/verify/{token}` + 24-часовой JWT-токен (FIX-007)
- Soft-delete для резюме и аккаунтов: `deleted_at` + restore эндпоинты (FIX-007, FIX-009)

**Frontend UI (4 исправления):**
- DOCX-просмотр резюме через mammoth.js с XSS-защитой (DOMPurify) (FIX-004)
- Email-обрезка с CSS `text-overflow: ellipsis` в профиле (FIX-006)
- Счётчик оптимизаций показывает только COMPLETED (FIX-006)
- Кнопка «Найти» обёрнута в `<form>`, кнопки имеют `type` атрибуты (FIX-010)

**UX/UI:**
- Сообщение "LLM-провайдер all" заменено на "Все LLM-провайдеры" (FIX-008/LIVE-006)
- Удалены placeholder-секции 2FA и «Активные сессии» со страницы безопасности (FIX-008)
- Строки истории оптимизаций стали кликабельными (FIX-012)

**Инфраструктура:**
- Alembic 005: `is_verified` Boolean → users
- Alembic 006: SQL REPLACE "LLM-провайдер all" → "Все LLM-провайдеры" в rewrite_history
- `cryptography>=42.0` + `reportlab>=4.1` + `mammoth` в зависимостях

**Тесты:**
- +50 новых backend-тестов (`test_v17_fixes.py`): верификация токенов, шифрование, экспорт PDF/TXT, soft-delete, restore, email enumeration, OpenAPI
- Обновлены тесты soft-delete (6 тестов) и email enumeration (3 теста)
- Исправлен баг: `session.refresh(resume)` в `restore_resume()` для предотвращения MissingGreenlet
- Итого: **516 backend-тестов passed** (было 466), **487 frontend-тестов**

### v1.6.0 (Март 2026) — QA: 43 дефекта исправлено

**Безопасность (7 исправлений):**
- Swagger UI и ReDoc отключены в production (SEC-003 / LIVE-011)
- SECRET_KEY валидация при запуске — отказ старта с placeholder-ключом (SEC-002)
- Rate limiting через slowapi: login 5/min, register 3/min, rewrite 10/hour (SEC-005 / LIVE-012)
- Path traversal protection в FileStorage через `.resolve()` + prefix check (SEC-006)
- XSS: DOMPurify.sanitize() на всех 4 dangerouslySetInnerHTML (SEC-007 / UI-001)
- Docker-порты привязаны к 127.0.0.1 вместо 0.0.0.0 (SEC-010 / ARCH-001)
- RabbitMQ credentials через env vars вместо guest/guest (SEC-011 / ARCH-002)

**Backend API (8 исправлений):**
- Counter оптимизаций инкрементируется только при COMPLETED (API-001 / LIVE-003)
- Пустое резюме блокируется с ValueError до отправки в LLM (API-002)
- Health check доступен по /health и /api/v1/health (API-005 / LIVE-015)
- Content-Length в DOCX-экспорте для прогресса скачивания (API-006)
- TariffLimitExceeded передаёт used/limit пользователю (API-008)
- Маршрут /history перед /{task_id}/* для корректного роутинга (API-009)
- Email enumeration предотвращён — единое сообщение при регистрации (API-010 / LIVE-013)
- Расширенные prompt injection паттерны (16 новых) + Unicode NFKC нормализация (API-011)

**Frontend (9 исправлений):**
- Match Score breakdown — реальные компоненты от API вместо фейковых формул (UI-002 / LIVE-009)
- Подтверждение пароля при регистрации (UI-003)
- Auto-refresh token при 401 с retry оригинального запроса (UI-005)
- alert() заменён на state-based UI notification (UI-006)
- Polling с maxRetries (60 × 3с = 3мин) вместо бесконечного (UI-008)
- ErrorBoundary оборачивает все routes с fallback UI (UI-010)
- EditorPage redirect при пустых данных → /app/upload (UI-012)
- Modal закрывается по Escape и кнопке X (LIVE-001)
- Responsive tab labels на мобильном (LIVE-010)

**UX/UI:**
- Email overflow fix в профиле (LIVE-007)
- Зелёные галочки только при реальной доступности провайдера (LIVE-004)
- LLM error message «all» заменён на человекочитаемое сообщение (LIVE-006)
- Дубликат API метода selectSearchVacancy → @deprecated delegate (ARCH-012)
- get_settings() кэшируется через @lru_cache (AUTH-008 / ARCH-004)
- Файлы удаляются при удалении аккаунта — ФЗ-152 (AUTH-001)

**Инфраструктура:**
- slowapi==0.1.9 + Redis storage для rate limiting
- dompurify + @types/dompurify для XSS-защиты
- calculate_match_score_detailed() в scoring.py для компонентного скоринга

**Тесты:**
- +tests/test_qa_fixes.py: email enum, LLM messages, tariff details, 16 sanitize patterns, match score
- +tests/test_core/test_storage.py: path traversal read/delete blocked
- +frontend/src/test/qa-fixes.test.tsx: ErrorBoundary, auth confirm, API, security, tabs
- QA отчёты обновлены: 43/71 дефектов ✅ FIXED, 28 → Phase 2

### v1.5.0 (Март 2026)

**Новые возможности:**
- Страница «Справка» — быстрый старт, pipeline, FAQ (12 вопросов), тарифы, контакты
- Навигационная ссылка «Справка» в боковом меню
- Выбор формата скачивания: PDF / DOCX / TXT с выпадающим меню
- Форматированное отображение текста резюме (заголовки ALL CAPS, буллеты)
- Подсветка различий: зелёные (добавлено) / красные (убрано) слова на странице результатов
- Полные данные вакансии из hh.ru API: `GET /vacancies/hh/{hh_id}` — зарплата, описание, навыки
- Расширенные списки моделей: OpenAI (10), Anthropic (7), OpenRouter (16)
- Человекочитаемые ошибки LLM на странице обработки

**Исправления:**
- Смена пароля корректно разлогинивает + редирект на /auth с сообщением
- Удаление резюме из текста (без файла) больше не вызывает ошибку `file_path`
- Иконка камеры на аватаре не обрезается (restructured DOM)
- Email и бейдж «Подтверждён» не наложены друг на друга (paddingRight + flexShrink)
- Адаптивная сетка профиля `auto-fit minmax(250px, 1fr)`
- Кнопка «Настроить ключи» всегда видна при ошибках LLM

**Тесты:**
- +62 новых frontend-теста (v5 fixes): все 10 изменений покрыты
- +17 новых backend-тестов: `get_hh_vacancy_detail`, `delete_resume` guard, schemas
- Обновлены 2 старых теста для нового текста success-сообщения
- Vitest config: `pool: 'forks'` для надёжной изоляции тестов
- Итого: **480 frontend-тестов** (было 428), **570 backend-тестов** (было 553)

### v1.4.0 (Март 2026)

**Новые возможности:**
- Встроенный PDF-просмотрщик на странице детали резюме (`ResumeDetailPage`)
- Скачивание оригинального файла резюме для всех статусов (не только optimized)
- Новый API-метод `downloadResumeFile(id)` — GET `/resumes/{id}/file`
- Диалог подтверждения перед оптимизацией с навигацией на выбор вакансии
- Пагинация результатов поиска вакансий на hh.ru (10 результатов на страницу)
- Передача `resumeId` через URL query params при переходе к выбору вакансии
- Модель AI по умолчанию из настроек пользователя (`localStorage ai_settings`)
- Fallback-подмодели для OpenAI / Anthropic / OpenRouter при недоступности сервера

**Исправления:**
- Кнопка «Оптимизировать» теперь доступна для всех статусов резюме
- Устранено наложение аватара на текст email/имени в настройках профиля
- Исправлена передача `resumeId` в WizardContext при переходе со страницы резюме
- Исправлена ошибка «Не удалось загрузить список моделей» при недоступности API

**Тесты:**
- +62 новых теста (v3 fixes): ResumeDetailPage, ResumesPage, VacancyPage, ModelsPage, ProcessingPage, SettingsProfilePage, API, интеграция, edge-cases
- Обновлены 4 старых теста для соответствия новому поведению
- Итого: **428 frontend-тестов** (было 366), **964 тестов всего** (было 902)

### v1.3.0 (Март 2026)

- Исправлено 12 frontend-багов (v2 fixes)
- 366 frontend-тестов, 902 тестов всего
- 3 CI/CD pipeline зелёные

---

**ResumeCraft** — AI-оптимизация резюме для российского рынка труда

[О проекте](#1-о-проекте) · [Быстрый старт](#14-установка-и-запуск) · [Тестирование](#17-тестирование) · [Docker](#16-docker) · [Лицензия](#20-лицензия)


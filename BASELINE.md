# ResumeCraft — Описание MVP (Baseline)

> **Документ:** BASELINE.md  
> **Версия:** 1.1  
> **Дата:** Февраль 2026  
> **Проект:** ResumeCraft — AI-реврайтер резюме для российского рынка труда  

---

## Содержание

1. [Введение и цели MVP](#1-введение-и-цели-mvp)
2. [Определение MVP](#2-определение-mvp)
3. [Функциональные требования MVP](#3-функциональные-требования-mvp)
4. [Нефункциональные требования](#4-нефункциональные-требования)
5. [Пользовательские истории (User Stories)](#5-пользовательские-истории-user-stories)
6. [Архитектура MVP](#6-архитектура-mvp)
7. [Технический стек MVP](#7-технический-стек-mvp)
8. [Схема данных MVP](#8-схема-данных-mvp)
9. [API-спецификация MVP](#9-api-спецификация-mvp)
10. [AI/ML Pipeline MVP](#10-aiml-pipeline-mvp)
11. [Интерфейс MVP — Streamlit Demo](#11-интерфейс-mvp--streamlit-demo)
12. [Интеграция с hh.ru API — MVP scope](#12-интеграция-с-hhru-api--mvp-scope)
13. [Безопасность MVP](#13-безопасность-mvp)
14. [Тестирование MVP](#14-тестирование-mvp)
15. [Инфраструктура и деплой MVP](#15-инфраструктура-и-деплой-mvp)
16. [Критерии приёмки MVP (Definition of Done)](#16-критерии-приёмки-mvp-definition-of-done)
17. [Метрики успеха MVP](#17-метрики-успеха-mvp)
18. [Ресурсы и сроки](#18-ресурсы-и-сроки)
19. [Управление рисками](#19-управление-рисками)
20. [Границы MVP (In/Out of Scope)](#20-границы-mvp-inout-of-scope)
21. [Roadmap после MVP](#21-roadmap-после-mvp)
22. [Приложения](#22-приложения)

---

## 1. Введение и цели MVP

### 1.1. Назначение документа

Настоящий документ определяет **минимально жизнеспособный продукт (Minimum Viable Product, MVP)** платформы ResumeCraft — AI-сервиса для оптимизации резюме под вакансии российского рынка труда. Документ фиксирует:

- Функциональный объём первой релизной версии
- Технические требования и архитектурные решения
- Критерии приёмки и метрики успеха
- Временные рамки и ресурсы
- Границы MVP — что включено, а что отложено на последующие фазы

### 1.2. Цели MVP

| Цель | Описание | Измеримый результат |
|------|----------|---------------------|
| **Валидация ценности** | Подтвердить, что AI-оптимизация резюме приносит измеримую пользу | Match Score +20%+ для 80% тестовых резюме |
| **Демонстрация технологии** | Показать работоспособность полного pipeline: upload → parse → match → rewrite → export | End-to-end pipeline за < 60 секунд |
| **Защита проекта** | Обеспечить функциональный прототип для академической защиты | Работающее приложение + Streamlit demo |
| **Сбор обратной связи** | Получить фидбэк от реальных пользователей (тестовая группа) | 20+ тестирований с оценкой NPS |
| **Техническая база** | Создать архитектурный фундамент для масштабирования | Модульная architecture, 70%+ test coverage |

### 1.3. Принципы MVP

1. **Работающий продукт важнее идеального** — доставить core value (AI-оптимизация) как можно быстрее
2. **Минимум фронтенда, максимум бэкенда** — Streamlit для демо, все усилия на backend и AI pipeline
3. **Один happy path** — сфокусироваться на основном пользовательском сценарии: Upload → Vacancy → Rewrite → Download
4. **Мультимодельность с первого дня** — минимум 2 LLM-провайдера (GigaChat + Groq) для снижения рисков
5. **Тестируемость** — каждый компонент покрыт тестами, CI/CD с первого коммита

---

## 2. Определение MVP

### 2.1. Формулировка ценностного предложения MVP

> ResumeCraft MVP позволяет соискателю загрузить своё резюме (PDF/DOCX), указать целевую вакансию (из hh.ru или вручную), и за 10–30 секунд получить AI-оптимизированную версию резюме с Match Score, ATS-рейтингом и возможностью скачать результат в формате DOCX.

### 2.2. Формула MVP

```
MVP = Upload Resume + Select Vacancy + AI Rewrite + Match Score + Download Result
```

### 2.3. Что НЕ входит в MVP

Подробные границы — в разделе [20. Границы MVP](#20-границы-mvp-inout-of-scope). Кратко:

- ❌ React SPA (используется Streamlit)
- ❌ OAuth с hh.ru (используется анонимный поиск вакансий)
- ❌ Платёжная система (ЮKassa)
- ❌ 2FA и расширенная безопасность
- ❌ Экспорт PDF с шаблонами (только DOCX)
- ❌ Публикация на hh.ru
- ❌ Мобильная адаптация
- ❌ History / Dashboard (полный)

---

## 3. Функциональные требования MVP

### 3.1. Модуль аутентификации (Auth)

| ID | Требование | Приоритет | Описание |
|----|-----------|-----------|----------|
| AUTH-01 | Регистрация по email | Must | Email + пароль, валидация формата |
| AUTH-02 | Вход по email | Must | Email + пароль → JWT-токен |
| AUTH-03 | JWT-аутентификация | Must | Access token (30 мин) + Refresh token (30 дней) |
| AUTH-04 | Хэширование паролей | Must | bcrypt, work factor 12 |
| AUTH-05 | Защита эндпоинтов | Must | Все /api/v1/* (кроме auth) требуют Bearer token |
| AUTH-06 | Выход | Should | Инвалидация refresh token |

**Не входит в MVP:**
- Подтверждение email (AUTH-07) — отложено на фазу 2
- OAuth 2.0 с hh.ru (AUTH-08) — отложено на фазу 2
- 2FA (AUTH-09) — отложено на фазу 2
- Регистрация по телефону (AUTH-10) — отложено

### 3.2. Модуль резюме (Resumes)

| ID | Требование | Приоритет | Описание |
|----|-----------|-----------|----------|
| RES-01 | Загрузка PDF | Must | Принять PDF ≤ 10 МБ, сохранить в /data/uploads |
| RES-02 | Загрузка DOCX | Must | Принять DOCX ≤ 10 МБ, сохранить в /data/uploads |
| RES-03 | Извлечение текста из PDF | Must | PyMuPDF → raw text |
| RES-04 | Извлечение текста из DOCX | Must | python-docx → raw text |
| RES-05 | LLM-структуризация | Must | Отправить raw text в LLM → structured JSON (имя, опыт, навыки) |
| RES-06 | Сохранение в БД | Must | User_id, file_path, raw_text, parsed_data (JSONB), embedding |
| RES-07 | Список резюме | Must | GET /api/v1/resumes → список резюме пользователя |
| RES-08 | Детали резюме | Must | GET /api/v1/resumes/{id} → полные данные |
| RES-09 | Удаление резюме | Should | DELETE /api/v1/resumes/{id} → удалить файл + запись |
| RES-10 | Валидация формата | Must | Проверка расширения и magic bytes, отклонение невалидных |
| RES-11 | OCR fallback | Could | pytesseract для сканированных PDF (если основной парсинг пуст) |

### 3.3. Модуль вакансий (Vacancies)

| ID | Требование | Приоритет | Описание |
|----|-----------|-----------|----------|
| VAC-01 | Поиск на hh.ru | Must | GET /api/v1/vacancies/search → проксирование hh.ru API |
| VAC-02 | Импорт по URL | Must | POST /api/v1/vacancies/from-url → парсинг вакансии hh.ru |
| VAC-03 | Ручной ввод | Must | POST /api/v1/vacancies/manual → описание + требования |
| VAC-04 | Извлечение требований | Must | Парсинг описания вакансии → структурированные requirements |
| VAC-05 | Сохранение в БД | Must | Vacancy + embedding |
| VAC-06 | Детали вакансии | Should | GET /api/v1/vacancies/{id} |

### 3.4. Модуль AI-оптимизации (Rewriter)

| ID | Требование | Приоритет | Описание |
|----|-----------|-----------|----------|
| REW-01 | Запуск оптимизации | Must | POST /api/v1/rewrite → Celery task |
| REW-02 | Выбор модели | Must | Параметр model: gigachat-pro / llama-3 |
| REW-03 | GigaChat Pro интеграция | Must | API-вызов GigaChat Pro для оптимизации |
| REW-04 | Llama 3 (Groq) интеграция | Must | API-вызов Groq для бесплатной оптимизации |
| REW-05 | Статус задачи | Must | GET /api/v1/rewrite/{task_id}/status → polling |
| REW-06 | Результат оптимизации | Must | GET /api/v1/rewrite/{task_id}/result → rewritten text |
| REW-07 | Match Score | Must | Расчёт Match Score до и после оптимизации (0–100%) |
| REW-08 | ATS-рейтинг | Should | Оценка ATS-совместимости (A+ – F) |
| REW-09 | Список изменений | Must | Diff: добавленные/удалённые фрагменты, ключевые слова |
| REW-10 | Сохранение истории | Must | Запись в rewrite_history (resume_id, vacancy_id, результат) |
| REW-11 | GPT-4o интеграция | Could | Дополнительная модель для тестирования |

### 3.5. Модуль экспорта (Export)

| ID | Требование | Приоритет | Описание |
|----|-----------|-----------|----------|
| EXP-01 | Экспорт DOCX | Must | Генерация DOCX из оптимизированного текста |
| EXP-02 | Скачивание файла | Must | GET → binary file download |
| EXP-03 | Экспорт PDF | Could | Генерация PDF (отложено, если сложно) |

---

## 4. Нефункциональные требования

### 4.1. Производительность

| Требование | Значение | Обоснование |
|-----------|----------|-------------|
| Время загрузки резюме | < 3 секунды | UX: пользователь не должен ждать |
| Время парсинга PDF/DOCX | < 5 секунд | Включая LLM-структуризацию |
| Время оптимизации (Llama 3) | < 15 секунд | Groq обеспечивает быстрый inference |
| Время оптимизации (GigaChat) | < 30 секунд | GigaChat Pro медленнее, но качественнее |
| Время экспорта DOCX | < 3 секунды | Генерация файла |
| API response time (CRUD) | < 200 мс | Стандартные операции чтения/записи |
| Concurrent users | 50 | MVP не предполагает высокую нагрузку |

### 4.2. Надёжность

| Требование | Значение |
|-----------|----------|
| Uptime | 95% (допустимо для MVP) |
| Data durability | PostgreSQL + Docker volumes с persistent storage |
| Error handling | Graceful degradation при недоступности LLM API |
| LLM fallback | Если GigaChat недоступен → fallback на Llama 3 (Groq) |

### 4.3. Безопасность

| Требование | Значение |
|-----------|----------|
| Аутентификация | JWT (HS256) |
| Хранение паролей | bcrypt (work factor 12) |
| HTTPS | Обязательно в production |
| Валидация входных данных | Pydantic schemas на всех эндпоинтах |
| SQL Injection | SQLAlchemy ORM (parameterized queries) |
| File upload validation | Проверка расширения + magic bytes + размер |

### 4.4. Качество кода

| Требование | Значение |
|-----------|----------|
| Test coverage | 70%+ |
| Type hints | 100% public API |
| Linter | Ruff (zero warnings) |
| Type checker | mypy --strict (zero errors) |
| Code style | PEP 8, max line length 99 |
| Docstrings | Google-style для всех public функций |

---

## 5. Пользовательские истории (User Stories)

### 5.1. Epic: Аутентификация

**US-01: Регистрация**
```
Как новый пользователь,
Я хочу зарегистрироваться по email и паролю,
Чтобы получить доступ к функциям сервиса.

Критерии приёмки:
- POST /api/v1/auth/register принимает email + password
- Пароль: минимум 8 символов, 1 заглавная, 1 цифра
- При дубликате email → 409 Conflict
- При успехе → 201 Created + JWT tokens
- Пароль хранится как bcrypt hash
```

**US-02: Вход**
```
Как зарегистрированный пользователь,
Я хочу войти по email и паролю,
Чтобы получить доступ к своим данным.

Критерии приёмки:
- POST /api/v1/auth/login принимает email + password
- При неверном пароле → 401 Unauthorized
- При успехе → 200 OK + access_token + refresh_token
- Access token expire: 30 минут
- Refresh token expire: 30 дней
```

**US-03: Обновление токена**
```
Как авторизованный пользователь с истёкшим access token,
Я хочу обновить токен через refresh token,
Чтобы не входить заново.

Критерии приёмки:
- POST /api/v1/auth/refresh принимает refresh_token
- Возвращает новый access_token
- Старый refresh_token инвалидируется
```

### 5.2. Epic: Загрузка и парсинг резюме

**US-04: Загрузка PDF**
```
Как авторизованный пользователь,
Я хочу загрузить своё резюме в формате PDF,
Чтобы система могла его проанализировать.

Критерии приёмки:
- POST /api/v1/resumes/upload принимает multipart/form-data
- Валидация: PDF, ≤ 10 МБ
- Файл сохраняется в /data/uploads
- Текст извлекается через PyMuPDF
- Структурированные данные (имя, опыт, навыки) сохраняются в JSONB
- Эмбеддинг генерируется и сохраняется в VECTOR
- Возвращает 201 Created + resume_id
```

**US-05: Загрузка DOCX**
```
Как авторизованный пользователь,
Я хочу загрузить своё резюме в формате DOCX,
Чтобы система могла его проанализировать.

Критерии приёмки:
- Аналогично US-04, но парсинг через python-docx
- Извлекаются параграфы и таблицы
```

**US-06: Просмотр загруженных резюме**
```
Как авторизованный пользователь,
Я хочу видеть список своих загруженных резюме,
Чтобы выбрать нужное для оптимизации.

Критерии приёмки:
- GET /api/v1/resumes → список с пагинацией
- Каждый элемент: id, title, status, created_at, file_format
- Только резюме текущего пользователя
```

### 5.3. Epic: Выбор вакансии

**US-07: Поиск вакансий на hh.ru**
```
Как авторизованный пользователь,
Я хочу найти вакансию на hh.ru прямо из ResumeCraft,
Чтобы указать, под какую вакансию оптимизировать резюме.

Критерии приёмки:
- GET /api/v1/vacancies/search?text=...&area=...
- Проксирование запроса к hh.ru API
- Возвращает: title, company, salary, experience, city
- Пагинация (20 элементов на странице)
```

**US-08: Импорт вакансии по URL**
```
Как авторизованный пользователь,
Я хочу вставить ссылку на вакансию hh.ru,
Чтобы система автоматически извлекла требования.

Критерии приёмки:
- POST /api/v1/vacancies/from-url с body: {url: "https://hh.ru/vacancy/12345"}
- Парсинг: извлечение vacancy_id из URL
- Запрос к GET /vacancies/{id} hh.ru API
- Сохранение: title, description, key_skills, requirements
- Возвращает 201 Created + vacancy_id
```

**US-09: Ручной ввод вакансии**
```
Как авторизованный пользователь,
Я хочу описать вакансию вручную,
Чтобы оптимизировать резюме даже без ссылки на hh.ru.

Критерии приёмки:
- POST /api/v1/vacancies/manual
- Поля: title (обязательно), description (обязательно), key_skills (опционально)
- Сохранение в БД + генерация эмбеддинга
```

### 5.4. Epic: AI-оптимизация

**US-10: Запуск оптимизации с GigaChat Pro**
```
Как авторизованный пользователь,
Я хочу оптимизировать своё резюме под выбранную вакансию через GigaChat Pro,
Чтобы повысить шансы на приглашение.

Критерии приёмки:
- POST /api/v1/rewrite с body: {resume_id, vacancy_id, model: "gigachat-pro"}
- Возвращает 202 Accepted + task_id
- Celery task: загружает данные → формирует промпт → вызывает GigaChat → сохраняет результат
- Промпт содержит: оригинальный текст, описание вакансии, ключевые навыки
- Результат: оптимизированный текст + Match Score + ATS-рейтинг
```

**US-11: Запуск оптимизации с Llama 3 (Groq)**
```
Как авторизованный пользователь,
Я хочу оптимизировать резюме через бесплатную модель Llama 3,
Чтобы попробовать сервис без оплаты.

Критерии приёмки:
- model: "llama-3" → Groq API (бесплатный tier)
- Остальное аналогично US-10
```

**US-12: Отслеживание статуса оптимизации**
```
Как авторизованный пользователь,
Я хочу видеть текущий статус обработки,
Чтобы понимать, сколько ждать.

Критерии приёмки:
- GET /api/v1/rewrite/{task_id}/status
- Статусы: pending → processing → completed / failed
- processing включает: step (1–4), progress (0–100%)
- completed включает: processing_time_ms
```

**US-13: Получение результата оптимизации**
```
Как авторизованный пользователь,
Я хочу увидеть результат: оптимизированный текст, Match Score и изменения,
Чтобы оценить качество и решить, использовать ли его.

Критерии приёмки:
- GET /api/v1/rewrite/{task_id}/result
- Ответ содержит:
  - original_text: str
  - rewritten_text: str
  - match_score_before: float (0–100)
  - match_score_after: float (0–100)
  - ats_rating: str (A+, A, B+, B, C+, C, D+, D, F)
  - keywords_added: list[str]
  - processing_time_ms: int
  - model_name: str
```

### 5.5. Epic: Экспорт

**US-14: Скачивание DOCX**
```
Как авторизованный пользователь,
Я хочу скачать оптимизированное резюме в формате DOCX,
Чтобы отправить его работодателю.

Критерии приёмки:
- POST /api/v1/export/docx с body: {rewrite_id}
- Генерация DOCX-файла (python-docx)
- Структура: Заголовок → О себе → Опыт → Образование → Навыки
- Возвращает binary file (application/vnd.openxmlformats-officedocument.wordprocessingml.document)
```

---

## 6. Архитектура MVP

### 6.1. Компоненты MVP

```
┌──────────────────────────────────────────────────────────┐
│                    Streamlit Demo UI                       │
│              (streamlit_app/app.py)                        │
│       File Upload → Vacancy Input → Results Display       │
└──────────────────────┬────────────────────────────────────┘
                       │ HTTP requests
┌──────────────────────┴────────────────────────────────────┐
│              FastAPI Application (async)                    │
│                                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
│  │   Auth   │ │ Resumes  │ │Vacancies │ │   Rewriter   │ │
│  │  Module  │ │  Module  │ │  Module  │ │   Module     │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘ │
│       │            │            │               │          │
└───────┼────────────┼────────────┼───────────────┼──────────┘
        │            │            │               │
   ┌────┴──────┐ ┌───┴────┐ ┌────┴────┐   ┌──────┴────────┐
   │PostgreSQL │ │Local FS│ │ hh.ru   │   │ Redis/Celery  │
   │+ pgvector │ │(Docker)│ │  API    │   │   Workers     │
   └───────────┘ └────────┘ └─────────┘   └──────┬────────┘
                                                  │
                                           ┌──────┴────────┐
                                           │   LLM APIs    │
                                           │ GigaChat Pro  │
                                           │ Llama 3 (Groq)│
                                           └───────────────┘
```

### 6.2. Принципы архитектуры MVP

1. **Модульность** — каждый домен (auth, resumes, vacancies, rewriter) изолирован в собственном пакете
2. **Async-first** — все I/O операции через async/await
3. **Dependency Injection** — FastAPI Depends() для БД, Redis, LLM-клиента
4. **Configuration as Code** — Pydantic BaseSettings из .env файла
5. **API-first** — Streamlit вызывает те же API-эндпоинты, которые будут использоваться React SPA

### 6.3. Потоки данных

**Поток 1: Загрузка и парсинг резюме**
```
Streamlit → POST /resumes/upload (multipart)
  → FastAPI: validate (size, format)
  → /data/uploads: save file
  → PyMuPDF / python-docx: extract text
  → LLM (GigaChat): structure text → JSON
  → sentence-transformers: generate embedding
  → PostgreSQL: save (raw_text, parsed_data, embedding)
  → Response: {resume_id, title, status}
```

**Поток 2: Выбор вакансии (hh.ru)**
```
Streamlit → GET /vacancies/search?text=...
  → FastAPI → httpx → hh.ru API
  → Response: [{title, company, salary, url}]

Streamlit → POST /vacancies/from-url
  → FastAPI → httpx → hh.ru API /vacancies/{id}
  → Extract: description, key_skills
  → Generate embedding
  → PostgreSQL: save
  → Response: {vacancy_id, title, company}
```

**Поток 3: AI-оптимизация**
```
Streamlit → POST /rewrite {resume_id, vacancy_id, model}
  → FastAPI: validate → create Celery task
  → Response: {task_id}

[Celery Worker]
  → Load resume parsed_data
  → Load vacancy requirements
  → Build prompt (system + user + examples)
  → Call LLM API (GigaChat / Groq)
  → Parse LLM response (Pydantic validation)
  → Calculate Match Score (cosine similarity + keyword match)
  → Calculate ATS rating
  → Save to rewrite_history
  → Mark task as completed

Streamlit → GET /rewrite/{task_id}/status (polling, every 2s)
Streamlit → GET /rewrite/{task_id}/result
```

---

## 7. Технический стек MVP

### 7.1. Обоснование выбора технологий

| Технология | Альтернативы рассмотренные | Причина выбора |
|-----------|---------------------------|----------------|
| **FastAPI** | Flask, Django REST | Async I/O (критично для LLM), автодокументация, Pydantic |
| **PostgreSQL + pgvector** | MongoDB, Qdrant, Pinecone | Единая БД для реляционных и векторных данных, зрелость |
| **Celery + RabbitMQ + Redis** | FastAPI BackgroundTasks, Dramatiq | Battle-tested для long-running tasks, RabbitMQ \u2014 брокер, Redis \u2014 result backend, Flower мониторинг |
| **GigaChat** | YandexGPT | #1 на MERA benchmark для русского, OpenAI-compatible SDK |
| **Llama 3 (Groq)** | Ollama, Together.ai | 14 400 бесплатных запросов/день, быстрый inference |
| **Local FS** | MinIO, AWS S3 | Docker volume /data/uploads. Для MVP достаточно, миграция на S3 в продакшене |
| **PyMuPDF** | pdfplumber, PDFMiner | Скорость: 10x быстрее альтернатив, качество извлечения |
| **Streamlit** | Gradio, Flask templates | Минимум кода для функционального UI, Python-only |
| **Docker Compose** | Kubernetes, manual setup | Простота: одна команда для всего стека |

### 7.2. Версии зависимостей (pinned для MVP)

```
# Core
python = "3.11"
fastapi = "0.115.*"
uvicorn = {extras = ["standard"], version = "0.30.*"}
pydantic = "2.9.*"
pydantic-settings = "2.5.*"

# Database
sqlalchemy = {extras = ["asyncio"], version = "2.0.*"}
asyncpg = "0.29.*"
alembic = "1.13.*"
pgvector = "0.3.*"

# Task Queue
celery = {extras = ["redis"], version = "5.4.*"}
redis = "5.1.*"
flower = "2.0.*"

# Storage
# Local filesystem с Docker volume (для MVP, миграция на MinIO/S3 в продакшене)
aiofiles = "24.*"

# Auth
pyjwt = "2.9.*"
passlib = {extras = ["bcrypt"], version = "1.7.*"}
python-multipart = "0.0.9"

# HTTP
httpx = "0.27.*"

# Document Parsing
pymupdf = "1.24.*"
python-docx = "1.1.*"

# AI/ML
openai = "1.40.*"           # Groq uses OpenAI-compatible SDK
gigachat = "0.1.*"          # GigaChat SDK
sentence-transformers = "3.0.*"

# Demo UI
streamlit = "1.38.*"

# Testing
pytest = "8.3.*"
pytest-asyncio = "0.23.*"
pytest-cov = "5.0.*"
httpx = "0.27.*"            # TestClient uses httpx

# Quality
ruff = "0.6.*"
mypy = "1.11.*"
```

---

## 8. Схема данных MVP

### 8.1. Миграция 001: Initial Schema

```sql
-- 001_initial_schema.sql

-- Расширения
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Типы
CREATE TYPE user_plan AS ENUM ('free', 'standard', 'pro');
CREATE TYPE resume_status AS ENUM ('draft', 'processing', 'optimized', 'error');
CREATE TYPE rewrite_status AS ENUM ('pending', 'processing', 'completed', 'failed');

-- Таблица пользователей
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    plan user_plan DEFAULT 'free' NOT NULL,
    optimizations_used INTEGER DEFAULT 0 NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Таблица резюме
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Таблица вакансий
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Таблица истории оптимизаций
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
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

### 8.2. Pydantic-модели MVP

```python
# src/app/resumes/schemas.py

from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

class ResumeUploadResponse(BaseModel):
    id: UUID
    title: str | None
    file_format: str
    file_size_bytes: int
    status: str
    created_at: datetime

class ResumeDetail(BaseModel):
    id: UUID
    title: str | None
    file_format: str
    file_size_bytes: int
    raw_text: str | None
    parsed_data: dict | None
    status: str
    created_at: datetime
    updated_at: datetime

class ParsedResume(BaseModel):
    """Результат LLM-структуризации резюме."""
    full_name: str | None = None
    position: str | None = None
    summary: str | None = None
    experience: list[dict] = Field(default_factory=list)
    education: list[dict] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    contacts: dict = Field(default_factory=dict)
```

```python
# src/app/rewriter/schemas.py

class RewriteRequest(BaseModel):
    resume_id: UUID
    vacancy_id: UUID
    model: str = "gigachat-pro"  # gigachat-pro | llama-3

class RewriteTaskStatus(BaseModel):
    task_id: str
    status: str  # pending | processing | completed | failed
    step: int | None = None  # 1-4
    progress: float | None = None  # 0-100
    processing_time_ms: int | None = None

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
    created_at: datetime
```

---

## 9. API-спецификация MVP

### 9.1. Полный список эндпоинтов MVP

```
BASE_URL: /api/v1

Auth:
  POST   /auth/register          → 201 Created
  POST   /auth/login             → 200 OK
  POST   /auth/refresh           → 200 OK

Resumes:
  POST   /resumes/upload         → 201 Created
  GET    /resumes                → 200 OK (list)
  GET    /resumes/{id}           → 200 OK
  DELETE /resumes/{id}           → 204 No Content

Vacancies:
  GET    /vacancies/search       → 200 OK (list from hh.ru)
  POST   /vacancies/from-url     → 201 Created
  POST   /vacancies/manual       → 201 Created
  GET    /vacancies/{id}         → 200 OK

Rewrite:
  POST   /rewrite                → 202 Accepted (task_id)
  GET    /rewrite/{task_id}/status → 200 OK
  GET    /rewrite/{task_id}/result → 200 OK

Export:
  POST   /export/docx            → 200 OK (binary)

Health:
  GET    /health                 → 200 OK
```

### 9.2. Примеры запросов и ответов

**Регистрация:**
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "anna@example.com",
  "password": "SecurePass123"
}

---

201 Created
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Загрузка резюме:**
```http
POST /api/v1/resumes/upload
Authorization: Bearer eyJhbGci...
Content-Type: multipart/form-data

file: resume.pdf (binary)

---

201 Created
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Anna Kozlova - Digital Marketing Manager",
  "file_format": "pdf",
  "file_size_bytes": 156234,
  "status": "ready",
  "created_at": "2025-07-15T10:30:00Z"
}
```

**Поиск вакансий:**
```http
GET /api/v1/vacancies/search?text=маркетолог&area=1&per_page=5
Authorization: Bearer eyJhbGci...

---

200 OK
{
  "items": [
    {
      "hh_id": "12345678",
      "title": "Digital Marketing Manager",
      "company": "Яндекс",
      "salary_from": 150000,
      "salary_to": 250000,
      "experience": "3–6 лет",
      "city": "Москва",
      "url": "https://hh.ru/vacancy/12345678"
    }
  ],
  "found": 1234,
  "page": 0,
  "per_page": 5
}
```

**Запуск оптимизации:**
```http
POST /api/v1/rewrite
Authorization: Bearer eyJhbGci...
Content-Type: application/json

{
  "resume_id": "550e8400-...",
  "vacancy_id": "660e8400-...",
  "model": "gigachat-pro"
}

---

202 Accepted
{
  "task_id": "celery-task-abc123"
}
```

**Статус оптимизации:**
```http
GET /api/v1/rewrite/celery-task-abc123/status
Authorization: Bearer eyJhbGci...

---

200 OK
{
  "task_id": "celery-task-abc123",
  "status": "processing",
  "step": 3,
  "progress": 72.5
}
```

**Результат оптимизации:**
```http
GET /api/v1/rewrite/celery-task-abc123/result
Authorization: Bearer eyJhbGci...

---

200 OK
{
  "id": "770e8400-...",
  "original_text": "Опытный маркетолог с большим опытом работы...",
  "rewritten_text": "Digital Marketing Manager с 5+ годами опыта в B2C ecommerce. Увеличила ROI рекламных кампаний на 180%...",
  "match_score_before": 47.2,
  "match_score_after": 89.1,
  "ats_rating": "A+",
  "keywords_added": ["performance marketing", "unit economics", "A/B testing", "attribution"],
  "model_name": "gigachat-pro",
  "processing_time_ms": 14320,
  "created_at": "2025-07-15T10:31:15Z"
}
```

---

## 10. AI/ML Pipeline MVP

### 10.1. Системный промпт для оптимизации

```python
REWRITE_SYSTEM_PROMPT = """Вы — эксперт по оптимизации резюме для российского рынка труда с 15-летним опытом в рекрутинге и HR.

Ваша задача — переработать текст резюме соискателя так, чтобы:
1. Максимально соответствовать требованиям целевой вакансии
2. Успешно проходить автоматические системы отбора (ATS)
3. Привлекать внимание рекрутера в первые 7 секунд просмотра

ПРАВИЛА:
- НЕ выдумывайте факты, достижения или опыт, которых нет в оригинале
- Перефразируйте существующий опыт, добавляя конкретные метрики где это уместно
- Используйте формулу: Действие + Результат + Метрика
- Замените расплывчатые формулировки на конкретные
- Добавьте ключевые слова из описания вакансии, если навык подтверждается опытом
- Сохраните русский язык (если оригинал на русском)
- Оптимальная длина резюме: 1–2 страницы A4

ФОРМАТ ОТВЕТА:
Верните JSON с полями:
- summary: профессиональное саммари (2–4 предложения)
- experience: массив объектов {position, company, period, achievements: [str]}
- education: массив объектов {institution, degree, specialization, year}
- skills: массив строк (ключевые навыки)
- keywords_added: массив строк (ключевые слова, добавленные из вакансии)
"""
```

### 10.2. Расчёт Match Score

Match Score рассчитывается как взвешенная комбинация четырёх компонентов:

```python
def calculate_match_score(
    resume_embedding: list[float],
    vacancy_embedding: list[float],
    resume_skills: list[str],
    vacancy_skills: list[str],
    resume_text: str,
    vacancy_text: str,
) -> float:
    """Расчёт Match Score (0–100).
    
    Компоненты (совпадают с UI — 12-results.html):
    - Совпадение ключевых слов — 40%
    - Уровень и релевантность опыта — 25%
    - Структура и оформление документа — 20%
    - Читаемость текста — 15%
    """
    
    # 1. Совпадение ключевых слов (40%)
    resume_tokens = set(normalize(resume_text))
    vacancy_tokens = set(normalize(vacancy_text))
    keyword_score = len(resume_tokens & vacancy_tokens) / max(len(vacancy_tokens), 1)
    
    # 2. Уровень и релевантность опыта (25%)
    # Комбинация: пересечение навыков + семантическая близость опыта
    resume_skills_set = set(s.lower() for s in resume_skills)
    vacancy_skills_set = set(s.lower() for s in vacancy_skills)
    skills_overlap = len(resume_skills_set & vacancy_skills_set) / max(len(vacancy_skills_set), 1)
    semantic_sim = cosine_similarity(resume_embedding, vacancy_embedding)
    experience_score = skills_overlap * 0.6 + semantic_sim * 0.4
    
    # 3. Структура и оформление документа (20%)
    structure_score = evaluate_structure(resume_text)
    
    # 4. Читаемость текста (15%)
    readability_score = evaluate_readability(resume_text)
    
    # Взвешенная комбинация
    match_score = (
        keyword_score * 0.40 +
        experience_score * 0.25 +
        structure_score * 0.20 +
        readability_score * 0.15
    ) * 100
    
    return round(min(max(match_score, 0), 100), 1)
```

### 10.3. ATS-рейтинг

```python
def calculate_ats_rating(match_score: float, structure_score: float) -> str:
    """Определение ATS-рейтинга на основе Match Score и структуры."""
    combined = match_score * 0.7 + structure_score * 100 * 0.3
    
    if combined >= 90: return "A+"
    if combined >= 80: return "A"
    if combined >= 70: return "B"
    if combined >= 60: return "C"
    if combined >= 50: return "D"
    return "F"
```

### 10.4. LLM-клиент (Strategy pattern)

```python
# src/app/ml/llm_client.py

from abc import ABC, abstractmethod

class BaseLLMClient(ABC):
    @abstractmethod
    async def complete(self, system: str, user: str) -> str:
        ...

class GigaChatClient(BaseLLMClient):
    async def complete(self, system: str, user: str) -> str:
        # GigaChat SDK
        ...

class GroqClient(BaseLLMClient):
    async def complete(self, system: str, user: str) -> str:
        # OpenAI-compatible SDK with Groq base_url
        ...

class LLMClientFactory:
    _clients = {
        "gigachat-pro": GigaChatClient,
        "llama-3": GroqClient,
    }
    
    @classmethod
    def create(cls, model: str) -> BaseLLMClient:
        client_cls = cls._clients.get(model)
        if not client_cls:
            raise ValueError(f"Unknown model: {model}")
        return client_cls()
```

---

## 11. Интерфейс MVP — Streamlit Demo

### 11.1. Экраны Streamlit

```
streamlit_app/
└── app.py
    │
    ├── Page 1: 🏠 Главная
    │   └── Описание проекта, ключевые возможности
    │
    ├── Page 2: 📄 Загрузка резюме
    │   ├── File uploader (PDF/DOCX, ≤ 10 МБ)
    │   ├── Отображение извлечённого текста
    │   └── Структурированные данные (имя, опыт, навыки)
    │
    ├── Page 3: 🎯 Выбор вакансии
    │   ├── Tab 1: Поиск на hh.ru (text input + search button)
    │   ├── Tab 2: URL вакансии (text input)
    │   └── Tab 3: Ручной ввод (text area)
    │
    ├── Page 4: 🤖 Оптимизация
    │   ├── Selectbox: выбор модели (GigaChat Pro / Llama 3)
    │   ├── Button: «Оптимизировать»
    │   ├── Progress bar + status messages
    │   └── Результат:
    │       ├── Match Score (before → after) с delta
    │       ├── ATS Rating (badge)
    │       ├── Diff: оригинал vs. оптимизированный (two columns)
    │       ├── Добавленные ключевые слова (tags)
    │       └── Время обработки
    │
    └── Page 5: 📥 Экспорт
        ├── Download button: DOCX
        └── Превью оптимизированного текста
```

### 11.2. Пример кода Streamlit

```python
# streamlit_app/app.py (simplified)

import streamlit as st
import httpx

API_BASE = "http://localhost:8000/api/v1"

st.set_page_config(page_title="ResumeCraft Demo", page_icon="📝", layout="wide")

st.title("📝 ResumeCraft — AI-оптимизатор резюме")

# Sidebar navigation
page = st.sidebar.radio("Навигация", [
    "🏠 Главная",
    "📄 Загрузка резюме",
    "🎯 Выбор вакансии",
    "🤖 Оптимизация",
    "📥 Экспорт",
])

if page == "📄 Загрузка резюме":
    st.header("Загрузка резюме")
    file = st.file_uploader("Выберите PDF или DOCX файл", type=["pdf", "docx"])
    
    if file and st.button("Загрузить"):
        with st.spinner("Загрузка и парсинг..."):
            response = httpx.post(
                f"{API_BASE}/resumes/upload",
                files={"file": (file.name, file.read(), file.type)},
                headers={"Authorization": f"Bearer {st.session_state.token}"},
            )
            if response.status_code == 201:
                data = response.json()
                st.success(f"Резюме загружено: {data['title']}")
                st.session_state.resume_id = data["id"]
                
                # Показать извлечённый текст
                detail = httpx.get(
                    f"{API_BASE}/resumes/{data['id']}",
                    headers={"Authorization": f"Bearer {st.session_state.token}"},
                ).json()
                
                with st.expander("Извлечённый текст"):
                    st.text(detail["raw_text"][:2000])
                
                if detail["parsed_data"]:
                    st.subheader("Структурированные данные")
                    st.json(detail["parsed_data"])
```

### 11.3. Зачем Streamlit для MVP

| Преимущество | Описание |
|-------------|----------|
| **Скорость разработки** | Полный UI за 1–2 дня (vs. 2–4 недели для React SPA) |
| **Python-only** | Нет необходимости в JS/TS специалисте |
| **Встроенные компоненты** | File uploader, progress bar, columns, charts — «из коробки» |
| **Ideal для demo** | Streamlit-приложения выглядят professional для презентации |
| **API-first** | Streamlit call те же эндпоинты, что и будущий React SPA → backend не переписывается |

---

## 12. Интеграция с hh.ru API — MVP scope

### 12.1. Используемые эндпоинты (MVP)

| Endpoint | Авторизация | Назначение в MVP |
|----------|-------------|------------------|
| `GET /vacancies` | Анонимный | Поиск вакансий по тексту и региону |
| `GET /vacancies/{id}` | Анонимный | Получение детального описания вакансии |
| `GET /dictionaries` | Анонимный | Справочники (регионы, опыт, занятость) |

### 12.2. Не используемые в MVP

- OAuth 2.0 авторизация соискателя (требует модерации приложения)
- `GET /resumes/mine` — чтение резюме с hh.ru
- `PUT /resumes/{id}` — публикация оптимизированного резюме на hh.ru

### 12.3. Реализация hh.ru клиента

```python
# src/app/vacancies/hh_client.py

import httpx
from pydantic import BaseModel

class HHVacancyShort(BaseModel):
    id: str
    title: str = field(alias="name")
    company: str | None = None
    salary_from: int | None = None
    salary_to: int | None = None
    experience: str | None = None
    city: str | None = None
    url: str = field(alias="alternate_url")

class HHClient:
    BASE_URL = "https://api.hh.ru"
    
    def __init__(self, user_agent: str):
        self.headers = {"User-Agent": user_agent}
    
    async def search_vacancies(
        self, text: str, area: int = 1, per_page: int = 20
    ) -> list[HHVacancyShort]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/vacancies",
                params={"text": text, "area": area, "per_page": per_page},
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()
            return [HHVacancyShort(**item) for item in data["items"]]
    
    async def get_vacancy(self, vacancy_id: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/vacancies/{vacancy_id}",
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()
```

### 12.4. Ограничения и fallback

- **Rate limiting:** hh.ru API может вернуть 429 при превышении лимита. Реализуем backoff с 3 retries.
- **Unavailability:** При недоступности hh.ru API пользователь всё равно может ввести вакансию вручную (VAC-03).
- **Parsing URL:** Регулярное выражение `r'hh\.ru/vacancy/(\d+)'` для извлечения vacancy_id из URL.

---

## 13. Безопасность MVP

### 13.1. Аутентификация

```python
# src/app/core/security.py

from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(user_id: str, secret: str, expires_minutes: int = 30) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=expires_minutes),
        "type": "access",
    }
    return jwt.encode(payload, secret, algorithm="HS256")

def create_refresh_token(user_id: str, secret: str, expires_days: int = 7) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(days=expires_days),
        "type": "refresh",
    }
    return jwt.encode(payload, secret, algorithm="HS256")
```

### 13.2. Валидация загружаемых файлов

```python
# src/app/resumes/service.py

ALLOWED_EXTENSIONS = {"pdf", "docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Magic bytes для валидации формата
MAGIC_BYTES = {
    "pdf": b"%PDF",
    "docx": b"PK\x03\x04",  # ZIP-based format
}

def validate_upload(file: UploadFile) -> None:
    # 1. Расширение
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"Unsupported format: {ext}")
    
    # 2. Размер
    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise ValidationError(f"File too large: {len(content)} bytes")
    
    # 3. Magic bytes
    expected = MAGIC_BYTES.get(ext)
    if expected and not content.startswith(expected):
        raise ValidationError("File content does not match extension")
    
    file.file.seek(0)  # Reset for further reading
```

### 13.3. Защита API

- **CORS:** Ограничение `allowed_origins` до фронтенд-домена и localhost
- **Rate Limiting:** Базовое ограничение через Redis (10 запросов/секунда на пользователя)
- **Input Validation:** Pydantic-схемы на всех эндпоинтах, SQLAlchemy (parameterized queries)
- **Secret Management:** Все секреты в .env (не в коде), .env в .gitignore

---

## 14. Тестирование MVP

### 14.1. Стратегия тестирования

```
┌─────────────────────────────────────┐
│         E2E Tests (Streamlit)       │  ← 5% (ручные)
├─────────────────────────────────────┤
│       Integration Tests (API)       │  ← 25%
├─────────────────────────────────────┤
│          Unit Tests (Logic)         │  ← 70%
└─────────────────────────────────────┘
```

### 14.2. Unit Tests

```python
# tests/test_ml/test_match_score.py

import pytest
from src.app.ml.scoring import calculate_match_score

class TestMatchScore:
    def test_perfect_match(self):
        """Резюме полностью соответствует вакансии → ~100%."""
        score = calculate_match_score(
            resume_skills=["Python", "FastAPI", "PostgreSQL"],
            vacancy_skills=["Python", "FastAPI", "PostgreSQL"],
            resume_embedding=[0.1] * 1536,
            vacancy_embedding=[0.1] * 1536,
            resume_text="Python FastAPI PostgreSQL developer",
            vacancy_text="Python FastAPI PostgreSQL developer",
        )
        assert score >= 90

    def test_no_match(self):
        """Резюме нерелевантно вакансии → < 30%."""
        score = calculate_match_score(
            resume_skills=["Excel", "1C"],
            vacancy_skills=["Python", "Docker", "Kubernetes"],
            resume_embedding=[0.1] * 1536,
            vacancy_embedding=[-0.1] * 1536,
            resume_text="бухгалтерия 1С отчётность",
            vacancy_text="Python Docker Kubernetes DevOps",
        )
        assert score < 30

    def test_partial_match(self):
        """Частичное совпадение → 40–70%."""
        score = calculate_match_score(
            resume_skills=["Python", "Django"],
            vacancy_skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
            resume_embedding=[0.1] * 1536,
            vacancy_embedding=[0.08] * 1536,
            resume_text="Python Django developer",
            vacancy_text="Python FastAPI PostgreSQL Docker developer",
        )
        assert 30 < score < 80
```

```python
# tests/test_resumes/test_parser.py

import pytest
from src.app.ml.resume_parser import ResumeParser

class TestResumeParser:
    def test_pdf_text_extraction(self, sample_pdf_path):
        """Извлечение текста из PDF."""
        parser = ResumeParser()
        text = parser._extract_pdf(sample_pdf_path)
        assert len(text) > 100
        assert "опыт" in text.lower() or "experience" in text.lower()

    def test_docx_text_extraction(self, sample_docx_path):
        """Извлечение текста из DOCX."""
        parser = ResumeParser()
        text = parser._extract_docx(sample_docx_path)
        assert len(text) > 100

    def test_file_validation_rejects_txt(self):
        """Отклонение файла с неподдерживаемым форматом."""
        with pytest.raises(ValidationError, match="Unsupported format"):
            validate_upload(MockUploadFile("resume.txt", b"text content"))

    def test_file_validation_rejects_oversized(self):
        """Отклонение файла > 10 МБ."""
        large_content = b"x" * (11 * 1024 * 1024)
        with pytest.raises(ValidationError, match="too large"):
            validate_upload(MockUploadFile("resume.pdf", b"%PDF" + large_content))
```

### 14.3. Integration Tests

```python
# tests/test_auth/test_auth_api.py

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
class TestAuthAPI:
    async def test_register_success(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "SecurePass123",
        })
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_register_duplicate_email(self, client: AsyncClient):
        await client.post("/api/v1/auth/register", json={
            "email": "dup@example.com", "password": "SecurePass123"
        })
        response = await client.post("/api/v1/auth/register", json={
            "email": "dup@example.com", "password": "AnotherPass456"
        })
        assert response.status_code == 409

    async def test_login_success(self, client: AsyncClient, registered_user):
        response = await client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "SecurePass123",
        })
        assert response.status_code == 200
        assert "access_token" in response.json()

    async def test_login_wrong_password(self, client: AsyncClient, registered_user):
        response = await client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "WrongPassword",
        })
        assert response.status_code == 401
```

### 14.4. Fixtures

```python
# tests/conftest.py

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.app.main import app
from src.app.core.database import get_db

TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/resumecraft_test"

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def sample_pdf_path(tmp_path):
    # Генерация тестового PDF
    ...
```

### 14.5. CI Pipeline

```yaml
# .gitlab-ci.yml

stages:
  - lint
  - test
  - build

lint:
  stage: lint
  script:
    - ruff check src/ tests/
    - mypy src/ --strict

test:
  stage: test
  services:
    - postgres:16
    - redis:7-alpine
  variables:
    DATABASE_URL: "postgresql+asyncpg://test:test@postgres:5432/test"
    REDIS_URL: "redis://redis:6379/0"
  script:
    - pytest --cov=src --cov-report=xml --cov-fail-under=70
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

build:
  stage: build
  script:
    - docker build -t resumecraft:latest .
  only:
    - main
```

---

## 15. Инфраструктура и деплой MVP

### 15.1. Локальная среда (Development)

```bash
# Одна команда для запуска всего стека
docker compose up -d

# Миграции
docker compose exec app alembic upgrade head

# Backend (hot reload)
docker compose exec app uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000

# Celery worker
docker compose exec app celery -A src.app.core.celery_app worker -l info

# Streamlit demo
streamlit run streamlit_app/app.py --server.port 8501
```

### 15.2. Docker Compose (MVP)

```yaml
version: '3.9'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./src:/app/src
    command: uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload

  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile
    env_file: .env
    depends_on: [db, redis]
    command: celery -A src.app.core.celery_app worker -l info -c 2
    volumes:
      - ./src:/app/src

  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: resumecraft
      POSTGRES_PASSWORD: devpassword
      POSTGRES_DB: resumecraft
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U resumecraft"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s

  # MinIO заменён на Local FS (Docker volume) для MVP
  # Файлы хранятся в Docker volume /data/uploads

  flower:
    build:
      context: .
      dockerfile: Dockerfile
    env_file: .env
    depends_on: [redis]
    command: celery -A src.app.core.celery_app flower --port=5555
    ports:
      - "5555:5555"

volumes:
  pgdata:
```

### 15.3. Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .
COPY streamlit_app/ streamlit_app/

EXPOSE 8000

CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 15.4. Деплой MVP (для защиты)

Для академической защиты достаточно локального деплоя на одной машине:

```
Ноутбук преподавателя/докладчика:
  Docker Desktop → docker compose up -d
  → FastAPI на :8000
  → Streamlit на :8501
  → PostgreSQL на :5432
  → Redis на :6379
  → Local FS (Docker volume /data/uploads)
```

Альтернатива — деплой на VPS (Selectel / Timeweb) для удалённого доступа.

---

## 16. Критерии приёмки MVP (Definition of Done)

### 16.1. Функциональные критерии

| № | Критерий | Тип | Статус |
|---|---------|-----|--------|
| 1 | Регистрация по email + пароль работает | Must | ☐ |
| 2 | Вход по email + пароль возвращает JWT | Must | ☐ |
| 3 | Загрузка PDF-резюме ≤ 10 МБ | Must | ☐ |
| 4 | Загрузка DOCX-резюме ≤ 10 МБ | Must | ☐ |
| 5 | Извлечение текста из PDF (PyMuPDF) | Must | ☐ |
| 6 | Извлечение текста из DOCX (python-docx) | Must | ☐ |
| 7 | LLM-структуризация резюме (имя, опыт, навыки) | Must | ☐ |
| 8 | Поиск вакансий через hh.ru API | Must | ☐ |
| 9 | Импорт вакансии по URL hh.ru | Must | ☐ |
| 10 | Ручной ввод вакансии | Must | ☐ |
| 11 | AI-оптимизация через GigaChat Pro | Must | ☐ |
| 12 | AI-оптимизация через Llama 3 (Groq) | Must | ☐ |
| 13 | Расчёт Match Score (до и после) | Must | ☐ |
| 14 | ATS-рейтинг (A+–F) | Should | ☐ |
| 15 | Diff: список изменений и ключевых слов | Must | ☐ |
| 16 | Экспорт DOCX | Must | ☐ |
| 17 | Streamlit demo UI (полный workflow) | Must | ☐ |
| 18 | Docker Compose: одна команда для запуска | Must | ☐ |

### 16.2. Качественные критерии

| Критерий | Порог |
|---------|-------|
| Unit test coverage | ≥ 70% |
| Ruff warnings | 0 |
| mypy errors | 0 |
| API response time (CRUD) | < 200 мс |
| Оптимизация (Llama 3) | < 15 секунд |
| Оптимизация (GigaChat) | < 30 секунд |
| Match Score improvement | +20%+ для 80% тестовых резюме |

### 16.3. Документационные критерии

| Документ | Статус |
|---------|--------|
| README.md (подробный) | ☐ |
| LICENSE (GPL-3.0) | ☐ |
| .gitignore | ☐ |
| REFERENCES.md (50+ источников) | ☐ |
| ANALYSIS.md (анализ ЦА) | ☐ |
| BASELINE.md (этот документ) | ☐ |
| .env.example | ☐ |
| API docs (auto-generated Swagger) | ☐ |
| Прототип (20 HTML-экранов) | ☐ |

---

## 17. Метрики успеха MVP

### 17.1. Технические метрики

| Метрика | Target | Как измеряется |
|---------|--------|----------------|
| End-to-end pipeline time | < 60 сек | Логирование в rewrite_history |
| Match Score improvement | +20%+ | Статистика по rewrite_history |
| Parsing success rate | > 95% | Ошибки парсинга / всего загрузок |
| LLM response validity | > 90% | Pydantic validation pass rate |
| Test coverage | ≥ 70% | pytest --cov |
| API availability (local) | 99% | Health check monitoring |

### 17.2. Пользовательские метрики (тестовая группа)

| Метрика | Target | Метод сбора |
|---------|--------|-------------|
| Task completion rate | > 80% | Наблюдение (user testing) |
| Time to first result | < 3 минуты | Замер при тестировании |
| User satisfaction (1–5) | ≥ 4.0 | Опрос после тестирования |
| NPS | ≥ 30 | Опрос (Would you recommend?) |
| Perceived Match Score accuracy | > 70% | Опрос (Насколько точна оценка?) |
| Willingness to pay | ≥ 30% | Опрос (Заплатили бы за Standard?) |

---

## 18. Ресурсы и сроки

### 18.1. Команда MVP

| Роль | Количество | Ответственность |
|------|-----------|-----------------|
| Backend-разработчик | 1 | FastAPI, Celery, LLM интеграция, БД |
| ML-инженер (совместитель) | 0.5 | Промпт-инженерия, Match Score, парсинг |

### 18.2. Timeline

```
Неделя 1–2: Фундамент
├── Инициализация проекта (pyproject.toml, Docker, CI)
├── Auth модуль (register, login, JWT)
├── Database schema + migrations
└── Local FS setup (Docker volume mount)

Неделя 3–4: Core Pipeline
├── Resume upload + parsing (PDF/DOCX)
├── LLM-структуризация
├── Vacancy module (hh.ru search, import, manual)
└── Embeddings generation

Неделя 5–6: AI Rewriting
├── Celery task pipeline
├── GigaChat Pro integration
├── Groq (Llama 3) integration
├── Match Score calculation
├── ATS rating
└── Diff generation

Неделя 7: Export + Streamlit
├── DOCX export
├── Streamlit demo UI (all pages)
└── End-to-end testing

Неделя 8: Polish + Documentation
├── Bug fixes
├── Test coverage → 70%+
├── Documentation finalization
├── Demo preparation
└── Docker compose verification
```

### 18.3. Зависимости

| Зависимость | Ответственный | Срок | Статус |
|-------------|---------------|------|--------|
| GigaChat API ключ | Разработчик | Неделя 1 | ☐ Получить на developers.sber.ru |
| Groq API ключ | Разработчик | Неделя 1 | ☐ Получить на console.groq.com |
| hh.ru App регистрация | Разработчик | Неделя 1 | ☐ Зарегистрировать на dev.hh.ru |
| Тестовые резюме (10+) | Разработчик | Неделя 3 | ☐ Собрать для тестирования |
| VPS (опционально) | Разработчик | Неделя 7 | ☐ Selectel/Timeweb |

---

## 19. Управление рисками

### 19.1. Матрица рисков

| Риск | Вероятность | Влияние | Митигация |
|------|------------|---------|-----------|
| **GigaChat API недоступен** | Средняя | Высокое | Fallback на Llama 3 (Groq). Автоматическое переключение. |
| **Groq rate limit исчерпан** | Средняя | Среднее | 14 400 запросов/день достаточно для MVP. При исчерпании → GigaChat. |
| **hh.ru API блокирует запросы** | Низкая | Среднее | User-Agent заголовок. Ручной ввод вакансии как fallback. |
| **Качество LLM-ответов нестабильно** | Средняя | Высокое | Pydantic-валидация ответов. Retry с другим промптом (до 3 попыток). |
| **Парсинг PDF даёт пустой результат** | Низкая | Среднее | OCR fallback (pytesseract). Уведомление пользователю. |
| **Не хватает времени** | Средняя | Высокое | Приоритизация Must-требований. Should/Could — при наличии времени. |
| **Тестовые резюме не репрезентативны** | Средняя | Среднее | Использовать публичные примеры с hh.ru, генерировать синтетические. |
| **Docker Hub заблокирован** | Высокая | Среднее | Использовать зеркала: mirror.gcr.io, Yandex Container Registry. |

### 19.2. Escalation-план

```
CRITICAL (блокер релиза):
  1. LLM API полностью недоступен → Ollama (локальный, офлайн)
  2. PostgreSQL + pgvector не работает → SQLite + FAISS (деградация)
  3. Не хватает времени → Сократить до: Upload + Manual Vacancy + Rewrite + Text Output

HIGH (значительное влияние):
  1. Match Score некорректен → Упростить до keyword overlap %
  2. DOCX export ломает форматирование → Экспорт как plain text

MEDIUM (умеренное влияние):
  1. Streamlit глючит → Swagger UI (/docs) как демо-интерфейс
  2. hh.ru API нестабилен → Только ручной ввод вакансий
```

---

## 20. Границы MVP (In/Out of Scope)

### 20.1. В объёме MVP (In Scope)

| Компонент | Объём |
|-----------|-------|
| **Аутентификация** | Email + пароль, JWT |
| **Резюме** | Загрузка PDF/DOCX, парсинг, LLM-структуризация |
| **Вакансии** | Поиск hh.ru (анонимный), URL-импорт, ручной ввод |
| **AI-оптимизация** | GigaChat Pro + Llama 3 (Groq), Match Score, ATS-рейтинг |
| **Экспорт** | DOCX |
| **UI** | Streamlit Demo (5 экранов) |
| **Инфраструктура** | Docker Compose, PostgreSQL, Redis, RabbitMQ, Local FS |
| **Тестирование** | Unit + Integration, 70%+ coverage |
| **Документация** | README, LICENSE, .gitignore, REFERENCES, ANALYSIS, BASELINE |
| **Прототип** | 20 HTML-экранов (уже готовы) |

### 20.2. Вне объёма MVP (Out of Scope → Future)

| Компонент | Фаза | Описание |
|-----------|------|----------|
| React SPA | Phase 2 | 20 экранов на React + TypeScript |
| OAuth hh.ru | Phase 2 | Авторизация соискателя, чтение/публикация резюме |
| ЮKassa | Phase 2 | Платёжная система, подписки |
| 2FA | Phase 2 | TOTP (Google Authenticator) + SMS |
| GPT-4o (OpenAI) | Phase 2 | Третья модель для Pro-пользователей |
| Экспорт PDF | Phase 2 | PDF с шаблонами (Minimal, Professional, Creative) |
| Экспорт на hh.ru | Phase 2 | Публикация оптимизированного резюме на hh.ru |
| Интерактивный редактор | Phase 2 | Редактирование секций резюме в UI |
| Dashboard | Phase 2 | Статистика, графики, карточки |
| History (полная) | Phase 2 | Timeline оптимизаций с фильтрами |
| Email подтверждение | Phase 2 | Верификация email при регистрации |
| Восстановление пароля | Phase 2 | Сброс через email |
| Telegram-бот | Phase 3 | Оптимизация резюме через Telegram |
| SuperJob / Avito | Phase 3 | Интеграция с другими площадками |
| Mobile app | Phase 3 | iOS + Android |
| B2B / API | Phase 3 | API для карьерных консультантов |
| AI Cover Letter | Phase 3 | Генерация сопроводительных писем |
| Interview Prep | Phase 4 | Подготовка к собеседованиям |
| AI Video Interview | Phase 4 | Тренажёр видеоинтервью |

---

## 21. Roadmap после MVP

### 21.1. Фазы развития

```
MVP (Phase 1) ─── 8 недель
│  Core pipeline: Upload → Parse → Match → Rewrite → Download
│  Streamlit Demo
│  GigaChat Pro + Llama 3
│  Docker Compose
│
├── Phase 2: Beta ─── 12 недель
│   │  React SPA (20 экранов)
│   │  OAuth hh.ru (полная интеграция)
│   │  ЮKassa (платёжная система)
│   │  GPT-4o (третья модель)
│   │  2FA, Email verification
│   │  PDF export + шаблоны
│   │  Интерактивный редактор
│   │  CI/CD (GitLab CI)
│   │
│   ├── Phase 3: Production ─── 16 недель
│   │   │  Yandex Cloud деплой
│   │   │  Prometheus + Grafana мониторинг
│   │   │  Sentry (error tracking)
│   │   │  A/B-тесты
│   │   │  SuperJob + Avito интеграция
│   │   │  Telegram-бот
│   │   │  B2B API
│   │   │
│   │   └── Phase 4: Scale ─── ongoing
│   │       Mobile app (iOS + Android)
│   │       AI Cover Letter
│   │       Interview Prep
│   │       Международные рынки (CIS)
│   │       AI Video Interview
```

### 21.2. KPI по фазам

| Фаза | MAU | Paid Users | MRR | Key Feature |
|------|-----|------------|-----|-------------|
| MVP | 100 (тест) | 0 | 0 | Core pipeline |
| Beta | 5 000 | 200 | 120 000 ₽ | React SPA + Payments |
| Production | 50 000 | 5 000 | 3 000 000 ₽ | Full product |
| Scale | 200 000 | 20 000 | 12 000 000 ₽ | Multi-platform |

---

## 22. Приложения

### 22.1. Чеклист запуска MVP

```
□ Git репозиторий инициализирован
□ .env.example создан и заполнен
□ Docker Compose поднимается одной командой
□ PostgreSQL + pgvector работает
□ Redis работает
□ Docker volumes для файлов настроены
□ Alembic миграции применяются
□ FastAPI запускается (GET /health → 200 OK)
□ Swagger UI доступен (/docs)
□ Регистрация работает
□ Вход работает
□ Загрузка PDF работает
□ Загрузка DOCX работает
□ Текст извлекается корректно
□ LLM-структуризация возвращает JSON
□ Поиск hh.ru API работает
□ Импорт вакансии по URL работает
□ GigaChat Pro оптимизация работает
□ Llama 3 (Groq) оптимизация работает
□ Match Score рассчитывается
□ ATS-рейтинг отображается
□ Diff (изменения) формируется
□ DOCX экспорт генерируется
□ Streamlit demo полностью функционален
□ Тесты проходят (70%+ coverage)
□ Ruff: 0 warnings
□ mypy: 0 errors
□ Документация актуальна
```

### 22.2. Словарь терминов MVP

| Термин | Определение |
|--------|-------------|
| **MVP** | Minimum Viable Product — минимально жизнеспособный продукт |
| **Pipeline** | Последовательность шагов обработки: parse → match → rewrite → export |
| **Match Score** | Оценка соответствия резюме вакансии (0–100%) |
| **ATS Rating** | Оценка совместимости с ATS-системами (A+ – F) |
| **Diff** | Визуальное сравнение оригинального и оптимизированного текста |
| **Celery Task** | Асинхронная задача, выполняемая worker'ом в фоне |
| **Embedding** | Векторное представление текста (1536 измерений) |
| **JWT** | JSON Web Token — формат аутентификационного токена |
| **HNSW** | Hierarchical Navigable Small World — алгоритм векторного поиска |
| **Structured Output** | Ответ LLM в формате JSON, валидируемый через Pydantic |

### 22.3. Соответствие экранов прототипа и MVP

| Экран прототипа | В MVP? | Реализация |
|-----------------|--------|------------|
| 01-landing.html | Частично | Streamlit: Page 1 (Главная) |
| 02-auth.html | Да | FastAPI: Auth Module |
| 03-password-recovery.html | Нет | Phase 2 |
| 04-email-verify.html | Нет | Phase 2 |
| 05-pricing.html | Нет | Phase 2 |
| 06-dashboard.html | Частично | Streamlit: базовая информация |
| 07-resumes.html | Да | FastAPI: GET /resumes |
| 08-upload.html | Да | Streamlit: Page 2 (Загрузка) |
| 09-vacancy.html | Да | Streamlit: Page 3 (Вакансия) |
| 10-models.html | Да | Streamlit: Page 4 (Selectbox) |
| 11-processing.html | Да | Streamlit: Progress bar |
| 12-results.html | Да | Streamlit: Page 4 (Results) |
| 13-editor.html | Нет | Phase 2 |
| 14-export.html | Частично | Streamlit: Page 5 (DOCX only) |
| 15-history.html | Нет | Phase 2 |
| 16-settings-profile.html | Нет | Phase 2 |
| 17-settings-ai.html | Нет | Phase 2 |
| 18-settings-subscription.html | Нет | Phase 2 |
| 19-settings-security.html | Нет | Phase 2 |
| 20-error-404.html | Нет | Phase 2 |

---

*ResumeCraft MVP — минимальный функциональный продукт, покрывающий базовый pipeline AI-оптимизации резюме для российского рынка труда.*

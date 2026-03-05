# ResumeCraft — Обзор литературы и конкурентного окружения

> **Версия:** 1.2  
> **Дата:** Март 2026  
> **Источников:** 60 верифицированных  
> **Связанные документы:** README.md (обзор), ANALYSIS.md (аудитория), BASELINE.md (спецификация)

---

## Содержание

1. [Российский рынок труда](#1-российский-рынок-труда)
2. [HeadHunter — платформа и API](#2-headhunter--платформа-и-api)
3. [ATS-системы и автоматизация рекрутинга](#3-ats-системы-и-автоматизация-рекрутинга)
4. [AI и LLM](#4-ai-и-llm)
5. [Конкуренты — глобальные](#5-конкуренты--глобальные)
6. [Конкуренты — российские](#6-конкуренты--российские)
7. [Технологический стек](#7-технологический-стек)
8. [Векторный поиск и эмбеддинги](#8-векторный-поиск-и-эмбеддинги)
9. [Парсинг документов](#9-парсинг-документов)
10. [UX/UI и дизайн-системы](#10-uxui-и-дизайн-системы)
11. [Законодательство](#11-законодательство)
12. [Научные публикации](#12-научные-публикации)
13. [Сводная таблица](#13-сводная-таблица)

---

## 1. Российский рынок труда

### [1] Росстат — Обследование рабочей силы (2025)

**URL:** https://rosstat.gov.ru/labour_force  
Данные о численности рабочей силы (~76 млн), занятости (74,3 млн) и безработице по МОТ (2,3% — рекорд). Обоснование размера целевого рынка.

### [2] HeadHunter Group PLC — Годовой отчёт 2024

**URL:** https://hh.ru/article/investor-relations  
Выручка 39,62 млрд ₽ (+34,5%), 93,3 млн резюме, 50+ млн уникальных соискателей, 1,8 млн вакансий. hh.ru = 64,3% трафика (SimilarWeb).

### [3] SimilarWeb — Трафик рекрутинговых сайтов

**URL:** https://www.similarweb.com/website/hh.ru/  
hh.ru — лидер (64,3%), SuperJob (~15%), Avito Работа. Среднее время визита 9:42, bounce rate 30,8%.

### [4] hh.ru — Индекс HeadHunter (2025)

**URL:** https://stats.hh.ru/  
Индекс для белых воротничков вырос с 3,7 до 5,9–7,3. Вакансии для офисных работников −25% (777K → 582K).

### [5] vc.ru — HR-tech тренды 2024–2025

**URL:** https://vc.ru/hr  
44% работодателей используют HR-автоматизацию. Рекрутеры тратят 6–20 сек на просмотр резюме.

---

## 2. HeadHunter — платформа и API

### [6] HH API — Документация

**URL:** https://github.com/hhru/api  
REST API (~590 ⭐). `GET /vacancies`, `GET /vacancies/{id}`, `GET /dictionaries`. Пагинация ≤ 2000, per_page max 100.

### [7] HH API — OAuth 2.0

**URL:** https://github.com/hhru/api/blob/master/docs/authorization.md  
4 уровня: анонимный, приложение, соискатель, работодатель. Access-токен ~14 дней. Регистрация на dev.hh.ru.

### [8] HH API — Вакансии

**URL:** https://github.com/hhru/api/blob/master/docs/vacancies.md  
Поиск по тексту, региону, зарплате, опыту. Детали: описание (HTML), ключевые навыки, зарплатная вилка.

### [9] HH API — Резюме

**URL:** https://github.com/hhru/api/blob/master/docs/resumes.md  
OAuth 2.0. `GET /resumes/mine`, `GET /resumes/{id}`, `PUT /resumes/{id}`. Структура: заголовок, опыт, навыки, контакты.

---

## 3. ATS-системы и автоматизация рекрутинга

### [10] Huntflow

**URL:** https://huntflow.ru/  
Лидирующая российская ATS. Интеграция с hh.ru, AI-ранжирование, воронка найма.

### [11] Potok

**URL:** https://potok.io/  
Облачная ATS для среднего бизнеса. Парсинг с hh.ru/SuperJob, автоматическое ранжирование.

### [12] Talantix (HeadHunter Group)

**URL:** https://talantix.ru/  
ATS от HeadHunter. Нативная интеграция с hh.ru, автопарсинг откликов.

### [13] Skillaz

**URL:** https://skillaz.ru/  
AI-powered HR: автоскрининг, чат-боты, предиктивная аналитика. Крупные корпорации и госсектор.

### [14] Jobvite — Job Seeker Nation Survey 2024

**URL:** https://www.jobvite.com/job-seeker-nation/  
75% резюме отсеиваются ATS на первом этапе. Рекрутеры тратят 6–7 сек на первичный просмотр.

### [15] TheLadders — Eye-Tracking Study

**URL:** https://www.theladders.com/static/images/basicSite/pdfs/TheLadders-EyeTracking-StudyC2.pdf  
Eye-tracking: рекрутеры тратят 7,4 сек, фокус на имени, должности, компании, образовании.

---

## 4. AI и LLM

### [16] GigaChat — API

**URL:** https://developers.sber.ru/docs/ru/gigachat/overview  
Lite (бесплатно), Pro (платно). OpenAI-compatible REST API. #1 на MERA для русского. Function calling, streaming, embeddings.

### [17] OpenAI — GPT-4o

**URL:** https://platform.openai.com/docs/api-reference/chat/create  
Structured outputs, function calling, 128K ctx. $2.50/$10.00 за 1M tokens. Premium-модель для Pro-пользователей.

### [18] Meta AI — Llama 3.3 70B

**URL:** https://ai.meta.com/blog/llama-3-3/  
Open-source, 70B params. Бесплатно через Groq (14 400 req/день), Together.ai, Ollama.

### [19] Groq — API

**URL:** https://console.groq.com/docs  
LPU-инференс. Free tier: 14 400 req/день для Llama 3.3 70B. 2–5× быстрее GPU.

### [20] Ollama

**URL:** https://ollama.com/  
Локальный запуск LLM. REST API совместим с OpenAI SDK. 100+ моделей. macOS/Linux/Windows.

### [21] MERA Benchmark

**URL:** https://mera.a-ai.ru/  
Российский бенчмарк LLM: понимание, генерация, рассуждения на русском. GigaChat Pro — лидер.

### [22] YandexGPT — API

**URL:** https://yandex.cloud/ru/docs/foundation-models/  
YandexGPT 4. Нативная интеграция с Yandex Cloud, streaming, embeddings.

### [60] Anthropic — Claude API

**URL:** https://docs.anthropic.com/en/docs  
Claude Sonnet 4, Claude Haiku. 200K контекст, structured output, Messages API. Прямая интеграция через `anthropic` SDK.

---

## 5. Конкуренты — глобальные

### [23] Rezi.ai

**URL:** https://www.rezi.ai/  
AI resume builder, ATS-шаблоны, keyword optimization. $29/мес. **Нет русского, нет hh.ru.**

### [24] Jobscan

**URL:** https://www.jobscan.co/  
Match Rate scoring, keyword analysis. $49.95/мес. Интеграция с LinkedIn. **Нет русского.**

### [25] Resume Worded

**URL:** https://resumeworded.com/  
AI-скоринг 0–100, фидбэк по секциям, LinkedIn optimization. $49/мес. **Нет русского.**

### [26] Teal HQ

**URL:** https://www.tealhq.com/  
AI resume + job tracker + matching score. Freemium. Drag & drop experience builder. **Нет русского.**

### [27] Kickresume

**URL:** https://www.kickresume.com/  
40+ шаблонов, GPT-4 генерация. 30+ языков (частичный русский). $19/мес. Нет hh.ru.

### [28] Enhancv

**URL:** https://enhancv.com/  
Фокус на визуальном оформлении. 30+ шаблонов, ATS checker. $24.99/мес. **Нет русского.**

---

## 6. Конкуренты — российские

### [29] Cvator.ru

**URL:** https://cvator.ru/  
AI-оптимизация существующего резюме. Наиболее функциональный RU-конкурент. Мало публичных отзывов.

### [30] Rezumus.com

**URL:** https://rezumus.com/  
AI-генерация с нуля. **Критический минус: не поддерживает загрузку существующего CV** — неприменим для 80%+ соискателей.

### [31] hh.ru — AI для работодателей

**URL:** https://hh.ru/employer  
AI-ранжирование откликов, скоринг кандидатов — только для работодателей. **Для соискателей AI-инструментов нет** → ниша открыта.

### [32] MyResume.ru

**URL:** https://myresume.ru/  
Шаблонный конструктор без AI. Бесплатный + Premium. Минимальный конкурент.

### [33] Canva — Шаблоны резюме

**URL:** https://www.canva.com/resumes/  
1000+ шаблонов. Визуально привлекательные, но **не ATS-совместимые** (многоколоночные макеты). Без AI.

---

## 7. Технологический стек

### [34] FastAPI

**URL:** https://fastapi.tiangolo.com/  
Async Python web-фреймворк. Pydantic, автогенерация OpenAPI. 80K+ ⭐.

### [35] FastAPI Best Practices

**URL:** https://github.com/zhanymkanov/fastapi-best-practices  
Архитектурные рекомендации: доменная организация, async-паттерны. 24.8K+ ⭐.

### [36] PostgreSQL 16

**URL:** https://www.postgresql.org/docs/16/  
Основная СУБД. JSONB, полнотекстовый поиск, транзакции, расширения.

### [37] pgvector

**URL:** https://github.com/pgvector/pgvector  
Векторное расширение PostgreSQL. L2, inner product, cosine distance. HNSW-индексы (recall 95%+). 13K+ ⭐.

### [38] SQLAlchemy 2.0

**URL:** https://docs.sqlalchemy.org/en/20/  
ORM + SQL toolkit. Async (asyncpg), типизированные запросы. Де-факто стандарт Python.

### [39] Celery

**URL:** https://docs.celeryq.dev/en/stable/  
Distributed task queue. RabbitMQ/Redis брокеры, Flower мониторинг, retries, canvas.

### [40] Redis

**URL:** https://redis.io/docs  
In-memory store. Result backend для Celery, кэш справочников hh.ru.

### [41] MinIO

**URL:** https://min.io/docs/minio/linux/index.html  
S3-совместимое хранилище. AGPL-3.0. В MVP: Local FS → в продакшене: Yandex Object Storage.

---

## 8. Векторный поиск и эмбеддинги

### [42] Vaswani et al. — Attention Is All You Need (2017)

**URL:** https://arxiv.org/abs/1706.03762  
Архитектура Transformer — основа всех LLM. Self-attention для контекста всех токенов.

### [43] Reimers & Gurevych — Sentence-BERT (2019)

**URL:** https://arxiv.org/abs/1908.10084  
Семантические эмбеддинги через siamese BERT. Библиотека sentence-transformers (30K+ ⭐).

### [44] Malkov & Yashunin — HNSW (2018)

**URL:** https://arxiv.org/abs/1603.09320  
Алгоритм приближённого поиска. Recall 95%+, субмиллисекундные запросы. Используется в pgvector.

---

## 9. Парсинг документов

### [45] PyMuPDF (fitz)

**URL:** https://pymupdf.readthedocs.io/en/latest/  
PDF: текст, метаданные, таблицы. ~0.1 сек/стр. AGPL-3.0 → причина GPL-3.0 проекта.

### [46] pdfplumber

**URL:** https://github.com/jsvine/pdfplumber  
Альтернативный PDF-парсер. MIT. Медленнее PyMuPDF, хорош для таблиц. Fallback.

### [47] python-docx

**URL:** https://python-docx.readthedocs.io/en/latest/  
Чтение/создание DOCX. Параграфы, таблицы, стили. MIT. Стандарт для Word в Python.

### [48] pytesseract

**URL:** https://github.com/madmaze/pytesseract  
Tesseract OCR wrapper. 100+ языков (вкл. русский). Fallback для сканированных PDF.

---

## 10. UX/UI и дизайн-системы

### [49] Google Fonts — Inter

**URL:** https://fonts.google.com/specimen/Inter  
Open-source шрифт для экранов. Кириллица, переменный вес. Используется в GitHub, Figma.

### [50] Nielsen Norman Group — Dashboard Design

**URL:** https://www.nngroup.com/articles/dashboard-design/  
Card-based layout, прогресс-бары, «Overview first, details on demand» (Shneiderman).

### [51] Material Design 3

**URL:** https://m3.material.io/  
Color tokens, elevation, typography scale. Информирование дизайн-системы ResumeCraft.

---

## 11. Законодательство

### [52] ФЗ-152 — О персональных данных

**URL:** http://www.consultant.ru/document/cons_doc_LAW_61801/  
Хранение ПД граждан РФ в России. Согласие на обработку, право на удаление.

### [53] GDPR

**URL:** https://gdpr-info.eu/  
Right to access, erasure, portability. Применимо при обработке данных граждан ЕС. Privacy by design.

### [54] ТК РФ — Статья 3

**URL:** http://www.consultant.ru/document/cons_doc_LAW_34683/  
Запрет дискриминации. AI не должен генерировать дискриминационные маркеры в резюме.

---

## 12. Научные публикации

### [55] Lewis et al. — RAG (NeurIPS 2020)

**URL:** https://arxiv.org/abs/2005.11401  
Retrieval-Augmented Generation. Обогащение LLM внешними источниками без дообучения.

### [56] Devlin et al. — BERT (NAACL 2019)

**URL:** https://arxiv.org/abs/1810.04805  
Bidirectional Transformers. Основа sentence-transformers для эмбеддингов.

### [57] Brown et al. — GPT-3 (NeurIPS 2020)

**URL:** https://arxiv.org/abs/2005.14165  
Few-shot learning. Теоретическая основа prompt engineering для оптимизации резюме.

### [58] Wei et al. — Chain-of-Thought (NeurIPS 2022)

**URL:** https://arxiv.org/abs/2201.11903  
CoT prompting. Пошаговая оценка соответствия резюме требованиям вакансии.

### [59] Touvron et al. — LLaMA (arXiv 2023)

**URL:** https://arxiv.org/abs/2302.13971  
Open-source LLM от Meta. Основа Llama 3.3 70B, используемой в Free-тарифе.

---

## 13. Сводная таблица

| № | Название | Тип | Год |
|--:|---------|-----|:---:|
| 1 | Росстат — Обследование рабочей силы | Статистика | 2025 |
| 2 | HeadHunter — Годовой отчёт | Отчёт | 2024 |
| 3 | SimilarWeb — Трафик | Аналитика | 2025 |
| 4 | hh.ru — Индекс | Статистика | 2025 |
| 5 | vc.ru — HR-tech | Аналитика | 2025 |
| 6 | HH API — Документация | Тех. док. | 2024 |
| 7 | HH API — OAuth 2.0 | Тех. док. | 2024 |
| 8 | HH API — Вакансии | Тех. док. | 2024 |
| 9 | HH API — Резюме | Тех. док. | 2024 |
| 10 | Huntflow | Продукт | 2025 |
| 11 | Potok | Продукт | 2025 |
| 12 | Talantix | Продукт | 2025 |
| 13 | Skillaz | Продукт | 2025 |
| 14 | Jobvite — Survey | Исследование | 2024 |
| 15 | TheLadders — Eye-Tracking | Исследование | 2018 |
| 16 | GigaChat API | Тех. док. | 2025 |
| 17 | OpenAI — GPT-4o | Тех. док. | 2025 |
| 18 | Meta — Llama 3.3 | Тех. док. | 2024 |
| 19 | Groq API | Тех. док. | 2025 |
| 20 | Ollama | Тех. док. | 2025 |
| 21 | MERA Benchmark | Бенчмарк | 2025 |
| 22 | YandexGPT | Тех. док. | 2025 |
| 60 | Anthropic — Claude API | Тех. док. | 2025 |
| 23 | Rezi.ai | Продукт | 2025 |
| 24 | Jobscan | Продукт | 2025 |
| 25 | Resume Worded | Продукт | 2025 |
| 26 | Teal HQ | Продукт | 2025 |
| 27 | Kickresume | Продукт | 2025 |
| 28 | Enhancv | Продукт | 2025 |
| 29 | Cvator.ru | Продукт | 2025 |
| 30 | Rezumus.com | Продукт | 2025 |
| 31 | hh.ru — AI (работодатели) | Продукт | 2025 |
| 32 | MyResume.ru | Продукт | 2025 |
| 33 | Canva — Резюме | Продукт | 2025 |
| 34 | FastAPI | Тех. док. | 2024 |
| 35 | FastAPI Best Practices | GitHub | 2024 |
| 36 | PostgreSQL 16 | Тех. док. | 2024 |
| 37 | pgvector | Тех. док. | 2024 |
| 38 | SQLAlchemy 2.0 | Тех. док. | 2024 |
| 39 | Celery | Тех. док. | 2024 |
| 40 | Redis | Тех. док. | 2024 |
| 41 | MinIO | Тех. док. | 2024 |
| 42 | Vaswani et al. — Transformer | Научная | 2017 |
| 43 | Reimers — Sentence-BERT | Научная | 2019 |
| 44 | Malkov — HNSW | Научная | 2018 |
| 45 | PyMuPDF | Тех. док. | 2024 |
| 46 | pdfplumber | Тех. док. | 2024 |
| 47 | python-docx | Тех. док. | 2024 |
| 48 | pytesseract | Тех. док. | 2024 |
| 49 | Inter (Google Fonts) | Ресурс | 2024 |
| 50 | NNGroup — Dashboards | Исследование | 2023 |
| 51 | Material Design 3 | Дизайн | 2024 |
| 52 | ФЗ-152 | Закон РФ | 2024 |
| 53 | GDPR | Регламент ЕС | 2016 |
| 54 | ТК РФ — Ст. 3 | Закон РФ | 2001 |
| 55 | Lewis et al. — RAG | Научная | 2020 |
| 56 | Devlin et al. — BERT | Научная | 2018 |
| 57 | Brown et al. — GPT-3 | Научная | 2020 |
| 58 | Wei et al. — CoT | Научная | 2022 |
| 59 | Touvron et al. — LLaMA | Научная | 2023 |

---

*ResumeCraft — 60 верифицированных источников по всем аспектам проекта.*

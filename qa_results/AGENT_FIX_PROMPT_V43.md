# AGENT FIX PROMPT V43 — Дефекты, фиксы и проверка провайдеров

**Дата:** 2026-03-14
**Источник:** QA Report #40 (40_FULL_REGRESSION_V43.md) + анализ кода
**Проект:** ResumeCraft.ru
**Тестовый аккаунт:** qa_v43_test@example.com / NewTestPass1231 — аккаунт АКТИВЕН

---

## 🎯 ЗАДАЧА V44: ПРОВЕРИТЬ РАБОТУ ВСЕХ 5 ПРОВАЙДЕРОВ

Раньше все 5 провайдеров работали. В V43 при автоматизированном тестировании OpenAI и Anthropic вернули ошибку "Модель недоступна у провайдера". Анализ кода показал, что **код фронтенда и бэкенда корректен** — вероятнее всего, проблема была в том, что ошибка `model not found` теперь перехватывается шире (коммит V43 расширил `_handle_llm_error` в `llm_client.py`).

### Что было сломано в V43 (коммит `6c56f12`) и ОТКАЧЕНО:

**Файл:** `src/app/ml/llm_client.py` — функция `_handle_llm_error`

В V43 расширили обнаружение model-not-found ошибок, что **сломало** перехват:
```python
# БЫЛО (V42) — РАБОТАЛО, ВОЗВРАЩЕНО:
if status_code == 404 or 'not found' in err_str.lower() or 'model_not_found' in err_str.lower():
    from app.core.exceptions import AppError
    raise AppError(
        message=f'Модель недоступна у провайдера {provider}',
        status_code=400,
        error_code='LLM_MODEL_NOT_FOUND',
        detail='Выбранная модель не найдена или снята с поддержки. Выберите другую модель.',
    ) from exc

# БЫЛО (V43) — СЛОМАНО, ОТКАЧЕНО:
model_keywords = (
    'model not found',
    'model_not_found',
    'does not exist',
    'invalid model',
    'model not active',
    'model is not available',
    'no such model',
)
is_model_err = status_code == 404 or any(kw in lower for kw in model_keywords)
```

**Причина поломки:** Расширенный список `model_keywords` слишком агрессивно перехватывал ответы провайдеров. Ключевые слова вроде `'does not exist'`, `'invalid model'`, `'model is not available'` могли срабатывать на ответы, не связанные с отсутствием модели (напр. ошибки авторизации, rate limit, billing).

**Статус:** Код ОТКАЧЕН к V42 версии. В `llm_client.py` сейчас стоит рабочая V42 проверка.

### Ошибка в истории: "OpenAI · GigaChat-Pro" и "Anthropic · GigaChat-Pro"

Записи в истории показывают, что бэкенд получил модель `GigaChat-Pro` вместо правильной модели провайдера. Это означает, что **фронтенд отправил `model: "gigachat-pro"` вместо `model: "openai"`**.

**Возможные причины:**
1. Сохранённая модель по умолчанию в `/api/v1/settings/ai-model` — если ранее был сохранён `gigachat-pro`, он подставляется при загрузке страницы `/app/models` (строки 115-118 `ModelsPage.tsx`)
2. React state `selected` не обновляется при клике на карточку — state остаётся `'gigachat-pro'` (default, строка 95)
3. Проверить endpoint `GET /api/v1/settings/ai-model` — что он возвращает для тестового аккаунта

**Рекомендация:** Обновить список моделей в API-ответе `/api/v1/models` и проверить, что все провайдеры возвращают `available: true` при наличии ключа.

### ✅ ОБЯЗАТЕЛЬНАЯ ПРОВЕРКА V44: Все 5 провайдеров

Запустить оптимизацию вручную (через UI) для каждого провайдера и убедиться, что все работают:

| # | Провайдер | Модель по умолчанию | Ожидаемый результат |
|---|-----------|-------------------|---------------------|
| 1 | GigaChat | GigaChat-Pro | ✅ Score + ATS rating |
| 2 | OpenAI | gpt-4o-mini (fallback) или gpt-4o | ✅ Score + ATS rating |
| 3 | Anthropic | claude-sonnet-4-20250514 | ✅ Score + ATS rating |
| 4 | OpenRouter | anthropic/claude-3.5-sonnet | ✅ Score + ATS rating |
| 5 | Groq | llama-3.3-70b-versatile | ✅ Score + ATS rating |

**Тестовые API-ключи:**
- GigaChat: `MDU2NDkwYjUtODc1OS00NmY4LThiZGMtZDk4ZGM4ZjEyMWFhOmNhZmQyYzA4LTY4ZjMtNDE5Yi04ZmMzLThlNzA5NjQ5MjJiNA==`
- OpenAI: `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`
- Anthropic: `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`
- OpenRouter: `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`
- Groq: `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`

---

## СВОДКА ДЕФЕКТОВ

| # | Приоритет | ID | Описание | Тип | Статус V43 |
|---|-----------|-----|----------|-----|------------|
| 24 | 🟡 P2 | OPENAI-MODEL-MAPPING | OpenAI оптимизация → ошибка "Модель недоступна" | INVESTIGATE | ❓ ТРЕБУЕТ ПРОВЕРКИ |
| 25 | 🟡 P2 | ANTHROPIC-MODEL-MAPPING | Anthropic оптимизация → ошибка "Модель недоступна" | INVESTIGATE | ❓ ТРЕБУЕТ ПРОВЕРКИ |
| 23 | 🔴 P1 | ACCOUNT-DELETE-500-REGRESSION | Удаление аккаунта → 500 | REGRESSION | ❌ CONFIRMED V43 |
| 3 | 🔴 P2 | HH-RESUME-LINK-400 | Загрузка резюме по ссылке hh.ru → 400 | BUG | ❌ CONFIRMED V43 |
| 18 | 🔴 P2 | GROQ-ALLAM-502 | Groq allam-2-7b → ошибка провайдера | BUG | ❌ CONFIRMED V43 |
| 21 | 🔴 P2 | ACCOUNT-DELETE-HARD-vs-SOFT | Hard delete вместо soft delete | BUG | ⏸ BLOCKED V43 |
| 7 | 🟡 P3 | VACANCY-TITLE-002 | Автозаполнение должности из имени резюме | BUG | ⚠️ KNOWN ISSUE |

---

## 🔧 ФИКСЫ И РЕКОМЕНДАЦИИ

### 1. OPENAI-MODEL-MAPPING + ANTHROPIC-MODEL-MAPPING — ДВА БАГА

**Баг A: `_handle_llm_error` сломан в V43 → ОТКАЧЕН**
Файл `src/app/ml/llm_client.py` — расширенный перехват `model_keywords` в V43 ловил ошибки, не связанные с моделью. **Код возвращён к V42 версии.** Не менять этот блок без тщательного тестирования всех 5 провайдеров.

**Баг B: Фронтенд отправляет `GigaChat-Pro` вместо правильной модели**
История показывает `"OpenAI · GigaChat-Pro"` и `"Anthropic · GigaChat-Pro"` — это значит, бэкенд получил `model="gigachat-pro"`.

Проверить:
1. `GET /api/v1/settings/ai-model` — что возвращает? Если `gigachat-pro`, то `ModelsPage.tsx` подставляет его как `selected` (строка 117-118)
2. `GET /api/v1/models` — все ли провайдеры возвращают `available: true`?
3. Проверить UI вручную: выбрать OpenAI → увидеть dropdown подмоделей → запустить → проверить что в payload POST /api/v1/rewrite пришло `model: "openai"`
4. Обновить список моделей в API если нужно — убедиться что все дефолтные модели (`gpt-4o-mini`, `claude-sonnet-4-20250514`, `llama-3.3-70b-versatile`) реально доступны у провайдеров

### 2. ACCOUNT-DELETE-500-REGRESSION (P1)

**Файл:** `src/app/auth/router.py`
**Проблема:** DELETE /api/v1/auth/me → 500 (4 версии подряд V40-V43)
**Коммит V43** добавил try/except в delete_me, но ошибка сохраняется.
**Рекомендация:** Проверить логи сервера для точной трассировки 500 ошибки. Возможные причины: FK constraints, cascade delete, отсутствие транзакции.

### 3. HH-RESUME-LINK-400 (P2) — Парсинг hh.ru резюме

**Проблема:** POST /api/v1/resumes/from-url → 400 (9 версий V35-V43!)
**Причина:** hh.ru блокирует обычные HTTP-запросы (requests/httpx). Нужен headless browser.

**Рабочий код парсинга hh.ru резюме (Playwright + BeautifulSoup):**
```python
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

URL = "https://hh.ru/resume/90d67b47ff01c53bfd0039ed1f36424d765046"

async def parse_resume():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )
        page = await context.new_page()
        await page.goto(URL, timeout=60000)
        await page.wait_for_timeout(4000)
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        result = {}
        # имя
        name = soup.select_one("h2[data-qa='resume-personal-name']")
        result["name"] = name.text.strip() if name else None
        # должность
        position = soup.select_one("span[data-qa='resume-block-title-position']")
        result["position"] = position.text.strip() if position else None
        # зарплата
        salary = soup.select_one("[data-qa='resume-block-salary']")
        result["salary"] = salary.text.strip() if salary else None
        # навыки
        skills = soup.select("[data-qa='bloko-tag__text']")
        result["skills"] = [s.text.strip() for s in skills]
        # опыт работы
        experience = []
        jobs = soup.select("[data-qa='resume-block-experience'] .resume-block-item-gap")
        for job in jobs:
            title = job.select_one("[data-qa='resume-block-experience-position']")
            company = job.select_one("[data-qa='resume-block-experience-employer']")
            period = job.select_one("[data-qa='resume-block-experience-date']")
            experience.append({
                "title": title.text.strip() if title else None,
                "company": company.text.strip() if company else None,
                "period": period.text.strip() if period else None
            })
        result["experience"] = experience
        await browser.close()
        return result

async def main():
    data = await parse_resume()
    print("RESULT:")
    print(data)

if __name__ == "__main__":
    asyncio.run(main())
```

**Аналогичный код для парсинга ВАКАНСИЙ hh.ru:**
```python
# URL вакансии: https://hh.ru/vacancy/131080132
# Селекторы:
# - Название: h1[data-qa='vacancy-title']
# - Зарплата: span[data-qa='vacancy-salary-compensation-type-net'] или [data-qa='vacancy-salary']
# - Компания: a[data-qa='vacancy-company-name']
# - Описание: div[data-qa='vacancy-description']
# - Навыки: li[data-qa='skills-element'] > span[data-qa='bloko-tag__text']
# - Опыт: span[data-qa='vacancy-experience']
```

**Рекомендация:** Использовать Playwright как основу для endpoint `POST /api/v1/resumes/from-url`. Необходимо: `pip install playwright beautifulsoup4`, `playwright install chromium`.

### 4. GROQ-ALLAM-502 (P2) — Заменить модель

**Проблема:** Модель `allam-2-7b` не существует на Groq. Groq теперь возвращает 400 (не 404), что раньше не перехватывалось.

**Решение:** Модель уже заменена в коде! В `llm_factory.py` строка 45: `'groq': 'llama-3.3-70b-versatile'`. А в `ModelsPage.tsx` fallback sub-models для Groq уже содержат рабочие модели:
```
llama-3.3-70b-versatile, llama-3.1-8b-instant, llama3-70b-8192, mixtral-8x7b-32768, gemma2-9b-it
```

**Проблема в том, что ранее сохранённый `sub_model` в БД может быть `allam-2-7b`!** При перезапуске оптимизации используется старый `sub_model`.

**Рабочий код Groq API (проверено, streaming):**
```python
from groq import Groq

client = Groq()
completion = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[
      {
        "role": "user",
        "content": "Привет"
      },
      {
        "role": "assistant",
        "content": "Привет! Чем я могу вам помочь?"
      },
      {
        "role": "user",
        "content": ""
      }
    ],
    temperature=1,
    max_completion_tokens=1024,
    top_p=1,
    stream=True,
    stop=None
)

for chunk in completion:
    print(chunk.choices[0].delta.content or "", end="")
```

**Рекомендация:** Groq работает. Проверить, что при выборе Groq в UI отправляется рабочая модель (`llama-3.3-70b-versatile` или `llama-3.1-8b-instant`), а не устаревшая `allam-2-7b`.

### 5. VACANCY-TITLE-002 (P3) — Автозаполнение должности
Коммит V43 добавил regex-парсинг должности из `raw_text` (`VacancyPage.tsx` строки 44-52). Проверить, работает ли.

### 6. ACCOUNT-DELETE-HARD-vs-SOFT (P3)
Заблокирован до исправления ACCOUNT-DELETE-500.

---

## 📊 АРХИТЕКТУРА ПРОВАЙДЕРОВ (для справки)

### Поток данных при оптимизации:
```
UI (ModelsPage.tsx)
  → selected: "openai", subModel: "gpt-4o"
  → api.startRewrite(resumeId, vacancyId, "openai", "gpt-4o")
  → POST /api/v1/rewrite { model: "openai", sub_model: "gpt-4o" }

Backend (router.py)
  → RewriteRequest(model="openai", sub_model="gpt-4o")
  → service.create_rewrite_task(model_name="openai", sub_model="gpt-4o")
  → effective_model = "openai:gpt-4o" (сохраняется в БД)

Celery (tasks.py → service.py)
  → provider_name="openai", sub_model_value="gpt-4o"
  → LLMClientFactory.create_with_fallback(preferred="openai", sub_model="gpt-4o")
  → OpenAIClient(model="gpt-4o", api_key=user_key)
  → OpenAI API: model="gpt-4o"
```

### Ключевые файлы:
| Файл | Назначение |
|------|-----------|
| `frontend/src/pages/wizard/ModelsPage.tsx` | UI выбора модели, state: `selected` + `subModel` |
| `frontend/src/services/api.ts` | `startRewrite(resumeId, vacancyId, model, subModel?)` |
| `src/app/rewriter/router.py` | POST /rewrite, маппинг model → provider для проверки ключа |
| `src/app/rewriter/service.py` | `create_rewrite_task()` — сохраняет `provider:sub_model` |
| `src/app/ml/llm_factory.py` | `LLMClientFactory.create()` — создаёт клиент по провайдеру |
| `src/app/ml/llm_client.py` | Клиенты: GigaChat, OpenAI, Anthropic, OpenRouter, Groq |

### Дефолтные модели (llm_factory.py `_MODEL_NAMES`):
| Провайдер | Модель по умолчанию |
|-----------|-------------------|
| gigachat-pro | GigaChat-Pro |
| openai | gpt-4o-mini |
| anthropic | claude-sonnet-4-20250514 |
| openrouter | anthropic/claude-3.5-sonnet |
| groq | llama-3.3-70b-versatile |

---

## ✅ ИСПРАВЛЕННЫЕ БАГИ (стабильны V43)

| ID | P | Описание | Исправлено | Стабильно |
|----|---|----------|------------|-----------|
| PASSWORD-CHANGE-503 | P1 | PUT /api/v1/auth/me/password → 204 | V42 | ✅ V43 |
| AVATAR-DELETE-503 | P2 | DELETE /api/v1/auth/me/avatar → 204 | V42 | ✅ V43 |
| LOGOUT-503 | P3 | POST /api/v1/auth/logout → 204 | V41 | ✅ V43 |
| VACANCY-URL-OBJECT-ERROR | P3 | API → 422 (было 500) | V40 | ✅ V43 |
| VACANCY-URL-500 | P3 | Невалидный URL → 422 | V40 | ✅ V43 |
| + 13 других багов (V35-V37) | — | Все стабильны | V35-V37 | ✅ V43 |

**Всего исправлено/закрыто: 18 из 25 (72%)**

---

## 📈 ТРЕНД КАЧЕСТВА

| Версия | Тестов | PASS | FAIL | Pass Rate | Провайдеры |
|--------|--------|------|------|-----------|------------|
| V35 | 25 | 14 | 11 | 56% | — |
| V36 | 25 | 16 | 9 | 64% | — |
| V37 | 25 | 17 | 7 | 68% | — |
| V38 | 25 | 17 | 7 | 68% | 4/5 |
| V39 | 25 | 18 | 6 | 72% | 4/5 |
| V40 | 25 | 19 | 5 | 76% | 4/5 |
| V41 | 25 | 20 | 5 | 80% | 4/5 |
| V42 | 25 | 22 | 3 | **88%** ⬆️ | 4/5 |
| **V43** | **25** | **18** | **5** | **72%** ⬇️ | **2/5** ⬇️ |

---

## ⚡ ПРИОРИТЕТНЫЙ ПЛАН ДЕЙСТВИЙ V44

1. **🔴 ОТКАЧЕНО** — `_handle_llm_error` в `llm_client.py` возвращён к V42 версии. НЕ МЕНЯТЬ расширенный перехват `model_keywords` без тестирования всех провайдеров!
2. **🔍 ПРОВЕРИТЬ ВСЕ 5 ПРОВАЙДЕРОВ** — Запустить оптимизацию через UI для каждого. Убедиться что POST /api/v1/rewrite получает правильный `model` (не `gigachat-pro` для всех).
3. **🔧 ИСПРАВИТЬ** — Если фронт отправляет неправильный model → проверить `GET /api/v1/settings/ai-model` и `GET /api/v1/models` + обновить список доступных моделей
4. **🔧 ИСПРАВИТЬ** — ACCOUNT-DELETE-500 (P1) — проверить логи, FK constraints
5. **🔧 ДОБАВИТЬ** — Парсинг hh.ru через Playwright (код выше)
6. **✅ ПРОВЕРИТЬ** — Groq с моделью `llama-3.3-70b-versatile` (не `allam-2-7b`)
7. **✅ ПРОВЕРИТЬ** — Автозаполнение должности из raw_text (V43 fix)

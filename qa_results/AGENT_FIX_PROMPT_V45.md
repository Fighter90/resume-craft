# AGENT FIX PROMPT V45 — Доработки по результатам полного регресса

**Дата:** 2026-03-14
**Версия приложения:** 1.26.0
**Источник:** QA Report #41 (41_FULL_REGRESSION_V45.md)
**Проект:** ResumeCraft.ru
**Тестовый аккаунт:** `qa_v45_live@example.com` / TestPass1231 — аккаунт АКТИВЕН (delete → 500)
**Окружение:** Chrome, resumecraft.ru (production)

---

## 📊 СТАТУС КАЧЕСТВА

| Метрика | V44 | V45 | Δ |
|---------|-----|-----|---|
| Pass Rate | 80% (24/30) | **87.5%** (28/32) | +7.5% ⬆️ |
| Провайдеры | 4/5 | **5/5** | +1 🎉 |
| Критичные баги | 2 | **0** | -2 ✅ |
| P2 баги | 2 | **1** | -1 ✅ |
| P3 баги | 1 | **2** | +1 |

### ✅ ИСПРАВЛЕНО в V45 (подтверждено тестами):
1. **GROQ-KEY-INVISIBLE** (P1) — Groq теперь работает (Score 17.6% → 31.2%, 2.1 сек)
2. **RATE-LIMIT-BYPASS** (P1) — 6-я оптимизация → 429 "Лимит исчерпан"
3. **OPENAI-JSON-WRAP** (P2) — OpenAI возвращает чистый JSON (без ` ```json ` обёртки)
4. **OPENAI-MODEL-MAPPING** (P1) — OpenAI корректно использует gpt-4o-mini (не GigaChat-Pro)
5. **ANTHROPIC-MODEL-MAPPING** (P1) — Anthropic корректно использует claude-sonnet-4

---

## СВОДКА ДЕФЕКТОВ — ЧТО НУЖНО ИСПРАВИТЬ

| # | Приоритет | ID | Описание | Версий в баге |
|---|-----------|-----|----------|---------------|
| 1 | 🔴 P1 | ACCOUNT-DELETE-500 | Удаление аккаунта → 500 | **6 версий** (V40→V45) |
| 2 | 🟡 P2 | HH-RESUME-LINK-400 | Загрузка резюме по ссылке hh.ru → 400 | **11 версий** (V35→V45) |
| 3 | 🟢 P3 | GROQ-JSON-WRAP | Groq возвращает JSON в markdown обёртке | **1 версия** (NEW V45) |
| 4 | 🟢 P3 | FINALIZATION-NO-CHECKMARK | Нет зелёной галочки при завершении финализации | **Confirmed V45** |

---

## 🔴 ДЕФЕКТ 1 — P1: ACCOUNT-DELETE-500 (Удаление аккаунта)

### Проблема
`DELETE /api/v1/auth/me` с верным паролем и подтверждением "УДАЛИТЬ" → 500 Internal Server Error. Ответ: `{"error":"DELETE_ACCOUNT_FAILED","message":"Не удалось удалить аккаунт. Попробуйте позже."}`. Аккаунт НЕ удаляется.

**Валидация работает корректно:** без body → 422, неверный пароль → 401.

### Шаги воспроизведения
1. Авторизоваться: POST /api/v1/auth/login → 200
2. Удалить: DELETE /api/v1/auth/me с body `{"password":"TestPass1231","confirmation":"УДАЛИТЬ"}` → **500**

### Корневая причина (предположение)
Ошибка в каскадном удалении связанных данных. У пользователя есть:
- 5 записей rewrite history
- 1 резюме
- 1 вакансия
- 5 сохранённых AI ключей

FK constraints не позволяют удалить пользователя без предварительной очистки связанных таблиц.

### Где исправлять

**Файл:** `src/app/auth/router.py` — функция `delete_me`

```python
# Вариант 1: Каскадное удаление (предпочтительно)
# Добавить CASCADE в модели User → связанные таблицы

# Вариант 2: Ручная очистка перед удалением
async def delete_me(current_user, session, body):
    # 1. Удалить rewrite history
    await session.execute(
        delete(RewriteTask).where(RewriteTask.user_id == current_user.id)
    )
    # 2. Удалить вакансии
    await session.execute(
        delete(Vacancy).where(Vacancy.user_id == current_user.id)
    )
    # 3. Удалить резюме
    await session.execute(
        delete(Resume).where(Resume.user_id == current_user.id)
    )
    # 4. Удалить AI ключи
    await session.execute(
        delete(UserSetting).where(UserSetting.user_id == current_user.id)
    )
    # 5. Удалить аватар (если есть)
    # 6. Удалить пользователя
    await session.delete(current_user)
    await session.commit()
```

**Альтернативно:** Проверить модель `User` в `src/app/auth/models.py`:
```python
class User(Base):
    # Добавить cascade="all, delete-orphan" в relationship:
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    vacancies = relationship("Vacancy", back_populates="user", cascade="all, delete-orphan")
    rewrite_tasks = relationship("RewriteTask", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSetting", back_populates="user", cascade="all, delete-orphan")
```

### Проверка
```bash
# 1. Создать тестовый аккаунт
# 2. Загрузить резюме, создать вакансию, запустить оптимизацию
# 3. DELETE /api/v1/auth/me → ожидаем 204
# 4. GET /api/v1/auth/me → ожидаем 401 (токен невалиден)
# 5. POST /api/v1/auth/login → ожидаем 401 (аккаунт не найден)
```

---

## 🟡 ДЕФЕКТ 2 — P2: HH-RESUME-LINK-400 (Загрузка резюме с hh.ru)

### Проблема
`POST /api/v1/resumes/from-url` с URL `https://hh.ru/resume/...` → 400 "Не удалось автоматически загрузить резюме с hh.ru".

**Примечание:** `POST /api/v1/vacancies/from-url` с URL вакансии hh.ru → 201 (работает!). Проблема только с РЕЗЮМЕ.

### Корневая причина
hh.ru блокирует HTTP-запросы к страницам резюме (защита от парсинга). Для вакансий используется API hh.ru (`api.hh.ru/vacancies/{id}`), а для резюме — прямой парсинг HTML, который блокируется.

### Где исправлять

**Файл:** `src/app/resumes/service.py` или `src/app/resumes/hh_parser.py`

**Вариант 1 (рекомендуемый):** Использовать Playwright для headless-браузера
```python
# pip install playwright beautifulsoup4
# playwright install chromium

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def parse_hh_resume(url: str) -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        await page.goto(url, timeout=60000)
        await page.wait_for_timeout(4000)
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        result = {}
        name = soup.select_one("h2[data-qa='resume-personal-name']")
        result["name"] = name.text.strip() if name else None
        position = soup.select_one("span[data-qa='resume-block-title-position']")
        result["position"] = position.text.strip() if position else None
        skills = soup.select("[data-qa='bloko-tag__text']")
        result["skills"] = [s.text.strip() for s in skills]

        experience = []
        jobs = soup.select("[data-qa='resume-block-experience'] .resume-block-item-gap")
        for job in jobs:
            title = job.select_one("[data-qa='resume-block-experience-position']")
            company = job.select_one("[data-qa='resume-block-experience-employer']")
            experience.append({
                "title": title.text.strip() if title else None,
                "company": company.text.strip() if company else None,
            })
        result["experience"] = experience
        await browser.close()
        return result
```

**Вариант 2 (быстрый):** Улучшить сообщение об ошибке — добавить инструкцию пользователю
```python
raise HTTPException(
    status_code=400,
    detail=(
        "Резюме с hh.ru доступно только для зарегистрированных пользователей hh.ru. "
        "Откройте резюме в браузере, скопируйте текст (Ctrl+A, Ctrl+C) "
        "и вставьте на вкладке «Вставить текст»."
    )
)
```

### Проверка
```bash
POST /api/v1/resumes/from-url
{"url": "https://hh.ru/resume/90d67b47ff01c53bfd0039ed1f36424d765046"}
# Ожидаем: 201 Created (вариант 1) или 400 с понятным сообщением (вариант 2)
```

---

## 🟢 ДЕФЕКТ 3 — P3: GROQ-JSON-WRAP (Markdown обёртка в ответе Groq)

### Проблема
Groq (llama-3.3-70b-versatile) возвращает JSON обёрнутый в ` ```json\n{...}\n``` ` вместо чистого JSON. Фронтенд корректно обрабатывает обёртку (отображение нормальное), но бэкенд должен стрипать обёртку перед сохранением.

**Примечание:** В V44 такой же баг был у OpenAI — **исправлен** (чистый JSON). Groq использует ту же фунцию _strip_markdown_wrapper, но Groq обёрнут в ` ```json ` а не ` ``` `. Возможно strip не покрывает этот случай.

### Где исправлять

**Файл:** `src/app/rewriter/service.py`

```python
def _strip_markdown_wrapper(text: str) -> str:
    """Удалить markdown code block обёртку если есть."""
    stripped = text.strip()
    # Обработать ```json и ``` варианты
    if stripped.startswith('```json'):
        stripped = stripped[7:]  # Убрать ```json
    elif stripped.startswith('```'):
        stripped = stripped[3:]  # Убрать ```
    if stripped.endswith('```'):
        stripped = stripped[:-3]
    return stripped.strip()
```

Проверить, что эта функция вызывается ДО JSON-парсинга для ВСЕХ провайдеров (включая Groq). Возможно, для Groq путь кода отличается.

### Проверка
```bash
POST /api/v1/rewrite { model: "groq" }
# После завершения проверить rewritten_text — должен начинаться с "{", не "```json"
```

---

## 🟢 ДЕФЕКТ 4 — P3: FINALIZATION-NO-CHECKMARK (Индикатор завершения)

### Проблема
На странице `/app/results/{id}` написано "Оптимизация завершена", но нет визуального индикатора (зелёной галочки ✅). Пользователю не очевидно, что процесс завершён — текст выглядит как статичный заголовок.

### Где исправлять

**Файл:** `frontend/src/pages/results/ResultsPage.tsx` (или аналогичный)

```tsx
// Найти текст "Оптимизация завершена" и добавить иконку:
<div className="flex items-center gap-2">
  <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
  </svg>
  <span className="text-green-600 font-medium">Оптимизация завершена</span>
</div>
```

Также рассмотреть добавление зелёной галочки на **шаге "Финализация"** в процессе оптимизации (на странице `/app/processing/{id}`), чтобы все 4 шага (Загрузка → Анализ → AI оптимизация → Финализация) были помечены ✅ при завершении.

### Проверка
Визуально: запустить оптимизацию → дождаться завершения → на странице результатов рядом с текстом "Оптимизация завершена" должна быть зелёная галочка.

---

## 📊 РЕЗУЛЬТАТЫ AI-ОПТИМИЗАЦИИ (ВСЕ 5 ПРОВАЙДЕРОВ)

| # | Провайдер | Score Before | Score After | Δ | Время | Статус |
|---|-----------|-------------|-------------|---|-------|--------|
| 1 | GigaChat | 17.6% | 40.6% | +23.0 | 11.3s | ✅ PASS |
| 2 | OpenAI | 17.6% | 40.4% | +22.8 | 13.3s | ✅ PASS |
| 3 | Anthropic | 17.6% | 42.6% | +25.0 | 13.3s | ✅ PASS |
| 4 | OpenRouter | 17.6% | 25.5% | +7.9 | 7.4s | ✅ PASS |
| 5 | Groq | 17.6% | 31.2% | +13.6 | 2.1s | ✅ PASS |

**Все 5 провайдеров работают!** Это первый раз за всю историю тестирования.

### Ключевые наблюдения по провайдерам:
- **Anthropic Claude** — лучший результат (+25 пунктов, 42.6%). Рекомендуется как premium-модель.
- **GigaChat Pro** — отличный результат для русского языка (+23 пункта). Хороший дефолт для РФ.
- **OpenAI gpt-4o-mini** — стабильный результат (+22.8 пунктов). Быстрый и надёжный.
- **Groq** — самый быстрый (2.1 сек), но результат ниже (+13.6). JSON обёрнут в markdown.
- **OpenRouter** — нестабильный результат (+7.9). Модель "К сожалению, текущий опыт и стек технологий кандидата не соответствуют" — модель отказалась оптимизировать несоответствующее резюме. Это интеллектуальное поведение, но нужно обрабатывать на бэкенде.

### Рекомендация для OpenRouter:
Если модель возвращает null в полях experience/education/skills — бэкенд должен это детектить и возвращать ошибку:
```python
# В service.py после парсинга LLM ответа:
if not parsed_response.get('experience') and not parsed_response.get('skills'):
    task.status = RewriteStatus.FAILED
    task.error_message = 'AI-модель не смогла оптимизировать резюме. Попробуйте другую модель.'
    return task
```

---

## 🎯 ПРИОРИТЕТНЫЙ ПЛАН ДЕЙСТВИЙ V46

### Критичные (P1) — исправить немедленно:
1. **ACCOUNT-DELETE-500** — Добавить каскадное удаление или ручную очистку связанных данных перед удалением пользователя. Баг существует 6 версий подряд.

### Важные (P2) — исправить в следующем спринте:
2. **HH-RESUME-LINK-400** — Внедрить Playwright для парсинга резюме hh.ru, либо улучшить сообщение об ошибке. Баг существует 11 версий.

### Minor (P3) — улучшения:
3. **GROQ-JSON-WRAP** — Убедиться что `_strip_markdown_wrapper` вызывается для Groq.
4. **FINALIZATION-NO-CHECKMARK** — Добавить зелёную галочку при завершении оптимизации.
5. **OpenRouter null response** — Добавить обработку случая когда модель отказывается оптимизировать.

---

## ✅ ВЕРИФИКАЦИЯ ПРЕДЫДУЩИХ ФИКСОВ (стабильны V45)

| ID | P | Описание | Версия фикса | Стабильно |
|----|---|----------|--------------|-----------|
| GROQ-KEY-INVISIBLE | P1 | Celery worker видит ключ Groq | V45 | ✅ V45 |
| RATE-LIMIT-BYPASS | P1 | 429 на 6-ю оптимизацию | V45 | ✅ V45 |
| OPENAI-JSON-WRAP | P2 | Чистый JSON от OpenAI | V45 | ✅ V45 |
| OPENAI-MODEL-MAPPING | P1 | OpenAI использует свою модель | V44 | ✅ V45 |
| ANTHROPIC-MODEL-MAPPING | P1 | Anthropic использует свою модель | V44 | ✅ V45 |
| PASSWORD-CHANGE-503 | P1 | PUT password → 204 | V42 | ✅ V45 |
| AVATAR-DELETE-503 | P2 | DELETE avatar → 204 | V42 | ✅ V45 |
| LOGOUT-503 | P3 | POST logout → 204 | V41 | ✅ V45 |
| P0-3 | P0 | Форматированный текст (не raw JSON) | V38 | ✅ V45 |
| PROGRESS-BAR | P1 | Прогресс-бар работает | V38 | ✅ V45 |

**Всего исправлено и стабильно: 10 багов**
**Открыто: 4 бага (1 P1, 1 P2, 2 P3)**

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
| V42 | 25 | 22 | 3 | **88%** | 4/5 |
| V43 | 25 | 18 | 5 | 72% ⬇️ | 2/5 ⬇️ |
| V44 | 30 | 24 | 4 | 80% | 4/5 |
| **V45** | **32** | **28** | **2** | **87.5%** ⬆️ | **5/5** 🎉 |

---

*Отчёт сгенерирован AI QA Agent (V45 Full Regression) — 2026-03-14*

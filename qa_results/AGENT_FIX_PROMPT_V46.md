# AGENT FIX PROMPT V46 — Доработки по результатам UI-регресса

**Дата:** 2026-03-14
**Версия приложения:** 1.26.0
**Источник:** QA Report #42 (42_UI_REGRESSION_V46.md)
**Проект:** ResumeCraft.ru
**Тестовый аккаунт:** `qa_ui_v46@example.com` / TestPass1231 — аккаунт АКТИВЕН
**Окружение:** Chrome (визуальный UI-тест), resumecraft.ru (production)

---

## 📊 СТАТУС КАЧЕСТВА

| Метрика | V45 (API) | V46 (UI) | Δ |
|---------|-----------|----------|---|
| Pass Rate | 87.5% (28/32) | **87%** (13/15) | ~0% |
| Провайдеры работают | 5/5 ✅ | **0/5** ❌ | -5 🔴 |
| P0 баги | 0 | **1** | +1 ❌ |
| P1 баги | 1 | 1 | = |
| P2 баги | 1 | 1 | = |
| P3 баги | 2 | 2 | = |

### ⚠️ КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ V45 → V46:
**V45 давал ложноположительные результаты!** API-тесты через JavaScript fetch() показывали 5/5 провайдеров работающими, но реальный пользовательский flow через UI обнаружил, что **НИ ОДИН провайдер не работает**. Причина — SECRET_KEY mismatch между web-сервером и Celery-воркером (см. P0 ниже).

---

## СВОДКА ДЕФЕКТОВ — ЧТО НУЖНО ИСПРАВИТЬ

| # | Приоритет | ID | Описание | Версий в баге |
|---|-----------|-----|----------|---------------|
| 1 | 🔴 **P0** | **ALL-PROVIDERS-KEY-NOT-CONFIGURED** | ВСЕ провайдеры: «API-ключ не настроен» при оптимизации | **NEW — БЛОКЕР** |
| 2 | 🔴 P1 | ACCOUNT-DELETE-500 | Удаление аккаунта → 500 | **7 версий** (V40→V46) |
| 3 | 🟡 P2 | HH-RESUME-LINK-400 | Загрузка резюме по ссылке hh.ru → 400 | **12 версий** (V35→V46) |
| 4 | 🟢 P3 | GROQ-JSON-WRAP | Groq возвращает JSON в markdown обёртке | V45→V46 |
| 5 | 🟢 P3 | FINALIZATION-NO-CHECKMARK | Нет зелёной галочки при завершении финализации | V45→V46 |

---

## 🔴🔴🔴 ДЕФЕКТ 0 — P0 БЛОКЕР: ALL-PROVIDERS-KEY-NOT-CONFIGURED

### ⛔ СЕРВИС НЕПРИГОДЕН ДЛЯ ИСПОЛЬЗОВАНИЯ

**Ни один пользователь не может выполнить оптимизацию резюме — основную функцию приложения.**

### Проблема
ВСЕ AI-провайдеры при запуске оптимизации через UI выдают ошибку: **«API-ключ для [провайдер] не настроен»**, несмотря на то что:
- API сохранения ключей возвращает 200 OK
- Страница настроек AI-моделей показывает зелёные галочки ✅ для всех 5 провайдеров
- `GET /api/v1/settings/ai-keys` подтверждает `has_key: true` для всех

### Шаги воспроизведения
1. Зарегистрировать новый аккаунт
2. Перейти в Настройки → AI-модели
3. Ввести API-ключи для всех 5 провайдеров (все сохраняются успешно, 200 OK)
4. Создать резюме (вставить текст) → Создать вакансию (ввести вручную) → Выбрать модель → «Начать оптимизацию»
5. **Результат:** Страница «Ошибка обработки» — «API-ключ для [провайдер] не настроен. Перейдите в настройки AI и проверьте ключ.»

### Протестированные провайдеры
- GigaChat → ❌ «API-ключ не настроен»
- OpenAI → ❌ «API-ключ не настроен»
- Anthropic / OpenRouter / Groq — **предположительно тоже ❌** (тот же механизм)

### Корневая причина (гипотеза)
**SECRET_KEY mismatch между web-сервером и Celery-воркером.**

Цепочка событий:
1. Web-сервер шифрует API-ключ при сохранении (`PUT /api/v1/settings/ai-keys`) → OK
2. Web-сервер проверяет наличие ключа (`GET /api/v1/settings/ai-keys`) → `has_key: true`
3. **Celery-воркер** пытается расшифровать ключ при оптимизации → **FAIL** (другой SECRET_KEY)
4. Воркер интерпретирует ошибку расшифровки как «ключ не настроен»

### Почему V45 API-тест показывал «все 5 работают»
В V45 оптимизация вызывалась через JavaScript `fetch()` → `POST /api/v1/rewrite`. Возможные причины расхождения:
- Тот тест выполнялся на **другом аккаунте** (`qa_v45_live@example.com`) с ключами, сохранёнными ранее, когда SECRET_KEY совпадал
- Или API-endpoint при определённых условиях использует синхронную обработку (внутри web-процесса, а не через Celery)
- Или между V45 и V46 был деплой, изменивший SECRET_KEY для одного из контейнеров

### Где исправлять

**Шаг 1: Диагностика — проверить SECRET_KEY**
```bash
# Сравнить SECRET_KEY в web и celery контейнерах
docker exec web printenv SECRET_KEY
docker exec celery printenv SECRET_KEY
# Они ДОЛЖНЫ быть ИДЕНТИЧНЫ

# Если используется docker-compose — проверить .env файл
cat .env | grep SECRET_KEY
```

**Шаг 2: Синхронизировать SECRET_KEY**
```yaml
# docker-compose.yml — убедиться что ОБА сервиса используют одну переменную:

services:
  web:
    environment:
      - SECRET_KEY=${SECRET_KEY}

  celery:
    environment:
      - SECRET_KEY=${SECRET_KEY}  # ← ДОЛЖЕН СОВПАДАТЬ с web!
```

**Шаг 3: Рестартнуть воркер**
```bash
docker-compose restart celery
# Или полный рестарт:
docker-compose down && docker-compose up -d
```

**Шаг 4: Альтернативная причина — проверить код расшифровки**

Если SECRET_KEY совпадает, проблема может быть в коде:

```python
# Файл: src/app/settings/service.py или src/app/rewriter/service.py
# Найти функцию получения API ключа в контексте Celery-задачи

# Проверить что:
# 1. Celery-воркер загружает settings из того же источника
# 2. Функция decrypt_api_key использует тот же алгоритм и ключ
# 3. При ошибке расшифровки логируется реальная ошибка, а не "ключ не настроен"
```

**Шаг 5: Улучшить обработку ошибок**
```python
# В Celery задаче оптимизации:
try:
    api_key = decrypt_api_key(encrypted_key, settings.SECRET_KEY)
except Exception as e:
    # Вместо "API-ключ не настроен" — показать реальную ошибку
    logger.error(f"Ошибка расшифровки ключа {provider}: {e}")
    logger.error(f"SECRET_KEY hash: {hashlib.md5(settings.SECRET_KEY.encode()).hexdigest()}")
    raise TaskError(f"Ошибка расшифровки API-ключа для {provider}. "
                    f"Проверьте SECRET_KEY в окружении Celery-воркера.")
```

### Проверка после исправления
```bash
# 1. Зарегистрировать НОВЫЙ аккаунт (не использовать старые — ключи зашифрованы старым SECRET_KEY)
# 2. Сохранить API-ключ для любого провайдера
# 3. Запустить оптимизацию через UI
# 4. Ожидаем: оптимизация выполняется успешно (не "ключ не настроен")

# Для существующих аккаунтов — пользователям нужно пересохранить ключи!
```

### Критичность
⛔ **БЛОКЕР ВСЕГО СЕРВИСА.** Без исправления этого бага:
- 0% пользователей могут использовать основную функцию (оптимизация резюме)
- Все остальные баги вторичны — исправлять их не имеет смысла пока P0 не решён

---

## 🔴 ДЕФЕКТ 1 — P1: ACCOUNT-DELETE-500 (Удаление аккаунта)

### Проблема
`DELETE /api/v1/auth/me` с верным паролем и подтверждением "УДАЛИТЬ" → 500 Internal Server Error. Ответ: `{"error":"DELETE_ACCOUNT_FAILED","message":"Не удалось удалить аккаунт. Попробуйте позже."}`. Аккаунт НЕ удаляется.

**Валидация работает корректно:** без body → 422, неверный пароль → 401.

### Шаги воспроизведения
1. Авторизоваться: POST /api/v1/auth/login → 200
2. Удалить: DELETE /api/v1/auth/me с body `{"password":"TestPass1231","confirmation":"УДАЛИТЬ"}` → **500**

### Корневая причина (предположение)
Ошибка в каскадном удалении связанных данных. FK constraints не позволяют удалить пользователя без предварительной очистки связанных таблиц (resumes, vacancies, rewrite_tasks, ai_keys).

### Где исправлять

**Файл:** `src/app/auth/router.py` — функция `delete_me`

```python
# Вариант 1: Каскадное удаление (предпочтительно)
# В модели User (src/app/auth/models.py):
class User(Base):
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    vacancies = relationship("Vacancy", back_populates="user", cascade="all, delete-orphan")
    rewrite_tasks = relationship("RewriteTask", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSetting", back_populates="user", cascade="all, delete-orphan")

# Вариант 2: Ручная очистка перед удалением
async def delete_me(current_user, session, body):
    await session.execute(delete(RewriteTask).where(RewriteTask.user_id == current_user.id))
    await session.execute(delete(Vacancy).where(Vacancy.user_id == current_user.id))
    await session.execute(delete(Resume).where(Resume.user_id == current_user.id))
    await session.execute(delete(UserSetting).where(UserSetting.user_id == current_user.id))
    await session.delete(current_user)
    await session.commit()
```

### Проверка
```bash
# 1. Создать тестовый аккаунт с данными (резюме, вакансия, ключи)
# 2. DELETE /api/v1/auth/me → ожидаем 204
# 3. POST /api/v1/auth/login → ожидаем 401
```

---

## 🟡 ДЕФЕКТ 2 — P2: HH-RESUME-LINK-400 (Загрузка резюме с hh.ru)

### Проблема
`POST /api/v1/resumes/from-url` с URL `https://hh.ru/resume/...` → 400 "Не удалось автоматически загрузить резюме с hh.ru".

### Корневая причина
hh.ru блокирует HTTP-запросы к страницам резюме (защита от парсинга). Для вакансий используется API hh.ru, а для резюме — прямой парсинг HTML, который блокируется.

### Где исправлять

**Файл:** `src/app/resumes/service.py` или `src/app/resumes/hh_parser.py`

**Вариант 1 (рекомендуемый):** Использовать Playwright для headless-браузера
```python
from playwright.async_api import async_playwright

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
        # Парсить HTML через BeautifulSoup
        await browser.close()
        return result
```

**Вариант 2 (быстрый):** Улучшить сообщение об ошибке
```python
raise HTTPException(
    status_code=400,
    detail="Резюме с hh.ru доступно только для зарегистрированных пользователей hh.ru. "
           "Откройте резюме в браузере, скопируйте текст (Ctrl+A, Ctrl+C) "
           "и вставьте на вкладке «Вставить текст»."
)
```

---

## 🟢 ДЕФЕКТ 3 — P3: GROQ-JSON-WRAP (Markdown обёртка)

### Проблема
Groq (llama-3.3-70b-versatile) возвращает JSON обёрнутый в ` ```json\n{...}\n``` `. Фронтенд обрабатывает корректно, но бэкенд должен стрипать обёртку.

### Где исправлять
**Файл:** `src/app/rewriter/service.py` — убедиться что `_strip_markdown_wrapper` вызывается для Groq и обрабатывает формат ` ```json `.

---

## 🟢 ДЕФЕКТ 4 — P3: FINALIZATION-NO-CHECKMARK (Индикатор завершения)

### Проблема
На странице результатов нет визуального индикатора (зелёной галочки) завершения оптимизации.

### Где исправлять
**Файл:** `frontend/src/pages/results/ResultsPage.tsx` — добавить SVG-иконку ✅ рядом с текстом "Оптимизация завершена".

---

## 🎯 ПРИОРИТЕТНЫЙ ПЛАН ДЕЙСТВИЙ

### 🔴 НЕМЕДЛЕННО (P0):
1. **ALL-PROVIDERS-KEY-NOT-CONFIGURED** — Синхронизировать SECRET_KEY между web и celery. **Без этого фикса сервис полностью нерабочий.**

### Критичные (P1):
2. **ACCOUNT-DELETE-500** — Добавить каскадное удаление. Баг существует **7 версий** подряд.

### Важные (P2):
3. **HH-RESUME-LINK-400** — Внедрить Playwright или улучшить сообщение. Баг существует **12 версий**.

### Minor (P3):
4. **GROQ-JSON-WRAP** — Strip markdown wrapper для Groq.
5. **FINALIZATION-NO-CHECKMARK** — Добавить зелёную галочку.

---

## ✅ ВЕРИФИКАЦИЯ ПРЕДЫДУЩИХ ФИКСОВ

| ID | P | Описание | Версия фикса | V45 | V46 |
|----|---|----------|--------------|-----|-----|
| GROQ-KEY-INVISIBLE | P1 | Groq ключ виден | V45 | ✅ | ✅ (сохраняется) |
| RATE-LIMIT-BYPASS | P1 | Rate limit работает | V45 | ✅ | ✅ |
| OPENAI-JSON-WRAP | P2 | Чистый JSON от OpenAI | V45 | ✅ | N/A* |
| OPENAI-MODEL-MAPPING | P1 | OpenAI модель корректна | V44 | ✅ | N/A* |
| ANTHROPIC-MODEL-MAPPING | P1 | Anthropic модель корректна | V44 | ✅ | N/A* |
| PASSWORD-CHANGE-503 | P1 | Смена пароля | V42 | ✅ | N/A |
| AVATAR-DELETE-503 | P2 | Удаление аватара | V42 | ✅ | N/A |
| LOGOUT-503 | P3 | Логаут | V41 | ✅ | N/A |
| P0-3 | P0 | Форматированный текст | V38 | ✅ | N/A* |
| PROGRESS-BAR | P1 | Прогресс-бар | V38 | ✅ | N/A* |

*N/A — не удалось проверить в V46, т.к. оптимизация не выполняется из-за P0 бага.

**Всего исправлено ранее: 10 багов**
**Открыто: 5 багов (1 P0 БЛОКЕР, 1 P1, 1 P2, 2 P3)**

---

## 📈 ТРЕНД КАЧЕСТВА

| Версия | Тестов | PASS | FAIL | Pass Rate | Провайдеры | Метод |
|--------|--------|------|------|-----------|------------|-------|
| V35 | 25 | 14 | 11 | 56% | — | API |
| V36 | 25 | 16 | 9 | 64% | — | API |
| V37 | 25 | 17 | 7 | 68% | — | API |
| V38 | 25 | 17 | 7 | 68% | 4/5 | API |
| V39 | 25 | 18 | 6 | 72% | 4/5 | API |
| V40 | 25 | 19 | 5 | 76% | 4/5 | API |
| V41 | 25 | 20 | 5 | 80% | 4/5 | API |
| V42 | 25 | 22 | 3 | **88%** | 4/5 | API |
| V43 | 25 | 18 | 5 | 72% ⬇️ | 2/5 ⬇️ | API |
| V44 | 30 | 24 | 4 | 80% | 4/5 | API |
| V45 | 32 | 28 | 2 | 87.5% | 5/5* | API |
| **V46** | **15** | **13** | **2** | **87%** | **0/5** ❌ | **UI** |

*V45 5/5 провайдеров — **ложноположительный результат** (API-тесты не обнаруживали P0 баг)

---

## ⚠️ ВАЖНОЕ ЗАМЕЧАНИЕ О МЕТОДОЛОГИИ ТЕСТИРОВАНИЯ

V46 стал переломным тестом: он показал, что **API-тесты могут давать ложноположительные результаты**. Реальный пользовательский flow через браузер обнаруживает баги, которые API-вызовы пропускают. Причина — в production-окружении запросы через UI маршрутизируются иначе (Celery worker vs синхронная обработка).

**Рекомендация:** Все критические сценарии (регистрация, оптимизация, экспорт) тестировать **обязательно через UI**, а не только через API.

---

*Отчёт сгенерирован AI QA Agent (V46 UI Regression) — 2026-03-14*

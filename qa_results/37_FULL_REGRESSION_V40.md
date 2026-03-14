# QA Report #38 — FULL REGRESSION V40

**Дата:** 2026-03-13
**Проект:** ResumeCraft.ru
**Тестовый аккаунт:** qa_v40_test@example.com / TestPass1232 (пароль сменён в ходе теста с TestPass1231)
**Базовый документ:** AGENT_FIX_PROMPT_V39.md (14/22 fixed, 64%)
**Цель:** Полная регрессия всех функций + ретест всех активных дефектов V39

---

## СВОДКА РЕЗУЛЬТАТОВ V40

| Метрика | Значение |
|---------|----------|
| Всего тестов | 25 |
| ✅ PASS | 19 |
| ❌ FAIL | 5 |
| ⏸ BLOCKED | 1 |
| Новых дефектов | 1 (ACCOUNT-DELETE-500-REGRESSION) |
| Регрессий | 1 (ACCOUNT-DELETE-500 вернулся) |
| Активных дефектов всего | 8 |
| Исправлено всего | 15 из 23 (65%) |

---

## 1. РЕГИСТРАЦИЯ И ВХОД

### 1.1 Регистрация нового аккаунта
- **URL:** /auth → "Регистрация"
- **Данные:** QA V40 Tester / qa_v40_test@example.com / TestPass1231
- **API:** POST /api/v1/auth/register → **201 Created** ✅
- **Результат:** ✅ PASS

### 1.2 Вход в аккаунт
- **API:** POST /api/v1/auth/login → **200 OK** ✅
- **Редирект:** → /app/dashboard ✅
- **Результат:** ✅ PASS

---

## 2. ЗАГРУЗКА РЕЗЮМЕ

### 2.1 Вставить текст (5 раз — для каждого провайдера)
- **URL:** /app/upload → "Вставить текст"
- **API:** POST /api/v1/resumes/from-text → **201 Created** (все 5 раз) ✅
- **Имена:** GigaChat Test V40, OpenAI Test V40, Anthropic Test V40, OpenRouter Test V40, Groq Test V40
- **Результат:** ✅ PASS

### 2.2 Ссылка hh.ru (реальное резюме)
- **URL:** /app/upload → "Ссылка hh.ru"
- **Ввод:** https://hh.ru/resume/90d67b47ff01c53bfd0039ed1f36424d765046
- **API:** POST /api/v1/resumes/from-url → **400 Bad Request** ❌
- **Graceful degradation:** "Не удалось автоматически загрузить резюме с hh.ru. Скопируйте текст резюме вручную на вкладке «Вставить текст»." ✅
- **Результат:** ❌ FAIL — **HH-RESUME-LINK-400 CONFIRMED V40**

---

## 3. ВАКАНСИИ

### 3.1 Поиск вакансий hh.ru
- **URL:** /app/vacancy → "Поиск hh.ru"
- **Поиск:** "Frontend разработчик", город Москва
- **API:** GET /api/v1/vacancies/search → **200 OK** ✅
- **Результат:** ✅ PASS

### 3.2 Выбор вакансии
- **API:** POST /api/v1/vacancies → **201 Created** ✅
- **Результат:** ✅ PASS

### 3.3 Вставить URL — невалидный URL (VACANCY-URL-OBJECT-ERROR retest)
- **URL:** /app/vacancy → "Вставить URL"
- **Ввод:** https://invalid-url.com/not-a-vacancy
- **API:** POST /api/v1/vacancies/from-url → **400 Bad Request**
- **UI:** "Введите корректную ссылку на вакансию hh.ru (например, https://hh.ru/vacancy/123456)" ✅
- **НЕТ [object Object]** — ошибка отображается корректно
- **VACANCY-URL-OBJECT-ERROR fix confirmed** ✅
- **Результат:** ✅ PASS

### 3.4 VACANCY-TITLE-002 — автозаполнение должности
- **Поведение:** Поле "Должность" автозаполняется именем резюме (напр. "Anthropic Test V40")
- **Workaround:** Пользователь может изменить вручную перед поиском
- **Результат:** ⚠️ KNOWN ISSUE — подтверждено V40, есть workaround

---

## 4. AI-МОДЕЛИ И API КЛЮЧИ

### 4.1 Сохранение API ключей (5 провайдеров)
- **URL:** /app/settings → "AI-модели"
- **Провайдеры:** GigaChat, OpenAI, Anthropic, OpenRouter, Groq
- **API:** PUT /api/v1/settings/api-keys → **200 OK** (все 5) ✅
- **Результат:** ✅ PASS

---

## 5. ОПТИМИЗАЦИЯ РЕЗЮМЕ (5 моделей)

### 5.1 GigaChat Pro
- **Модель:** GigaChat-Pro
- **API:** POST /rewrite → 202, GET /status (poll), GET /result → 200 ✅
- **Результат:** Match 29% → 50%, ATS Score: D
- **Статус:** ✅ PASS

### 5.2 OpenAI
- **Модель:** o4-mini-2025-04-16
- **API:** POST /rewrite → 202, GET /status (poll), GET /result → 200 ✅
- **Результат:** Match 29% → 46%, ATS Score: D
- **Статус:** ✅ PASS

### 5.3 Anthropic Claude
- **Модель:** claude-sonnet-4-6
- **API:** POST /rewrite → 202, GET /status (poll), GET /result → 200 ✅
- **Результат:** Match 29% → 57%, ATS Score: C
- **Статус:** ✅ PASS

### 5.4 OpenRouter
- **Модель:** ai21/jamba-large-1.7
- **API:** POST /rewrite → 202, GET /status (poll), GET /result → 200 ✅
- **Результат:** Match 29% → 52%, ATS Score: C
- **Статус:** ✅ PASS

### 5.5 Groq allam-2-7b (GROQ-ALLAM-502 retest)
- **Модель:** allam-2-7b
- **API:** POST /rewrite → 202, GET /status → error (no /result)
- **UI:** "Ошибка обработки — AI-провайдер временно недоступен"
- **Счётчик:** остался 4/5
- **Результат:** ❌ FAIL — **GROQ-ALLAM-502 CONFIRMED V40**

---

## 6. ЭКСПОРТ

### 6.1 Экспорт DOCX
- **API:** GET /api/v1/export/{id}/docx → **200 OK** ✅
- **Результат:** ✅ PASS

### 6.2 Экспорт PDF
- **API:** GET /api/v1/export/{id}/pdf → **200 OK** ✅
- **Результат:** ✅ PASS

### 6.3 Экспорт TXT
- **API:** GET /api/v1/export/{id}/txt → **200 OK** ✅
- **Результат:** ✅ PASS

---

## 7. СТРАНИЦЫ ПРИЛОЖЕНИЯ

### 7.1 Мои резюме (/app/resumes)
- **Содержимое:** 6 резюме (Groq=Черновик, остальные 4=Оптимизировано, 1=Черновик)
- **Результат:** ✅ PASS

### 7.2 История (/app/history)
- **Содержимое:** 5 оптимизаций:
  - Groq · allam-2-7b — ⚠️ AI-провайдер временно недоступен
  - OpenRouter · ai21/jamba-large-1.7 — Match: 29% → 52%, ATS: C
  - Anthropic · claude-sonnet-4-6 — Match: 29% → 57%, ATS: C
  - OpenAI · o4-mini-2025-04-16 — Match: 29% → 46%, ATS: D
  - GigaChat · GigaChat-Pro — Match: 29% → 50%, ATS: D
- **Результат:** ✅ PASS

### 7.3 Дашборд (/app/dashboard)
- **Содержимое:** Загружено резюме: 6, Оптимизаций: 4, Успешных: 4 из 5, Средний Match Score: 51%
- **Результат:** ✅ PASS

---

## 8. ПРОФИЛЬ — АВАТАР

### 8.1 Загрузка аватара
- **URL:** /app/settings/profile
- **Метод:** JavaScript Canvas → Blob → File → DataTransfer → input.files
- **API:** POST /api/v1/auth/me/avatar → **200 OK** ✅
- **AVATAR-DELETE-BTN-UX fix confirmed** ✅ (кнопка "Удалить" появилась)
- **Результат:** ✅ PASS

### 8.2 Удаление аватара (AVATAR-DELETE-503 retest)
- **API:** DELETE /api/v1/auth/me/avatar → **503 Service Unavailable** ❌
- **Поведение на сервере:** Аватар УДАЛЁН (показывает инициалы "QV", кнопка "Удалить" пропала)
- **AVATAR-DELETE-503 CONFIRMED V40** (5-я версия подряд: V36, V37, V38, V39, V40)
- **Результат:** ❌ FAIL

---

## 9. БЕЗОПАСНОСТЬ — СМЕНА ПАРОЛЯ

### 9.1 Смена пароля (PASSWORD-CHANGE-503 retest)
- **URL:** /app/settings/security
- **Ввод:** Текущий: TestPass1231, Новый: TestPass1232, Подтверждение: TestPass1232
- **API:** PUT /api/v1/auth/me/password → **503 Service Unavailable** ❌
- **Побочный эффект:** POST /api/v1/auth/logout → **503** (LOGOUT-503 confirmed)
- **Пользователь выброшен на /auth**
- **Проверка:**
  - Логин с СТАРЫМ паролем TestPass1231 → **401 Unauthorized** ✅ (отклонён)
  - Логин с НОВЫМ паролем TestPass1232 → **200 OK** ✅ (принят)
- **Вывод:** Пароль УСПЕШНО изменён на сервере, несмотря на 503
- **PASSWORD-CHANGE-503 CONFIRMED V40**
- **LOGOUT-503 CONFIRMED V40**
- **Результат:** ❌ FAIL

---

## 10. БЕЗОПАСНОСТЬ — УДАЛЕНИЕ АККАУНТА

### 10.1 Валидация формы удаления (пустые поля)
- **Действие:** "Удалить аккаунт" → форма раскрылась → "Подтвердить" с пустыми полями
- **Валидация:** "Введите текущий пароль" (красный текст) ✅
- **API запрос:** Не отправлен (клиентская валидация) ✅
- **DELETE-FORM-NO-VALIDATION-MSG fix confirmed V40** ✅
- **Результат:** ✅ PASS

### 10.2 Удаление аккаунта (заполненная форма)
- **Ввод:** Пароль: TestPass1232, Подтверждение: УДАЛИТЬ
- **API:** DELETE /api/v1/auth/me → **500 Internal Server Error** ❌❌❌
- **UI:** "Внутренняя ошибка сервера"
- **Поведение:** Пользователь остался залогинен, аккаунт НЕ удалён
- **РЕГРЕССИЯ:** В V39 этот endpoint возвращал 200 OK. В V40 — 500!
- **Результат:** ❌ FAIL — **NEW BUG: ACCOUNT-DELETE-500-REGRESSION (P1)**

### 10.3 Восстановление удалённого аккаунта (ACCOUNT-DELETE-HARD-vs-SOFT retest)
- **Статус:** НЕ ТЕСТИРОВАЛОСЬ — удаление не выполнилось (500)
- **ACCOUNT-DELETE-HARD-vs-SOFT:** невозможно ретестировать, пока DELETE не работает
- **Результат:** ⏸ BLOCKED by ACCOUNT-DELETE-500-REGRESSION

---

## СВОДНАЯ ТАБЛИЦА ТЕСТОВ V40

| # | Тест | Статус | Примечание |
|---|------|--------|------------|
| 1 | Регистрация | ✅ PASS | 201 Created |
| 2 | Вход | ✅ PASS | 200 OK → /app/dashboard |
| 3 | Резюме — вставить текст (×5) | ✅ PASS | 201 Created (все 5) |
| 4 | Резюме — ссылка hh.ru | ❌ FAIL | HH-RESUME-LINK-400: POST → 400 |
| 5 | Вакансии — поиск hh.ru | ✅ PASS | 200 OK |
| 6 | Вакансии — выбор | ✅ PASS | 201 Created |
| 7 | Вакансии — невалидный URL | ✅ PASS | VACANCY-URL-OBJECT-ERROR fix confirmed |
| 8 | API ключи (×5) | ✅ PASS | PUT → 200 OK (все 5) |
| 9 | Оптимизация GigaChat Pro | ✅ PASS | Match 29→50%, ATS D |
| 10 | Оптимизация OpenAI | ✅ PASS | Match 29→46%, ATS D |
| 11 | Оптимизация Anthropic Claude | ✅ PASS | Match 29→57%, ATS C |
| 12 | Оптимизация OpenRouter | ✅ PASS | Match 29→52%, ATS C |
| 13 | Оптимизация Groq allam-2-7b | ❌ FAIL | GROQ-ALLAM-502 confirmed |
| 14 | Экспорт DOCX | ✅ PASS | GET → 200 |
| 15 | Экспорт PDF | ✅ PASS | GET → 200 |
| 16 | Экспорт TXT | ✅ PASS | GET → 200 |
| 17 | Мои резюме | ✅ PASS | 6 резюме |
| 18 | История | ✅ PASS | 5 оптимизаций |
| 19 | Дашборд | ✅ PASS | Статистика корректна |
| 20 | Аватар — загрузка | ✅ PASS | POST → 200 |
| 21 | Аватар — удаление | ❌ FAIL | AVATAR-DELETE-503 (5-я версия) |
| 22 | Смена пароля | ❌ FAIL | PASSWORD-CHANGE-503 + LOGOUT-503 |
| 23 | Удаление аккаунта — валидация | ✅ PASS | Красное сообщение ✅ |
| 24 | Удаление аккаунта — API | ❌ FAIL | ACCOUNT-DELETE-500-REGRESSION (было 200 → стало 500) |
| 25 | Удаление аккаунта — восстановление | ⏸ BLOCKED | Зависит от #24 |

**Итого: 25 тестов — 19 ✅ PASS, 5 ❌ FAIL, 1 ⏸ BLOCKED**

---

## СИСТЕМНАЯ ПРОБЛЕМА: ПАТТЕРН 503 (ПОДТВЕРЖДЁН V40)

Паттерн 503 из V39 полностью подтверждён в V40:

| Endpoint | HTTP Status | Операция на сервере |
|----------|-------------|---------------------|
| DELETE /api/v1/auth/me/avatar | 503 ❌ | Аватар удалён ✅ |
| PUT /api/v1/auth/me/password | 503 ❌ | Пароль изменён ✅ |
| POST /api/v1/auth/logout | 503 ❌ | Сессия завершена ✅ |
| DELETE /api/v1/auth/me | **500 ❌** | Аккаунт **НЕ удалён** ❌ |

**ИЗМЕНЕНИЕ V40:** DELETE /api/v1/auth/me **деградировал** с 200 (V39) до 500 (V40). В отличие от паттерна 503 (операция выполняется, статус неверный), здесь операция НЕ выполняется. Это отдельный баг — **регрессия**.

---

## ДЕФЕКТЫ V40

### ❌ NEW BUGS

#### 1. ACCOUNT-DELETE-500-REGRESSION (P1) — NEW V40
- **Endpoint:** DELETE /api/v1/auth/me → 500 Internal Server Error
- **UI:** "Внутренняя ошибка сервера"
- **Реальность:** Аккаунт НЕ удалён (пользователь остаётся залогинен, все данные на месте)
- **РЕГРЕССИЯ:** В V39 → 200 OK (работало), в V40 → 500 (сломалось)
- **Блокирует:** Ретест ACCOUNT-DELETE-HARD-vs-SOFT

### ❌ CONFIRMED BUGS (from V39)

#### 2. PASSWORD-CHANGE-503 (P1) — CONFIRMED V40
- PUT /api/v1/auth/me/password → 503, пароль реально меняется
- Паттерн 503

#### 3. AVATAR-DELETE-503 (P2) — CONFIRMED V40 (5-я версия: V36-V40)
- DELETE /api/v1/auth/me/avatar → 503, файл удаляется на сервере
- Паттерн 503

#### 4. HH-RESUME-LINK-400 (P2) — CONFIRMED V40
- POST /api/v1/resumes/from-url → 400
- Graceful degradation UI ✅

#### 5. GROQ-ALLAM-502 (P2) — CONFIRMED V40
- Groq allam-2-7b → "AI-провайдер временно недоступен"
- POST /rewrite → 202, но status возвращает ошибку

#### 6. LOGOUT-503 (P3) — CONFIRMED V40
- POST /api/v1/auth/logout → 503, сессия завершается
- Паттерн 503

### ⏸ BLOCKED / NOT FULLY TESTABLE

#### 7. ACCOUNT-DELETE-HARD-vs-SOFT (P2) — BLOCKED V40
- Не тестируемо, пока DELETE /auth/me → 500

### ✅ FIXED (подтверждено V40)

#### VACANCY-URL-OBJECT-ERROR — FIXED V40
- Невалидный URL → корректное сообщение об ошибке (не [object Object])
- POST /vacancies/from-url → 400 + понятный текст ошибки

---

## ПОДТВЕРЖДЁННЫЕ ФИКСЫ (проверены в V40)

| ID | Тест V40 | Статус |
|----|----------|--------|
| DELETE-FORM-NO-VALIDATION-MSG | Валидация пустых полей формы удаления | ✅ Работает |
| AVATAR-DELETE-BTN-UX | Кнопка "Удалить" скрыта без аватара | ✅ Работает |
| VACANCY-URL-OBJECT-ERROR | Невалидный URL → понятное сообщение | ✅ **FIXED V40** (NEW) |

---

## ОБЩИЙ ПРОГРЕСС

| Метрика | V35 | V36 | V37 | V38 | V39 | V40 |
|---------|-----|-----|-----|-----|-----|-----|
| Всего дефектов | 15 | 17 | 18 | 19 | 22 | 23 |
| Исправлено/закрыто | 7 (47%) | 10 (59%) | 14 (78%) | 14 (74%) | 14 (64%) | 15 (65%) |
| Активных | 8 | 7 | 4 | 5 | 8 | 8 |
| Новых | 0 | 2 | 1 | 1 | 3 | 1 |
| Тестов PASS | 20/25 | 23/27 | 28/30 | 29/32 | 7/12* | 19/25 |

**Тренд V40:** +1 фикс (VACANCY-URL-OBJECT-ERROR), но +1 регрессия (ACCOUNT-DELETE-500). Паттерн 503 стабильно подтверждён. GROQ-ALLAM-502 подтверждён впервые с V38. Число активных дефектов стабильно (8). Критический новый баг — регрессия удаления аккаунта (500 вместо 200).

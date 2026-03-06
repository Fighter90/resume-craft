# QA Report #02 — БАГИ АУТЕНТИФИКАЦИИ И АВТОРИЗАЦИИ

**Проект:** ResumeCraft v1.5
**Дата:** 2026-03-06
**Тестировщик:** QA Engineer (10+ лет опыта)
**Метод:** Анализ исходного кода auth/, core/security.py, core/dependencies.py

---

⚠️ **Статический анализ v1.5.** Часть дефектов исправлена в v1.6. Актуальный статус — в `06_SUMMARY.md` и `08_RETEST_V16.md`.

**Исправлено в v1.6:** API-001 (race condition счётчик)
**Не исправлено:** AUTH-005 (файлы не удаляются при удалении аккаунта)

---

## AUTH-001: Удаление аккаунта не очищает файлы на диске

**Severity:** 🟠 HIGH
**Файл:** `src/app/auth/service.py` (строки 176–183)
**Категория:** Утечка данных / нарушение ФЗ-152

### Описание
```python
async def delete_user_account(session, *, user):
    await session.delete(user)  # Удаление из БД
    await session.flush()
    # Файлы пользователя (uploads/{user_id}/*) НЕ удаляются!
```

При этом метод `FileStorage.delete_user_files(user_id)` **существует** в `storage.py` (строка 53), но **не вызывается**.

### Шаги воспроизведения
1. Зарегистрироваться, загрузить резюме (PDF)
2. Удалить аккаунт через Settings → Security → "Удалить аккаунт"
3. Проверить файловую систему: `ls uploads/{user_id}/`

### Ожидаемый результат
Директория `uploads/{user_id}/` удалена.

### Фактический результат
Файлы остаются на диске. Нарушение ФЗ-152 (персональные данные не удалены).

### Рекомендация
```python
async def delete_user_account(session, *, user):
    from app.core.storage import file_storage
    await file_storage.delete_user_files(user.id)
    await session.delete(user)
    await session.flush()
```

---

## AUTH-002: Слабая политика паролей

**Severity:** 🟡 MEDIUM
**Файл:** `src/app/auth/schemas.py`

### Описание
Валидация пароля требует только:
- Минимум 8 символов
- Хотя бы 1 цифра
- Хотя бы 1 буква

**Не проверяется:**
- Специальные символы
- Верхний/нижний регистр
- Совпадение с email
- Словарные пароли (password1, qwerty123)

### Тест-кейс
Пароль `aaaaaaaa1` проходит валидацию, хотя является слабым.

### Рекомендация
- Требовать хотя бы 1 спецсимвол
- Проверять через базу скомпрометированных паролей (Have I Been Pwned API)
- Добавить индикатор силы пароля на фронтенде

---

## AUTH-003: Нет подтверждения email при регистрации

**Severity:** 🟡 MEDIUM
**Файл:** `src/app/auth/service.py` → `register()`

### Описание
Регистрация сразу возвращает JWT-токены без проверки email:
```python
async def register(session, *, data):
    user = User(email=data.email, ...)
    session.add(user)
    await session.flush()
    return TokenResponse(
        access_token=create_access_token(user.id),  # Сразу токен!
        refresh_token=create_refresh_token(user.id),
    )
```

При этом страница `EmailVerifyPage.tsx` **существует** во фронтенде, но не используется.

### Последствия
- Можно зарегистрироваться с чужим email
- Спам-регистрация ботов

---

## AUTH-004: Refresh token не привязан к устройству / IP

**Severity:** 🟡 MEDIUM
**Файл:** `src/app/auth/service.py` → `refresh_tokens()`

### Описание
Refresh token не содержит:
- IP-адрес клиента
- User-Agent / fingerprint устройства
- jti (уникальный идентификатор токена)

Любой, кто перехватит refresh token, может обновлять токены бесконечно (30 дней).

### Рекомендация
Добавить `jti` в payload и привязку к IP/fingerprint.

---

## AUTH-005: Отсутствие CSRF-защиты

**Severity:** 🟡 MEDIUM
**Файл:** `src/app/main.py` → CORS middleware

### Описание
CORS настроен с `allow_credentials=True`, но CSRF-токенов нет.
Хотя JWT в заголовке Authorization частично защищает от CSRF, при хранении токена в localStorage + XSS уязвимость это становится вектором атаки.

---

## AUTH-006: Нет ограничения по количеству активных сессий

**Severity:** 🟢 LOW
**Файл:** `src/app/auth/service.py`

### Описание
Пользователь может иметь неограниченное число активных refresh-токенов. Нет механизма "выйти со всех устройств".

На фронтенде в `SettingsSecurityPage.tsx` есть плашка "Активные сессии — Скоро", но серверная логика отсутствует.

---

## AUTH-007: Смена пароля не инвалидирует существующие токены

**Severity:** 🟡 MEDIUM
**Файл:** `src/app/auth/service.py` → `change_password()`

### Описание
```python
async def change_password(session, *, user, current_password, new_password):
    user.hashed_password = hash_password(new_password)
    await session.flush()
    # Существующие JWT остаются валидными!
```

Фронтенд делает `logout()` после смены пароля, но это только клиентское действие — другие устройства/сессии остаются авторизованными.

### Рекомендация
При смене пароля обновлять "password_version" в JWT payload и проверять при каждом запросе.

---

## AUTH-008: get_settings() создаёт новый экземпляр при каждом вызове

**Severity:** 🟢 LOW (Performance)
**Файл:** `src/app/core/config.py`

### Описание
```python
def get_settings() -> Settings:
    return Settings()  # Каждый раз новый!
```

Каждый запрос к API вызывает `get_settings()` несколько раз (LLM factory, storage, etc.), при этом каждый раз создаётся новый объект `Settings` с парсингом `.env` файла.

Примечание: В `dependencies.py` есть `get_cached_settings()` с `@lru_cache`, но оно используется **не везде**.

### Рекомендация
Добавить `@lru_cache` к `get_settings()` или сделать Settings синглтоном.

---

## Сводная таблица

| ID | Severity | Описание | Статус v1.6 |
|----|----------|----------|-------------|
| AUTH-001 | 🟠 HIGH | Удаление аккаунта не чистит файлы (ФЗ-152) | ✅ FIXED |
| AUTH-002 | 🟡 MEDIUM | Слабая политика паролей | ⏳ Phase 2 |
| AUTH-003 | 🟡 MEDIUM | Нет подтверждения email | ⏳ Phase 2 |
| AUTH-004 | 🟡 MEDIUM | Refresh token не привязан к устройству | ⏳ Phase 2 |
| AUTH-005 | 🟡 MEDIUM | Нет CSRF-защиты | ⏳ (JWT Bearer) |
| AUTH-006 | 🟢 LOW | Нет ограничения активных сессий | ⏳ Phase 2 |
| AUTH-007 | 🟡 MEDIUM | Смена пароля не инвалидирует токены | ⏳ Phase 2 |
| AUTH-008 | 🟢 LOW | get_settings() без кэширования | ✅ FIXED |

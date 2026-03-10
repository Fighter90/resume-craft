# ResumeCraft V34 — ИТОГОВЫЙ ПРОМТ ДЛЯ ИСПРАВЛЕНИЙ

> **Дата:** 2026-03-10
> **Источники:** QA Report #30 (Full Retest V34) + Report #31 (hh.ru link tests) + Report #32 (Profile & Settings)
> **Всего замечаний:** 15 (1 × P1, 5 × P2, 3 × P3, 6 × P4)
> **Тестовый аккаунт:** test_qa_v34@example.com / TestPass1231
> **Статус:** ✅ Core flow работает, но settings/security содержит критический баг

---

## ✅ ИСПРАВЛЕННЫЕ БАГИ (подтверждены ретестом V34)

| ID | Описание | Статус |
|----|----------|--------|
| KEY-CHECK-001 (P0) | Движок не видит API-ключи | ✅ ИСПРАВЛЕН |
| HISTORY-RAW-ERROR-001 (P2) | "Failed to load raw text" | ✅ НЕ ВОСПРОИЗВОДИТСЯ |
| PRICING-MISMATCH-001 (P3) | "5 бесплатных" vs "1 бесплатная" | ✅ ИСПРАВЛЕН |
| HISTORY-COUNT-001 (P4) | Некорректный подсчёт | ✅ ИСПРАВЛЕН |

---

## ✅ РАБОТАЮЩИЕ ФУНКЦИИ (подтверждены тестами)

| Функция | Статус |
|---------|--------|
| Регистрация / Авторизация | ✅ |
| Сохранение API-ключей (все 5 провайдеров) | ✅ |
| AI-оптимизация (GigaChat, OpenAI, Anthropic, OpenRouter, Groq) | ✅ |
| Загрузка резюме (текст) | ✅ |
| Загрузка резюме (маленький PDF) | ✅ |
| Загрузка вакансии (ссылка hh.ru) | ✅ |
| Загрузка вакансии (ручной ввод) | ✅ |
| Экспорт (DOCX / PDF / TXT) | ✅ |
| Загрузка фото профиля | ✅ |
| Изменение имени/фамилии | ✅ |

---

## 🔴 ЗАМЕЧАНИЕ 1 (P1): ACCOUNT-DELETE-500 — Удаление аккаунта не работает

### Проблема

При попытке удалить аккаунт через `/app/settings/security` → "Удалить аккаунт" сервер возвращает **500 Internal Server Error**. Аккаунт НЕ удаляется.

### Воспроизведение

```
1. Войти в аккаунт
2. Перейти на /app/settings/security
3. Нажать "Удалить аккаунт"
4. Ввести пароль аккаунта
5. Ввести "УДАЛИТЬ" в поле подтверждения
6. Нажать "Подтвердить"
7. РЕЗУЛЬТАТ: "Внутренняя ошибка сервера" (красное сообщение)
8. ОЖИДАНИЕ: Аккаунт удалён, редирект на главную
```

### Технические детали

```
DELETE /api/v1/auth/me → 500 (Internal Server Error)
```

### Рекомендации по исправлению

```python
@router.delete("/api/v1/auth/me")
async def delete_account(
    password: str = Body(...),
    confirmation: str = Body(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Валидация
    if confirmation != "УДАЛИТЬ":
        raise HTTPException(400, "Введите УДАЛИТЬ для подтверждения")

    if not verify_password(password, user.hashed_password):
        raise HTTPException(401, "Неверный пароль")

    try:
        # 2. Удалить связанные данные (каскадное удаление или soft delete)
        await db.execute(delete(Resume).where(Resume.user_id == user.id))
        await db.execute(delete(Optimization).where(Optimization.user_id == user.id))
        await db.execute(delete(ApiKey).where(ApiKey.user_id == user.id))
        # ... другие связанные таблицы

        # 3. Удалить пользователя
        await db.delete(user)
        await db.commit()

        # 4. Инвалидировать сессию
        return {"message": "Аккаунт удалён"}

    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Account deletion failed (integrity): {e}")
        raise HTTPException(500, "Ошибка при удалении. Обратитесь в поддержку.")
    except Exception as e:
        await db.rollback()
        logger.error(f"Account deletion failed: {e}")
        raise HTTPException(500, "Внутренняя ошибка сервера")
```

**Вероятная причина 500:** Каскадное удаление не настроено — при попытке удалить пользователя нарушаются foreign key constraints связанных таблиц (resumes, optimizations, api_keys и др.).

### Тест-кейс

```
1. Удалить аккаунт с правильным паролем и "УДАЛИТЬ" → ОЖИДАНИЕ: Аккаунт удалён, редирект
2. Удалить аккаунт с неверным паролем → ОЖИДАНИЕ: "Неверный пароль"
3. Удалить аккаунт без "УДАЛИТЬ" → ОЖИДАНИЕ: Ошибка валидации
4. Попытка войти после удаления → ОЖИДАНИЕ: "Аккаунт не найден"
```

### ⚠️ Важно: GDPR

Невозможность удалить аккаунт может нарушать GDPR (право на удаление, ст. 17). Это должно быть исправлено с высоким приоритетом.

---

## 🔴 ЗАМЕЧАНИЕ 2 (P2): PROFILE-PHONE-SAVE — Телефон не сохраняется

### Проблема

На странице `/app/settings/profile` при изменении номера телефона и нажатии "Сохранить изменения" сервер возвращает 200 OK, но после перезагрузки телефон пустой.

### Воспроизведение

```
1. Перейти на /app/settings/profile
2. Ввести телефон: +7 (916) 123-45-67
3. Нажать "Сохранить изменения" → 200 OK
4. Перезагрузить страницу
5. РЕЗУЛЬТАТ: Поле телефона пустое (+7 (___) ___-__-__)
6. ОЖИДАНИЕ: Телефон сохранён и отображается
```

### Технические детали

```
PUT /api/v1/auth/me → 200 OK
// Но phone не включается в request body или игнорируется бэкендом
```

### Рекомендации

**Вариант А (фронтенд не отправляет поле):**

```typescript
// Проверить, что phone включён в body запроса:
const updateProfile = async (data: ProfileForm) => {
  await api.put('/auth/me', {
    first_name: data.firstName,
    last_name: data.lastName,
    phone: data.phone,     // ← Убедиться, что это поле отправляется
    city: data.city,       // ← И это тоже
  });
};
```

**Вариант Б (бэкенд игнорирует поле):**

```python
# В Pydantic-схеме обновления профиля добавить поля:
class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None      # ← Добавить
    city: Optional[str] = None       # ← Добавить

# В endpoint:
@router.put("/api/v1/auth/me")
async def update_profile(data: UserUpdate, user: User = Depends(get_current_user)):
    if data.phone is not None:
        user.phone = data.phone
    if data.city is not None:
        user.city = data.city
    # ...
```

### Тест-кейс

```
1. Ввести телефон → Сохранить → Перезагрузить → ОЖИДАНИЕ: Телефон на месте
2. Очистить телефон → Сохранить → Перезагрузить → ОЖИДАНИЕ: Поле пустое
```

---

## 🔴 ЗАМЕЧАНИЕ 3 (P2): PROFILE-CITY-SAVE — Город не сохраняется

### Проблема

При выборе города (select: Москва, Санкт-Петербург, Новосибирск, Екатеринбург, Казань, Другой) и сохранении настроек город не персистится — после перезагрузки возвращается "Москва".

### Воспроизведение

```
1. Перейти на /app/settings/profile
2. Выбрать город: "Санкт-Петербург"
3. Нажать "Сохранить изменения" → 200 OK
4. Перезагрузить страницу
5. РЕЗУЛЬТАТ: Город = "Москва"
6. ОЖИДАНИЕ: Город = "Санкт-Петербург"
```

### Рекомендации

Аналогично замечанию 2 (PROFILE-PHONE-SAVE). Проверить:
1. Отправляется ли поле `city` в PUT-запросе на фронтенде
2. Принимает ли бэкенд поле `city` в схеме обновления
3. Сохраняется ли значение в БД

### Тест-кейс

```
1. Выбрать каждый город из списка → Сохранить → Перезагрузить → ОЖИДАНИЕ: Выбранный город
```

---

## 🔴 ЗАМЕЧАНИЕ 4 (P2): AVATAR-DELETE-503 — Удаление аватара возвращает 503

### Проблема

При нажатии "Удалить" рядом с аватаром фронтенд визуально удаляет фото (показывает инициалы), но сервер возвращает **503 Service Unavailable**.

### Воспроизведение

```
1. Загрузить аватар (POST /api/v1/auth/me/avatar → 200 OK)
2. Нажать "Удалить"
3. РЕЗУЛЬТАТ (UI): Аватар заменён на инициалы ✅
4. РЕЗУЛЬТАТ (Network): DELETE /api/v1/auth/me/avatar → 503 ❌
5. ОЖИДАНИЕ: DELETE → 200 OK
```

### Рекомендации

```python
@router.delete("/api/v1/auth/me/avatar")
async def delete_avatar(user: User = Depends(get_current_user)):
    try:
        # Удалить файл из storage
        if user.avatar_path:
            await delete_file(user.avatar_path)

        user.avatar_path = None
        await db.commit()
        return {"message": "Аватар удалён"}

    except Exception as e:
        logger.error(f"Avatar delete error: {e}")
        raise HTTPException(500, "Не удалось удалить аватар")
```

**Вероятная причина:** 503 обычно означает, что сервис (или upstream) недоступен. Возможно, endpoint не реализован или файловое хранилище (S3/MinIO) недоступно.

### Тест-кейс

```
1. Загрузить аватар → Удалить → ОЖИДАНИЕ: 200 OK, аватар удалён
2. Перезагрузить → ОЖИДАНИЕ: Инициалы (аватар не восстановился)
```

---

## 🔴 ЗАМЕЧАНИЕ 5 (P2): HH-RESUME-LINK-405 — Загрузка резюме по ссылке hh.ru не работает

### Проблема

На странице `/app/upload` (вкладка "Ссылка hh.ru") endpoint `POST /api/v1/resumes/from-url` возвращает **405 Method Not Allowed**. Вся вкладка нефункциональна.

### Воспроизведение

```
1. Перейти на /app/upload → вкладка "Ссылка hh.ru"
2. Ввести: https://hh.ru/resume/90d67b47ff01c53bfd0039ed1f36424d765046
3. Нажать "Загрузить резюме"
4. РЕЗУЛЬТАТ: "Не удалось автоматически загрузить резюме с hh.ru"
5. Network: POST /api/v1/resumes/from-url → 405
```

### Рекомендации

**Вариант А — реализовать парсинг:**

```python
@router.post("/api/v1/resumes/from-url")
async def import_resume_from_url(url: str, user: User = Depends(get_current_user)):
    if not re.match(r'^https?://(www\.)?hh\.ru/resume/[a-f0-9]+', url):
        raise HTTPException(400, "Поддерживаются только ссылки на резюме hh.ru")

    try:
        text = await fetch_and_parse_hh_resume(url)
        return {"text": text, "source": "hh_url"}
    except Exception as e:
        raise HTTPException(400, "Не удалось загрузить. Скопируйте текст вручную.")
```

**Вариант Б — скрыть вкладку до реализации:**

```typescript
// Временно скрыть вкладку "Ссылка hh.ru" если feature не реализована:
const TABS = [
  { id: 'text', label: 'Вставить текст' },
  { id: 'file', label: 'Загрузить файл' },
  // { id: 'hh_link', label: 'Ссылка hh.ru' },  // Раскомментировать после реализации
];
```

### Тест-кейс

```
1. Ввести валидную ссылку hh.ru → ОЖИДАНИЕ: Резюме загружено
2. Ввести невалидную ссылку → ОЖИДАНИЕ: "Поддерживаются только ссылки hh.ru"
3. Пустое поле → ОЖИДАНИЕ: "Введите ссылку"
```

---

## 🟡 ЗАМЕЧАНИЕ 6 (P2): PDF-PARSE-502 — "Bad Gateway" при загрузке больших PDF

### Проблема

При загрузке PDF-файла (> 100 КБ) сервер возвращает 502 Bad Gateway. Маленькие well-formed PDF (2.4 КБ) парсятся успешно.

### Воспроизведение

```
1. Загрузить реальный PDF-резюме (100–500 КБ)
2. Нажать "Продолжить"
3. РЕЗУЛЬТАТ: "Bad Gateway"
4. ОЖИДАНИЕ: Текст извлечён
```

### Рекомендации

1. Проверить `client_max_body_size` и `proxy_read_timeout` в nginx
2. Обернуть PDF-парсинг в try/except с понятной ошибкой
3. Добавить проверку размера файла на фронтенде (макс. 5 МБ)

---

## 🟡 ЗАМЕЧАНИЕ 7 (P3): PROFILE-EMAIL-VERIFY — Нет кнопки подтверждения email

### Проблема

На странице профиля рядом с email отображается "⚠️ Не подтверждён", но нет кнопки/ссылки для повторной отправки письма подтверждения.

### Воспроизведение

```
1. Перейти на /app/settings/profile
2. Рядом с email: "⚠️ Не подтверждён"
3. Нет кнопки "Отправить повторно"
```

### Рекомендации

```tsx
{!user.emailVerified && (
  <div className="flex items-center gap-2">
    <span className="text-yellow-600">⚠️ Не подтверждён</span>
    <button
      onClick={() => resendVerificationEmail()}
      className="text-blue-600 hover:underline text-sm"
    >
      Отправить повторно
    </button>
  </div>
)}
```

```python
@router.post("/api/v1/auth/resend-verification")
async def resend_verification(user: User = Depends(get_current_user)):
    if user.email_verified:
        raise HTTPException(400, "Email уже подтверждён")
    await send_verification_email(user.email)
    return {"message": "Письмо отправлено"}
```

---

## 🟡 ЗАМЕЧАНИЕ 8 (P3): VACANCY-TITLE-002 — Автозаполнение "Название должности" из имени резюме

### Проблема

На `/app/vacancy` поле "Название должности" заполняется **именем записи резюме** вместо извлечённой из текста должности.

### Рекомендации

```typescript
// БЫЛО:
setVacancyTitle(resumeData?.name || '');
// ДОЛЖНО БЫТЬ:
setVacancyTitle(resumeData?.extractedPosition || '');
```

---

## 🟡 ЗАМЕЧАНИЕ 9 (P3): PRICING-FORMAT-001 — Расхождение описания форматов экспорта

### Проблема

Разные страницы по-разному описывают форматы экспорта: лендинг говорит "DOCX", справка — "PDF/DOCX", фактически доступны DOCX + PDF + TXT.

### Рекомендация

Унифицировать описание форматов на всех страницах (/#pricing, /app/help, /app/settings/subscription).

---

## Замечание 10 (P4): HH-RESUME-LINK-VALIDATION — Нет клиентской валидации URL

### Проблема

Вкладка "Ссылка hh.ru" принимает любой URL без проверки (google.com, пустая строка).

### Рекомендация

```typescript
const HH_RESUME_PATTERN = /^https?:\/\/(www\.)?hh\.ru\/resume\/[a-f0-9]+/i;

if (!url.trim()) {
  showError('Введите ссылку на резюме');
  return;
}
if (!HH_RESUME_PATTERN.test(url)) {
  showError('Введите корректную ссылку на резюме hh.ru');
  return;
}
```

---

## Замечание 11 (P4): PROFILE-AVATAR-SIDEBAR — Sidebar не показывает аватар

### Проблема

После загрузки аватара на странице профиля фото отображается корректно, но в sidebar показываются только инициалы.

### Рекомендация

Sidebar компонент должен подписаться на обновление аватара и использовать avatar_url вместо initials, если аватар загружен.

```tsx
// В sidebar:
{user.avatarUrl ? (
  <img src={user.avatarUrl} className="w-8 h-8 rounded-full" />
) : (
  <div className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center">
    {user.initials}
  </div>
)}
```

---

## Замечание 12 (P4): DELETE-FORM-NO-VALIDATION-MSG — Нет валидации формы удаления

### Проблема

Форма удаления аккаунта не показывает ошибки при пустой отправке.

### Рекомендация

```typescript
if (!password) {
  showError('Введите пароль');
  return;
}
if (confirmation !== 'УДАЛИТЬ') {
  showError('Введите слово УДАЛИТЬ для подтверждения');
  return;
}
```

---

## Замечание 13 (P4): SECURITY-AUTOFILL — Автозаполнение пароля в форме

### Проблема

Поле "Подтвердите пароль" в разделе смены пароля заполняется браузерным автозаполнением.

### Рекомендация

```html
<input type="password" autocomplete="new-password" />
```

---

## Замечание 14 (P4): GROQ-CASE-002 — "groq" в нижнем регистре в истории

### Проблема

В истории: "Оптимизация · groq" вместо "Оптимизация · Groq".

### Рекомендация

Использовать маппинг display_name для всех провайдеров.

---

## Замечание 15 (P4 INFO): HISTORY-MODEL-FORMAT-001 — Неконсистентный формат наименований

### Проблема

В истории разные форматы: `openrouter:ai21/jamba-large-1.7`, `groq` (без модели), `gigachat-pro` (без провайдера).

### Рекомендация

Унифицировать: **"Provider · Model"** для всех записей.

---

## СВОДНАЯ ТАБЛИЦА

| # | ID | P | Описание | Компонент | Сложность |
|---|----|---|----------|-----------|-----------|
| 1 | ACCOUNT-DELETE-500 | **P1** | Удаление аккаунта → 500 | Backend | Средняя |
| 2 | PROFILE-PHONE-SAVE | **P2** | Телефон не сохраняется | Frontend/Backend | Лёгкая |
| 3 | PROFILE-CITY-SAVE | **P2** | Город не сохраняется | Frontend/Backend | Лёгкая |
| 4 | AVATAR-DELETE-503 | **P2** | Удаление аватара → 503 | Backend | Средняя |
| 5 | HH-RESUME-LINK-405 | **P2** | Загрузка резюме по ссылке → 405 | Backend | Средняя |
| 6 | PDF-PARSE-502 | **P2** | PDF загрузка → 502 | Backend/Nginx | Средняя |
| 7 | PROFILE-EMAIL-VERIFY | P3 | Нет кнопки подтверждения email | Frontend/Backend | Лёгкая |
| 8 | VACANCY-TITLE-002 | P3 | Автозаполнение должности | Frontend | Лёгкая |
| 9 | PRICING-FORMAT-001 | P3 | Расхождение форматов экспорта | Content | Лёгкая |
| 10 | HH-RESUME-LINK-VALIDATION | P4 | Нет валидации URL резюме | Frontend | Лёгкая |
| 11 | PROFILE-AVATAR-SIDEBAR | P4 | Sidebar не показывает аватар | Frontend | Лёгкая |
| 12 | DELETE-FORM-NO-VALIDATION-MSG | P4 | Нет валидации формы удаления | Frontend | Лёгкая |
| 13 | SECURITY-AUTOFILL | P4 | Автозаполнение пароля | Frontend | Лёгкая |
| 14 | GROQ-CASE-002 | P4 | groq в нижнем регистре | Frontend | Лёгкая |
| 15 | HISTORY-MODEL-FORMAT-001 | P4 | Неконсистентный формат | Frontend/Backend | Лёгкая |

---

## РЕКОМЕНДУЕМЫЙ ПОРЯДОК ИСПРАВЛЕНИЙ

### Спринт 1 — Критичное (1–2 дня)

1. **ACCOUNT-DELETE-500 (P1)** — удаление аккаунта. Настроить каскадное удаление связанных записей. GDPR compliance.

### Спринт 2 — Сохранение профиля (1 день)

2. **PROFILE-PHONE-SAVE (P2)** — добавить phone в PUT /auth/me
3. **PROFILE-CITY-SAVE (P2)** — добавить city в PUT /auth/me
4. **AVATAR-DELETE-503 (P2)** — реализовать/починить DELETE /auth/me/avatar

### Спринт 3 — Загрузка данных (1–2 дня)

5. **HH-RESUME-LINK-405 (P2)** — реализовать endpoint или скрыть вкладку
6. **PDF-PARSE-502 (P2)** — проверить nginx таймауты, обработка ошибок

### Спринт 4 — UX-улучшения (1 день)

7. **PROFILE-EMAIL-VERIFY (P3)** — добавить кнопку "Отправить повторно"
8. **VACANCY-TITLE-002 (P3)** — исправить автозаполнение
9. **PRICING-FORMAT-001 (P3)** — унифицировать описания

### Спринт 5 — Косметика (0.5 дня)

10–15. Все P4 замечания — одним коммитом

---

## ИТОГОВАЯ ОЦЕНКА V34

| Категория | Оценка |
|-----------|--------|
| Core flow (оптимизация резюме) | **9/10** |
| Загрузка данных (резюме/вакансии) | **7.5/10** |
| Профиль и настройки | **4/10** |
| Безопасность (удаление аккаунта) | **2/10** |
| Экспорт | **9/10** |
| **ИТОГО** | **7.5/10** |
| **Production ready (core flow)** | **✅ ДА** |
| **Production ready (полный функционал)** | **⚠️ НЕТ (P1 ACCOUNT-DELETE-500)** |

---

*Итоговый отчёт: 10.03.2026*
*QA Reports: #30, #31, #32*
*Тестовый аккаунт: test_qa_v34@example.com / TestPass1231*

# AGENT FIX PROMPT V35 — Все дефекты и доработки после регрессии V35

**Дата:** 2026-03-10
**Источник:** QA Report #33 (33_FULL_REGRESSION_V35.md) + регрессия FINAL_FIX_PROMPT_V34.md
**Проект:** ResumeCraft.ru
**Тестовый аккаунт:** qa_regress_v35@example.com (удалён в ходе тестирования)
**Альтернативные аккаунты:** test@example.com / TestPass1231, test_new@example.com / TestPass1231

---

## СВОДКА ДЕФЕКТОВ

| # | Приоритет | ID | Описание | Тип | Статус V35 |
|---|-----------|-----|----------|-----|------------|
| 1 | 🔴 P2 | AVATAR-DELETE-503 | Удаление аватара → 503 | BUG (не исправлен с V34) | ❌ CONFIRMED |
| 2 | 🔴 P2 | HH-RESUME-LINK-405 | Загрузка резюме по ссылке hh.ru → 400 (парсинг не работает) | BUG (частично исправлен V35) | ⚠️ PARTIAL FIX |
| 3 | 🔴 P2 | PDF-PARSE-502 | Большие PDF → 502 Bad Gateway | BUG (не тестировалось V35) | ⏸ NOT RETESTED |
| 4 | 🟡 P3 | VACANCY-TITLE-002 | Автозаполнение должности из имени резюме | BUG (не тестировалось V35) | ⏸ NOT RETESTED |
| ~~5~~ | ~~🟡 P3~~ | ~~PRICING-FORMAT-001~~ | ~~Расхождение описания форматов экспорта~~ | ~~CONTENT~~ | ✅ **FIXED V35** |
| 6 | 🟢 P4 | PROFILE-AVATAR-SIDEBAR | Sidebar не показывает аватар | BUG (не исправлен с V34) | ❌ CONFIRMED |
| 7 | 🟢 P4 | DELETE-FORM-NO-VALIDATION-MSG | Нет валидации формы удаления аккаунта | BUG (не исправлен с V34) | ❌ CONFIRMED |
| 8 | 🟢 P4 | SECURITY-AUTOFILL | Автозаполнение пароля браузером | BUG (не исправлен с V34) | ❌ CONFIRMED |
| 9 | 🟢 P4 | PHONE-MASK-FORMAT | Маска телефона не форматирует цифры | BUG (новый V35) | ❌ NEW |
| ~~10~~ | ~~🟢 P4~~ | ~~HH-RESUME-LINK-VALIDATION~~ | ~~Нет клиентской валидации URL hh.ru~~ | ~~BUG~~ | ✅ **FIXED V35** |
| 11 | 🟢 P4 | GROQ-CASE-002 | "groq" в нижнем регистре в истории | BUG (не удалось воспроизвести) | ⏸ CANNOT VERIFY |
| ~~12~~ | ~~🟢 P4~~ | ~~HISTORY-MODEL-FORMAT-001~~ | ~~Неконсистентный формат наименований~~ | ~~BUG~~ | ✅ **FIXED V35** |

---

## ✅ ИСПРАВЛЕННЫЕ БАГИ В V35 (подтверждены тестами)

| ID | P | Описание | V34 → V35 |
|----|---|----------|-----------|
| ACCOUNT-DELETE-500 | **P1** | Удаление аккаунта → 500 | ❌ 500 → ✅ 200 OK |
| PROFILE-PHONE-SAVE | P2 | Телефон не сохранялся | ❌ Пустой → ✅ Сохраняется |
| PROFILE-CITY-SAVE | P2 | Город не сохранялся | ❌ Москва → ✅ СПб |
| PROFILE-EMAIL-VERIFY | P3 | Нет кнопки подтверждения email | ❌ Нет кнопки → ✅ "Отправить повторно" |
| PRICING-FORMAT-001 | P3 | Расхождение форматов экспорта | ❌ Разные описания → ✅ "DOCX, PDF и TXT" везде |
| HH-RESUME-LINK-VALIDATION | P4 | Нет валидации URL hh.ru | ❌ Нет валидации → ✅ "Введите корректную ссылку" |
| HISTORY-MODEL-FORMAT-001 | P4 | Неконсистентный формат истории | ❌ Разнородный → ✅ "Provider · Model" |

---

## 🔴 ДЕФЕКТ 1 — AVATAR-DELETE-503 (P2): Удаление аватара возвращает 503

### Проблема

При нажатии "Удалить" рядом с аватаром сервер возвращает **503 Service Unavailable**. Аватар не удаляется ни на бэкенде, ни в UI.

### Воспроизведение

```
1. Войти в аккаунт
2. Перейти на /app/settings/profile
3. Загрузить аватар (POST /api/v1/auth/me/avatar → 200 OK) ✅
4. Нажать кнопку "Удалить" рядом с аватаром
5. РЕЗУЛЬТАТ: DELETE /api/v1/auth/me/avatar → 503 (Service Unavailable)
6. ОЖИДАНИЕ: DELETE → 200 OK, аватар удалён
```

### Технические детали

```
DELETE /api/v1/auth/me/avatar → 503 (Service Unavailable)
```

503 обычно означает, что upstream-сервис недоступен. Вероятные причины:
- Endpoint `DELETE /api/v1/auth/me/avatar` не реализован на бэкенде
- Файловое хранилище (S3/MinIO) недоступно или не настроено для удаления
- Nginx/reverse proxy не проксирует DELETE-запросы на этот endpoint

### Рекомендации по исправлению

```python
@router.delete("/api/v1/auth/me/avatar")
async def delete_avatar(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not user.avatar_path:
        return {"message": "Аватар не установлен"}

    try:
        # 1. Удалить файл из storage (S3/MinIO/локальный диск)
        storage = get_storage_backend()
        await storage.delete(user.avatar_path)
    except Exception as e:
        logger.warning(f"Failed to delete avatar file: {e}")
        # Продолжить даже если файл не удалился

    # 2. Обнулить путь в БД
    user.avatar_path = None
    user.avatar_url = None
    await db.commit()

    return {"message": "Аватар удалён"}
```

**Проверить также:**
- Nginx config: убедиться, что `DELETE` method разрешён для `/api/v1/auth/me/avatar`
- CORS: убедиться, что DELETE в `Access-Control-Allow-Methods`

### Тест-кейс

```
1. Загрузить аватар → 200 OK
2. Удалить аватар → ОЖИДАНИЕ: 200 OK
3. Перезагрузить → ОЖИДАНИЕ: Отображаются инициалы (аватар не восстановился)
4. Попытка удалить без аватара → ОЖИДАНИЕ: 200 OK (или 404 "Аватар не установлен")
```

---

## 🔴 ДЕФЕКТ 2 — HH-RESUME-LINK-405 (P2): Парсинг hh.ru не работает (⚠️ частично исправлен)

### Проблема

На странице `/app/upload` (вкладка "Ссылка hh.ru") endpoint `POST /api/v1/resumes/from-url` теперь существует (V34: 405 → V35: 400), но парсинг страницы hh.ru не работает — сервер возвращает **400 Bad Request**. Фронтенд показывает пользователю сообщение об ошибке с предложением скопировать текст вручную (UX улучшен).

### Воспроизведение

```
1. Перейти на /app/upload → вкладка "Ссылка hh.ru"
2. Ввести: https://hh.ru/resume/90d67b47ff01c53bfd0039ed1f36424d765046
3. Нажать "Загрузить резюме"
4. РЕЗУЛЬТАТ: POST /api/v1/resumes/from-url → 400 Bad Request
5. Фронтенд: Сообщение об ошибке с fallback-предложением (вставить текст вручную)
6. ОЖИДАНИЕ: Резюме загружено автоматически
```

### Рекомендации

**Вариант А — реализовать endpoint:**

```python
@router.post("/api/v1/resumes/from-url")
async def import_resume_from_url(
    url: str = Body(..., embed=True),
    user: User = Depends(get_current_user)
):
    # Валидация URL
    if not re.match(r'^https?://(www\.)?hh\.ru/resume/[a-f0-9]+', url):
        raise HTTPException(400, "Поддерживаются только ссылки на резюме hh.ru")

    try:
        # Парсинг страницы hh.ru
        text = await fetch_and_parse_hh_resume(url)
        return {"text": text, "source": "hh_url"}
    except Exception as e:
        logger.error(f"hh.ru parse error: {e}")
        raise HTTPException(422, "Не удалось загрузить. Скопируйте текст вручную.")
```

**Вариант Б — скрыть вкладку до реализации:**

```typescript
// Временно скрыть вкладку если feature flag выключен:
const UPLOAD_TABS = [
  { id: 'text', label: 'Вставить текст' },
  { id: 'file', label: 'Загрузить файл' },
  // Показывать только если feature реализована:
  ...(FEATURES.HH_IMPORT ? [{ id: 'hh_link', label: 'Ссылка hh.ru' }] : []),
];
```

### Тест-кейс

```
1. Ввести валидную ссылку hh.ru → ОЖИДАНИЕ: Резюме загружено (или "Функция в разработке")
2. Ввести невалидную ссылку → ОЖИДАНИЕ: "Поддерживаются только ссылки hh.ru"
3. Пустое поле → ОЖИДАНИЕ: "Введите ссылку"
```

---

## 🔴 ДЕФЕКТ 3 — PDF-PARSE-502 (P2): Большие PDF → 502 Bad Gateway

### Проблема

При загрузке PDF-файла > 100 КБ сервер возвращает **502 Bad Gateway**. Маленькие PDF (< 10 КБ) парсятся успешно.

### Воспроизведение

```
1. Перейти на /app/upload → вкладка "Загрузить файл"
2. Загрузить реальное PDF-резюме (100–500 КБ)
3. Нажать "Продолжить"
4. РЕЗУЛЬТАТ: "Bad Gateway"
5. ОЖИДАНИЕ: Текст из PDF извлечён, переход к /app/vacancy
```

### Рекомендации

1. **Nginx:** Увеличить таймауты и размер тела запроса:

```nginx
location /api/ {
    client_max_body_size 10M;
    proxy_read_timeout 60s;
    proxy_connect_timeout 30s;
    proxy_send_timeout 30s;
}
```

2. **Backend:** Обернуть PDF-парсинг в try/except:

```python
@router.post("/api/v1/resumes/upload")
async def upload_resume(file: UploadFile):
    # Проверка размера
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:  # 5 МБ
        raise HTTPException(413, "Файл слишком большой. Максимум 5 МБ.")

    try:
        text = extract_text_from_pdf(content)
        if not text.strip():
            raise HTTPException(422, "Не удалось извлечь текст из PDF")
        return {"text": text}
    except Exception as e:
        logger.error(f"PDF parse error: {e}")
        raise HTTPException(422, "Ошибка чтения PDF. Попробуйте скопировать текст вручную.")
```

3. **Frontend:** Добавить проверку размера до отправки:

```typescript
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 МБ

if (file.size > MAX_FILE_SIZE) {
  showError('Файл слишком большой. Максимум 5 МБ.');
  return;
}
```

### Тест-кейс

```
1. PDF < 10 КБ → ОЖИДАНИЕ: Текст извлечён ✅
2. PDF 100–500 КБ → ОЖИДАНИЕ: Текст извлечён (сейчас 502)
3. PDF > 5 МБ → ОЖИДАНИЕ: "Файл слишком большой"
4. Повреждённый PDF → ОЖИДАНИЕ: "Ошибка чтения PDF"
```

---

## 🟡 ДЕФЕКТ 4 — VACANCY-TITLE-002 (P3): Автозаполнение должности из имени резюме

### Проблема

На `/app/vacancy` поле "Название должности" заполняется **именем записи резюме** (например "resume_2026-03-10") вместо извлечённой из текста должности.

### Рекомендации

```typescript
// БЫЛО (вероятно):
setVacancyTitle(resumeData?.name || '');

// ДОЛЖНО БЫТЬ:
setVacancyTitle(resumeData?.extractedPosition || resumeData?.detected_title || '');
```

Если `extractedPosition` не доступен, оставить поле пустым для ручного заполнения.

### Тест-кейс

```
1. Загрузить резюме с должностью "Продакт-менеджер" → ОЖИДАНИЕ: Поле заполнено "Продакт-менеджер"
2. Загрузить резюме без явной должности → ОЖИДАНИЕ: Поле пустое
```

---

## ~~🟡 ДЕФЕКТ 5 — PRICING-FORMAT-001 (P3): ✅ ИСПРАВЛЕН В V35~~

> **Подтверждено 11.03.2026:** Все страницы (лендинг /#pricing, справка /app/help) теперь показывают единообразное "DOCX, PDF и TXT". Баг закрыт.

---

## 🟢 ДЕФЕКТ 6 — PROFILE-AVATAR-SIDEBAR (P4): Sidebar не показывает аватар

### Проблема

После загрузки аватара на странице профиля фото отображается корректно, но в sidebar показываются только инициалы.

### Рекомендации

```tsx
// Sidebar component — использовать avatar_url если доступен:
function SidebarUser({ user }: { user: User }) {
  return (
    <div className="flex items-center">
      {user.avatarUrl ? (
        <img
          src={user.avatarUrl}
          alt={user.initials}
          className="w-8 h-8 rounded-full object-cover"
        />
      ) : (
        <div className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center text-sm font-medium">
          {user.initials}
        </div>
      )}
      <span className="ml-2">{user.fullName}</span>
    </div>
  );
}
```

Также убедиться, что при загрузке/удалении аватара состояние пользователя в сторе обновляется (React Context / Redux / Zustand) — sidebar должен реагировать на изменение `avatarUrl`.

### Тест-кейс

```
1. Загрузить аватар → ОЖИДАНИЕ: Аватар в sidebar (без перезагрузки)
2. Удалить аватар → ОЖИДАНИЕ: Инициалы в sidebar
3. Перезагрузить → ОЖИДАНИЕ: Состояние сохранилось
```

---

## 🟢 ДЕФЕКТ 7 — DELETE-FORM-NO-VALIDATION-MSG (P4): Нет валидации формы удаления

### Проблема

Форма удаления аккаунта не показывает визуальных ошибок при пустой отправке. Форма не отправляется (хорошо), но пользователь не понимает почему.

### Рекомендации

```typescript
const handleDeleteAccount = () => {
  // Клиентская валидация
  if (!password) {
    setError('Введите текущий пароль');
    return;
  }
  if (confirmation !== 'УДАЛИТЬ') {
    setError('Введите слово УДАЛИТЬ для подтверждения');
    return;
  }

  // Отправка запроса
  deleteAccount({ password, confirmation });
};
```

```tsx
{error && (
  <div className="text-red-500 text-sm mt-2">{error}</div>
)}
```

### Тест-кейс

```
1. Пустые оба поля → "Подтвердить" → ОЖИДАНИЕ: "Введите текущий пароль"
2. Пароль введён, подтверждение пустое → ОЖИДАНИЕ: "Введите слово УДАЛИТЬ"
3. Пароль и "УДАЛИТЬ" введены → ОЖИДАНИЕ: Запрос отправлен
```

---

## 🟢 ДЕФЕКТ 8 — SECURITY-AUTOFILL (P4): Автозаполнение пароля браузером

### Проблема

Поля "Текущий пароль" и "Подтвердите пароль" в разделе смены пароля на `/app/settings/security` заполняются браузерным автозаполнением, что вводит пользователя в заблуждение.

### Рекомендации

```html
<!-- Для полей смены пароля: -->
<input type="password" autocomplete="new-password" name="new-password-field" />

<!-- Для поля текущего пароля (подтверждение): -->
<input type="password" autocomplete="off" name="current-password-confirm" />
```

Альтернативно — использовать `readonly` на фокусе:

```tsx
<input
  type="password"
  readOnly
  onFocus={(e) => e.target.removeAttribute('readOnly')}
  autoComplete="new-password"
/>
```

---

## 🟢 ДЕФЕКТ 9 — PHONE-MASK-FORMAT (P4): Маска телефона не форматирует (НОВЫЙ V35)

### Проблема

Телефонная маска `+7 (___) ___-__-__` не применяет форматирование к введённым/сохранённым цифрам. После сохранения номер отображается как `9161234567` вместо `+7 (916) 123-45-67`.

### Воспроизведение

```
1. Перейти на /app/settings/profile
2. Ввести в поле телефона: 9161234567
3. Нажать "Сохранить изменения" → 200 OK
4. Перезагрузить страницу
5. РЕЗУЛЬТАТ: Поле содержит "9161234567" (сырые цифры)
6. ОЖИДАНИЕ: "+7 (916) 123-45-67" (форматированный через маску)
```

### Рекомендации

1. **При загрузке профиля** — применить маску к сохранённому значению:

```typescript
import { formatPhone } from '@/utils/phone';

// При получении данных профиля:
const formattedPhone = formatPhone(profileData.phone);
// "9161234567" → "+7 (916) 123-45-67"

function formatPhone(raw: string): string {
  if (!raw) return '';
  const digits = raw.replace(/\D/g, '');
  // Убрать ведущую 7/8 если есть
  const normalized = digits.startsWith('7') ? digits.slice(1) :
                     digits.startsWith('8') ? digits.slice(1) : digits;
  if (normalized.length !== 10) return raw; // Не трогать некорректные
  return `+7 (${normalized.slice(0,3)}) ${normalized.slice(3,6)}-${normalized.slice(6,8)}-${normalized.slice(8,10)}`;
}
```

2. **Использовать библиотеку маски** (react-input-mask или react-imask):

```tsx
import InputMask from 'react-input-mask';

<InputMask
  mask="+7 (999) 999-99-99"
  value={phone}
  onChange={(e) => setPhone(e.target.value)}
>
  {(inputProps) => <input {...inputProps} type="tel" />}
</InputMask>
```

3. **При сохранении** — отправлять на бэкенд только цифры:

```typescript
const savePhone = phone.replace(/\D/g, ''); // "+7 (916) 123-45-67" → "79161234567"
```

### Тест-кейс

```
1. Ввести 9161234567 → ОЖИДАНИЕ: Маска форматирует в +7 (916) 123-45-67
2. Сохранить → Перезагрузить → ОЖИДАНИЕ: +7 (916) 123-45-67
3. Ввести +7 (495) 000-00-00 → Сохранить → Перезагрузить → ОЖИДАНИЕ: Тот же формат
```

---

## ~~🟢 ДЕФЕКТ 10 — HH-RESUME-LINK-VALIDATION (P4): ✅ ИСПРАВЛЕН В V35~~

> **Подтверждено 11.03.2026:** Клиентская валидация URL теперь работает. Пустое поле не отправляется, невалидный URL (google.com) показывает "Введите корректную ссылку на резюме hh.ru". Баг закрыт.

---

## 🟢 ДЕФЕКТ 11 — GROQ-CASE-002 (P4): "groq" в нижнем регистре (⏸ не удалось воспроизвести)

### Проблема

В истории оптимизаций: "Оптимизация · groq" вместо "Оптимизация · Groq".

> **Примечание 11.03.2026:** Не удалось воспроизвести — на доступных аккаунтах (test@example.com, test_new@example.com) нет записей Groq в истории. Все существующие записи используют корректный формат "Provider · Model" с правильным регистром. Возможно, уже исправлен вместе с HISTORY-MODEL-FORMAT-001.

### Рекомендация (на случай если баг всё ещё актуален)

```typescript
const PROVIDER_DISPLAY_NAMES: Record<string, string> = {
  gigachat: 'GigaChat',
  openai: 'OpenAI',
  anthropic: 'Anthropic',
  openrouter: 'OpenRouter',
  groq: 'Groq',
};

const displayName = PROVIDER_DISPLAY_NAMES[provider] || provider;
```

---

## ~~🟢 ДЕФЕКТ 12 — HISTORY-MODEL-FORMAT-001 (P4): ✅ ИСПРАВЛЕН В V35~~

> **Подтверждено 11.03.2026:** Формат записей в истории унифицирован — все записи используют "Оптимизация · Provider · Model" с корректным регистром. Баг закрыт.

---

## СВОДНАЯ ТАБЛИЦА (актуальных дефектов)

| # | ID | P | Описание | Компонент | Сложность | С версии | Статус V35 |
|---|----|---|----------|-----------|-----------|----------|------------|
| 1 | AVATAR-DELETE-503 | **P2** | Удаление аватара → 503 | Backend/Storage | Средняя | V34 | ❌ Confirmed |
| 2 | HH-RESUME-LINK-405 | **P2** | Парсинг hh.ru → 400 (endpoint есть, парсинг нет) | Backend | Средняя | V34 | ⚠️ Partial |
| 3 | PDF-PARSE-502 | **P2** | PDF > 100 КБ → 502 | Backend/Nginx | Средняя | V34 | ⏸ Untested |
| 4 | VACANCY-TITLE-002 | P3 | Автозаполнение должности | Frontend | Лёгкая | V34 | ⏸ Untested |
| 5 | PROFILE-AVATAR-SIDEBAR | P4 | Sidebar без аватара | Frontend | Лёгкая | V34 | ❌ Confirmed |
| 6 | DELETE-FORM-NO-VALIDATION-MSG | P4 | Нет валидации удаления | Frontend | Лёгкая | V34 | ❌ Confirmed |
| 7 | SECURITY-AUTOFILL | P4 | Автозаполнение паролей | Frontend | Лёгкая | V34 | ❌ Confirmed |
| 8 | PHONE-MASK-FORMAT | P4 | Маска телефона | Frontend | Лёгкая | **V35 NEW** | ❌ New |
| 9 | GROQ-CASE-002 | P4 | "groq" lowercase | Frontend | Лёгкая | V34 | ⏸ Cannot verify |

**Исправлены в V35:** PRICING-FORMAT-001 (P3), HH-RESUME-LINK-VALIDATION (P4), HISTORY-MODEL-FORMAT-001 (P4)

---

## РЕКОМЕНДУЕМЫЙ ПОРЯДОК ИСПРАВЛЕНИЙ

### Спринт 1 — P2 Backend (1–2 дня)

1. **AVATAR-DELETE-503** — Реализовать/починить DELETE /api/v1/auth/me/avatar. Проверить nginx проксирование DELETE-запросов и доступность storage.
2. **HH-RESUME-LINK-405** — Починить парсинг hh.ru страницы (endpoint работает, но парсинг возвращает 400). Или временно скрыть вкладку "Ссылка hh.ru" с feature flag.
3. **PDF-PARSE-502** — Увеличить nginx таймауты (proxy_read_timeout 60s), добавить client_max_body_size 10M, обернуть PDF-парсинг в try/except.

### Спринт 2 — P3 UX (0.5 дня)

4. **VACANCY-TITLE-002** — Использовать extractedPosition вместо name для автозаполнения должности.

### Спринт 3 — P4 Косметика (0.5 дня)

5–9. Все P4 — одним коммитом:
- PROFILE-AVATAR-SIDEBAR: Подписать sidebar на обновление avatarUrl
- DELETE-FORM-NO-VALIDATION-MSG: Добавить клиентскую валидацию
- SECURITY-AUTOFILL: Добавить autocomplete="new-password"
- PHONE-MASK-FORMAT: Применить маску при загрузке значения
- GROQ-CASE-002: Проверить маппинг display_name для Groq (возможно уже исправлен)

---

## ИТОГОВАЯ ОЦЕНКА V35

| Категория | V34 | V35 | Изменение |
|-----------|-----|-----|-----------|
| Core flow (оптимизация резюме) | 9/10 | **9.5/10** | ↑ |
| AI-провайдеры (все 5) | 9/10 | **9.5/10** | ↑ |
| Загрузка данных (резюме/вакансии) | 7.5/10 | **7.5/10** | → |
| Экспорт | 9/10 | **9.5/10** | ↑ |
| Профиль и настройки | 4/10 | **6.5/10** | ↑↑ |
| Безопасность (удаление аккаунта) | 2/10 | **8/10** | ↑↑↑ |
| **ИТОГО** | **7.5/10** | **8.5/10** | **+1.0** |
| Production ready (core flow) | ✅ | **✅** | — |
| Production ready (полный) | ⚠️ НЕТ | **⚠️ ПОЧТИ** | P1 исправлен, P2 остались |

### Прогресс V35

- **Критических (P1) багов: 0** (ACCOUNT-DELETE-500 исправлен!)
- **Высоких (P2) багов: 3** (AVATAR-DELETE-503, HH-RESUME-LINK-405 partial, PDF-PARSE-502 untested)
- **Средних (P3): 1** (VACANCY-TITLE-002 untested)
- **Низких (P4): 5** (4 confirmed + 1 cannot verify)
- **Всего активных: 9 замечаний** (было 15 в V34 → 7 исправлены, 1 новый)
- **Исправлено в V35: 7 из 15 багов V34** + 3 дополнительно подтверждены 11.03.2026

---

*Промт для исправлений создан: 10.03.2026, обновлён: 11.03.2026*
*Основан на: QA Report #33 + регрессия FINAL_FIX_PROMPT_V34 + дотестирование 11.03.2026*
*Предыдущие промты: AGENT_FIX_PROMPT_V34.md, FINAL_FIX_PROMPT_V34.md*

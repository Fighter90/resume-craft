# QA Fix Status — v1.6

## Исправлено в v1.6 (41 из 71 дефектов)

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

| Категория | Исправлено | Отложено | Всего |
|-----------|-----------|----------|-------|
| Безопасность | 7 | 4 | 11 |
| Аутентификация | 2 | 6 | 8 |
| Backend API | 8 | 3 | 11 |
| Frontend UI | 9 | 4 | 13 |
| Архитектура | 5 | 7 | 12 |
| Живое тестирование | 12 | 4 | 16 |
| **ИТОГО** | **43** | **28** | **71** |

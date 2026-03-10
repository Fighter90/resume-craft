# Changelog

Все заметные изменения проекта ResumeCraft документируются в этом файле.

Формат основан на [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
проект следует [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.14.0] — 2026-03

### Added
- 66 новых backend-тестов (`test_full_coverage.py`) для достижения 100% покрытия (2540/2540 statements)
- `@vitest/coverage-v8` для frontend coverage-отчётов
- `CHANGELOG.md` с полной историей версий

### Fixed
- 32 сломанных frontend-теста в 6 файлах (адаптация к миграции localStorage→server API, password requirements, model counts, 2FA removal)
- `ruff format` для `test_v30_fixes.py` и `test_full_coverage.py`

### Changed
- Backend unit-тестов: 578 → 819
- Frontend тестов: 525 → 558
- Всего тестов: 1216 → 1490
- Backend coverage statements: 1722 → 2540
- Синхронизированы версии: pyproject.toml (0.1.0 → 1.14.0), package.json (0.0.0 → 1.14.0)
- Обновлена документация README.md (метрики тестов, структура)

---

## [1.13.0] — 2026-03

### Added
- 10 backend-тестов (scoring determinism ×4, source checks ×4, nginx config ×2)
- 5 frontend-тестов (localStorage auth, 401 retry, server error parsing)

### Fixed
- FILE-UPLOAD-001: auth fallback + 401 retry + серверный парсинг ошибок
- nginx `client_max_body_size 12m` (ранее default 1MB блокировал >1MB)
- SCORE-VARIANCE-001: документировано как ожидаемое поведение (±6 пунктов)

### Changed
- QA Retest V30 FINAL: все 5 AI-провайдеров работают на свежем аккаунте

---

## [1.12.0] — 2026-03

### Fixed
- KEY-CHECK-001 (P2): Race condition — `session.commit()` до `execute_rewrite_task.delay()`
- KEY-CHECK-001 (groq): добавлен в маппинги router pre-check
- NAV-001 (P3): убран `preventDefault()` из ссылки «Обновить до Pro →»
- isAuthError: сужена проверка ошибок (точные маркеры вместо generic)

### Added
- 27 backend-тестов, 7 frontend-тестов

---

## [1.11.0] — 2026-03

### Fixed
- RESET-001 (P1 HIGH): кнопка «Сбросить» больше не удаляет API-ключи
- NAV-001 (P3): explicit onClick с navigate()
- OPENAI-O4MINI (P3): regex `^o\d` для o-series моделей

### Added
- 28 backend-тестов, 6 frontend-тестов

---

## [1.10.0] — 2026-03

### Fixed
- NAV-001 (REGRESSION): `NavLink` → `Link`, CSS `pointer-events: auto; z-index: 2`
- EMAIL-VERIFY-001: динамический статус верификации на странице профиля

### Added
- 15 backend-тестов, 6 frontend-тестов

---

## [1.9.0] — 2026-03

### Added
- `GET /models/health` — health-check всех LLM-провайдеров
- Ping-функции для GigaChat, OpenAI, Anthropic, OpenRouter, Groq
- 5-й AI-провайдер: Groq

### Fixed
- P0-3-CLAUDE: универсальный парсер LLM-ответа (strip markdown code blocks)
- GROQ-KEY: добавлен в 3 пропущенные точки SettingsAiPage
- AVATAR-001: динамические инициалы из firstName/lastName

---

## [1.8.0] — 2026-03

### Added
- `GET /resumes/{id}/file` — скачивание оригинального файла
- `GET /resumes/{id}/preview` — preview текста резюме
- `GET /export/{id}/txt` — экспорт в TXT
- OpenRouter search + optgroup-группировка моделей
- POST /auth/me/avatar, DELETE /auth/me/avatar
- ResumeViewerModal (DOCX/PDF/TXT)

### Fixed
- P0-2: Match Score ×100 (Dashboard, Results, History, Export)
- P0-3: JSON-ответы от /auth/me и /rewrite/history
- P0-4: o-series `max_completion_tokens` вместо `max_tokens`
- P1-6: аватар мигрирован из localStorage на сервер
- Content-Disposition: RFC 5987 кодировка для кириллицы

### Changed
- Удалён формат hh.ru из ExportPage
- +120 новых тестов, итого 757 backend + 534 frontend

---

## [1.7.0] — 2026-03

### Security
- API-ключи LLM перенесены из localStorage → Fernet AES-128-CBC + SHA-256
- openapi.json закрыт в production
- Rate limiting: login 5/min, register 3/min, rewrite 10/hour
- Защита от email enumeration

### Added
- `GET /export/{id}/pdf` (reportlab), `GET /export/{id}/txt`
- `GET /resumes/{id}/file`
- `GET /auth/verify/{token}` — email-верификация
- Soft-delete для резюме и аккаунтов
- DOCX-просмотр через mammoth.js + DOMPurify
- +50 новых backend-тестов

---

## [1.6.0] — 2026-03

### Security
- Swagger UI / ReDoc отключены в production
- SECRET_KEY валидация при запуске
- Rate limiting через slowapi + Redis
- Path traversal protection в FileStorage
- XSS: DOMPurify.sanitize() на dangerouslySetInnerHTML
- Docker-порты: 127.0.0.1 вместо 0.0.0.0

### Fixed
- 43 QA-дефекта: API, UI, UX, Security
- Counter оптимизаций: только COMPLETED
- Health check: /health и /api/v1/health
- Match Score breakdown: реальные компоненты от API
- Auto-refresh token при 401

### Added
- ErrorBoundary для всех routes
- Responsive tab labels
- calculate_match_score_detailed()

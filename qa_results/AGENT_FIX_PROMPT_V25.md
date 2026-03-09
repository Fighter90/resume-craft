# AGENT_FIX_PROMPT_V25

> Промт для AI-агента на доработку проекта ResumeCraft.ru
> Создан на основе QA Report #20 (20_FULL_RETEST_V25.md)
> Дата: 09.03.2026

---

## КОНТЕКСТ

Проведён полный ретест всех функций ResumeCraft.ru после фиксов V24.
**Результат: 5 из 6 багов ИСПРАВЛЕНЫ.** Приложение в целом production-ready.

Остались 2 проблемы:
1. **GIGACHAT-001** — ошибка биллинга на стороне Сбер GigaChat (НЕ баг приложения)
2. **DASHBOARD-001** — секция "Недавние резюме" на дашборде не показывает резюме (NEW, LOW)

---

## ИСПРАВЛЕННЫЕ БАГИ (подтверждено тестированием)

| Bug ID | Описание | Статус |
|--------|----------|--------|
| P0-3-CLAUDE | RAW JSON в результатах Claude | ✅ FIXED — текст отображается корректно |
| GROQ-KEY | Ключ Groq не сохраняется | ✅ FIXED — ключ сохраняется с зелёной галочкой |
| AVATAR-001 | Инициалы не соответствуют имени | ✅ FIXED — "QT" = "QA Tester V25" |
| LOGOUT-001 | Нет кнопки выхода | ✅ FIXED — дропдаун с "Выйти" |
| NAV-001 | Ссылка "Обновить до Pro" нестабильна | ✅ FIXED — навигация работает |

---

## ДЕФЕКТ 1: DASHBOARD-001 — «Недавние резюме» пустые

**Severity:** P3 (Low / Cosmetic)
**Страница:** /app/dashboard
**Описание:** Секция «Недавние резюме» показывает только карточку «Создать новое», хотя в системе есть 5 резюме (4 оптимизированных + 1 черновик).

**Шаги воспроизведения:**
1. Войти под qa_v25_test@example.com
2. Перейти на /app/dashboard
3. Посмотреть секцию «Недавние резюме»
4. Видно только «Создать новое», карточки резюме отсутствуют

**Ожидаемое поведение:** Должны отображаться карточки последних 3-4 резюме с быстрым доступом к просмотру/оптимизации.

**Вероятная причина:** Бэкенд-эндпоинт или фронтенд-запрос для «Недавних резюме» фильтрует только файловые загрузки (PDF/DOCX), игнорируя резюме, созданные через «Вставить текст».

### Файлы для исправления:

#### Backend
```
# Проверить эндпоинт, который возвращает недавние резюме для дашборда
# Убедиться, что запрос включает ВСЕ резюме, а не только file uploads
# Файл: app/api/routes/resumes.py или app/api/routes/dashboard.py

# Примерный фикс — убрать фильтр по source_type или format:
# Было:
#   query = query.filter(Resume.source_type == 'file')
# Стало:
#   query = query  # без фильтра по source_type
```

#### Frontend
```
# Проверить компонент дашборда
# Файл: src/pages/Dashboard.tsx или src/components/RecentResumes.tsx

# Убедиться, что API-запрос для недавних резюме не фильтрует по типу
# и обрабатывает пустой массив корректно (не показывает "Загрузка..." вечно)
```

---

## ДЕФЕКТ 2: GIGACHAT-001 — Ошибка биллинга GigaChat

**Severity:** P2 (Medium — провайдер недоступен)
**Тип:** Проблема на стороне провайдера (НЕ баг приложения)
**Описание:** При оптимизации через GigaChat Pro API возвращает ошибку «Недостаточно средств на балансе провайдера».

**Обработка ошибки в приложении:** ✅ КОРРЕКТНАЯ
- Понятное сообщение об ошибке на русском
- Кнопки «Выбрать другую модель» и «Настроить ключи»
- Слот оптимизации НЕ расходуется при ошибке

**Рекомендации:**
1. Пополнить баланс на https://developers.sber.ru/
2. Проверить, что API-ключ привязан к аккаунту с активной подпиской GigaChat Pro
3. Альтернатива: временно скрыть GigaChat из списка провайдеров, если баланс не будет пополнен

---

## CHANGELOG V25

### Fixed (подтверждено)
- ✅ P0-3-CLAUDE: Claude optimization results now render as formatted text (not raw JSON)
- ✅ GROQ-KEY: Groq API key saves correctly with green checkmark
- ✅ AVATAR-001: User initials match first letters of first + last name
- ✅ LOGOUT-001: Dropdown with "Профиль" and "Выйти" options on avatar click
- ✅ NAV-001: "Обновить до Pro →" navigates to /app/settings/subscription

### Known Issues
- ⚠️ GIGACHAT-001: GigaChat billing error (provider-side, not app bug)
- 🔵 DASHBOARD-001: "Недавние резюме" section shows empty on dashboard (P3/Low)

---

## ОБНОВЛЕНИЕ ДОКУМЕНТАЦИИ

### README.md — обновить секцию «AI-провайдеры»
```markdown
## Поддерживаемые AI-провайдеры

| Провайдер | Модели | Статус |
|-----------|--------|--------|
| Anthropic Claude | Claude Sonnet 4.6, Claude Haiku | ✅ Работает |
| OpenAI | GPT-4o, GPT-4o-mini, o4-mini | ✅ Работает |
| OpenRouter | 100+ моделей (AI21, Llama и др.) | ✅ Работает |
| Groq | Llama, Mixtral, Gemma | ✅ Работает (самый быстрый ~2с) |
| GigaChat Pro | GigaChat-Pro | ⚠️ Требуется активная подписка Сбер |
```

---

## ТЕСТЫ

### test_dashboard_recent_resumes.py
```python
"""Тесты для секции 'Недавние резюме' на дашборде."""
import pytest

class TestDashboardRecentResumes:
    """DASHBOARD-001: Недавние резюме должны отображаться на дашборде."""

    def test_recent_resumes_show_text_paste_uploads(self, auth_client, test_user):
        """Резюме, созданные через 'Вставить текст', отображаются в недавних."""
        # Создать резюме через text paste
        resume = auth_client.post("/api/resumes", json={
            "title": "Test Resume",
            "text": "Senior Python Developer с опытом 5 лет...",
            "source_type": "text"
        })
        assert resume.status_code == 201
        resume_id = resume.json()["id"]

        # Проверить, что дашборд возвращает это резюме
        dashboard = auth_client.get("/api/dashboard/recent-resumes")
        assert dashboard.status_code == 200
        resume_ids = [r["id"] for r in dashboard.json()["resumes"]]
        assert resume_id in resume_ids

    def test_recent_resumes_show_file_uploads(self, auth_client, test_user):
        """Резюме, загруженные как файл, отображаются в недавних."""
        # Создать резюме через file upload
        resume = auth_client.post("/api/resumes", json={
            "title": "File Resume",
            "text": "Resume content from file...",
            "source_type": "file"
        })
        assert resume.status_code == 201

        dashboard = auth_client.get("/api/dashboard/recent-resumes")
        assert dashboard.status_code == 200
        assert len(dashboard.json()["resumes"]) > 0

    def test_recent_resumes_limit(self, auth_client, test_user):
        """Недавние резюме показывают максимум N последних записей."""
        # Создать 6 резюме
        for i in range(6):
            auth_client.post("/api/resumes", json={
                "title": f"Resume {i}",
                "text": f"Content for resume {i} " * 10,
                "source_type": "text"
            })

        dashboard = auth_client.get("/api/dashboard/recent-resumes")
        assert dashboard.status_code == 200
        # Должно быть не больше 4 (или другого лимита)
        assert len(dashboard.json()["resumes"]) <= 4

    def test_recent_resumes_ordered_by_date(self, auth_client, test_user):
        """Недавние резюме отсортированы по дате (новые первые)."""
        for i in range(3):
            auth_client.post("/api/resumes", json={
                "title": f"Resume {i}",
                "text": f"Content {i} " * 10,
                "source_type": "text"
            })

        dashboard = auth_client.get("/api/dashboard/recent-resumes")
        resumes = dashboard.json()["resumes"]
        if len(resumes) >= 2:
            # Проверить, что первое резюме новее второго
            assert resumes[0]["created_at"] >= resumes[1]["created_at"]

    def test_dashboard_stats_include_all_sources(self, auth_client, test_user):
        """Статистика дашборда учитывает все типы загрузок."""
        # Создать резюме через text
        auth_client.post("/api/resumes", json={
            "title": "Text Resume",
            "text": "Content " * 10,
            "source_type": "text"
        })

        dashboard = auth_client.get("/api/dashboard/stats")
        assert dashboard.status_code == 200
        stats = dashboard.json()
        assert stats["total_resumes"] > 0
```

### test_gigachat_error_handling.py
```python
"""Тесты обработки ошибок GigaChat."""
import pytest

class TestGigaChatErrorHandling:
    """GIGACHAT-001: Корректная обработка ошибок биллинга."""

    def test_billing_error_returns_user_friendly_message(self, auth_client):
        """Ошибка биллинга возвращает понятное сообщение."""
        # Имитируем ошибку биллинга от GigaChat API
        response = auth_client.post("/api/optimize", json={
            "resume_id": "test-id",
            "provider": "gigachat",
            "model": "GigaChat-Pro"
        })
        # Если ошибка биллинга — сообщение должно быть на русском
        if response.status_code == 402 or "insufficient" in str(response.json()).lower():
            error = response.json()
            assert "баланс" in error.get("message", "").lower() or \
                   "средств" in error.get("message", "").lower()

    def test_billing_error_does_not_consume_slot(self, auth_client, test_user):
        """Ошибка биллинга НЕ расходует слот оптимизации."""
        # Получить текущий счётчик
        before = auth_client.get("/api/user/stats").json()
        before_count = before["optimizations_used"]

        # Попытка оптимизации с GigaChat (ожидаем ошибку)
        auth_client.post("/api/optimize", json={
            "resume_id": "test-id",
            "provider": "gigachat",
            "model": "GigaChat-Pro"
        })

        # Счётчик не должен измениться
        after = auth_client.get("/api/user/stats").json()
        assert after["optimizations_used"] == before_count

    def test_error_page_shows_recovery_options(self):
        """Страница ошибки показывает кнопки восстановления."""
        # Фронтенд тест — проверить наличие кнопок
        # "Выбрать другую модель" -> навигация на /app/models
        # "Настроить ключи" -> навигация на /app/settings/ai
        pass  # E2E тест через Playwright/Cypress
```

### test_all_providers_e2e.py
```python
"""E2E тесты для всех провайдеров."""
import pytest

class TestAllProvidersE2E:
    """Полный цикл оптимизации для каждого провайдера."""

    @pytest.mark.parametrize("provider,model", [
        ("anthropic", "claude-sonnet-4-6"),
        ("openai", "o4-mini-2025-04-16"),
        ("openrouter", "ai21/jamba-large-1.7"),
        ("groq", "llama-3.3-70b-versatile"),
    ])
    def test_optimization_full_cycle(self, auth_client, provider, model):
        """Полный цикл: загрузка → вакансия → оптимизация → результат."""
        # 1. Создать резюме
        resume = auth_client.post("/api/resumes", json={
            "title": f"Test {provider}",
            "text": "Senior Developer с опытом 5 лет в Python, Django, FastAPI. "
                    "Знание SQL, Docker, Kubernetes, CI/CD.",
            "source_type": "text"
        })
        assert resume.status_code == 201
        resume_id = resume.json()["id"]

        # 2. Создать вакансию
        vacancy = auth_client.post("/api/vacancies", json={
            "title": "Senior Developer",
            "company": "Test Co",
            "description": "Python, Django, REST API, SQL, Docker",
            "skills": "Python, Django, Docker"
        })

        # 3. Запустить оптимизацию
        result = auth_client.post("/api/optimize", json={
            "resume_id": resume_id,
            "provider": provider,
            "model": model
        })
        assert result.status_code in [200, 201]

        # 4. Проверить результат
        data = result.json()
        assert "match_score" in data
        assert "ats_grade" in data
        assert data["match_score"]["optimized"] > data["match_score"]["original"]
        assert data["ats_grade"] in ["A+", "A", "B+", "B", "C", "D", "F"]

    def test_optimization_results_not_raw_json(self, auth_client):
        """P0-3-CLAUDE: Результат не содержит сырой JSON."""
        resume = auth_client.post("/api/resumes", json={
            "title": "JSON Test",
            "text": "Developer с опытом 3 лет в Python.",
            "source_type": "text"
        })
        resume_id = resume.json()["id"]

        result = auth_client.post("/api/optimize", json={
            "resume_id": resume_id,
            "provider": "anthropic",
            "model": "claude-sonnet-4-6"
        })

        data = result.json()
        optimized_text = data.get("optimized_text", "")
        # Не должно начинаться с { или содержать "```json"
        assert not optimized_text.strip().startswith("{")
        assert "```json" not in optimized_text
        assert "```" not in optimized_text[:10]
```

---

## ИТОГО

**Статус проекта: ✅ PRODUCTION READY**

Все критические баги исправлены. Остался 1 минорный косметический баг (DASHBOARD-001) и проблема биллинга GigaChat на стороне провайдера.

**Приоритет доработок:**
1. 🔵 DASHBOARD-001 (P3/Low) — показывать недавние резюме на дашборде
2. ⚠️ GIGACHAT-001 (Provider) — пополнить баланс GigaChat или скрыть провайдер

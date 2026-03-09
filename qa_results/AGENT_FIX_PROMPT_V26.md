# AGENT_FIX_PROMPT_V26

> Промт для AI-агента на доработку проекта ResumeCraft.ru
> Создан на основе QA Report #21 (21_FULL_RETEST_V26.md)
> Дата: 09.03.2026

---

## КОНТЕКСТ

Проведён повторный полный ретест всех функций ResumeCraft.ru после фиксов V25.
**Результат: 6 из 7 багов ИСПРАВЛЕНЫ.** Приложение production-ready.

Остались 3 проблемы:
1. **NAV-001** — ссылка «Обновить до Pro →» не реагирует на физический клик мыши (REGRESSION, P3)
2. **EMAIL-VERIFY-001** — противоречие баннера верификации email между Dashboard и Profile (NEW, P3)
3. **GIGACHAT-001** — ошибка биллинга на стороне Сбер GigaChat (НЕ баг приложения)

---

## ИСПРАВЛЕННЫЕ БАГИ (подтверждено ретестом V26)

| Bug ID | Описание | V25 | V26 |
|--------|----------|-----|-----|
| P0-3-CLAUDE | RAW JSON в результатах Claude | ✅ FIXED | ✅ CONFIRMED |
| GROQ-KEY | Ключ Groq не сохраняется | ✅ FIXED | ✅ CONFIRMED |
| AVATAR-001 | Инициалы не соответствуют имени | ✅ FIXED | ✅ CONFIRMED |
| LOGOUT-001 | Нет кнопки выхода | ✅ FIXED | ✅ CONFIRMED |
| DASHBOARD-001 | «Недавние резюме» пустые | 🔵 BUG | ✅ FIXED |

---

## ДЕФЕКТ 1: NAV-001 — «Обновить до Pro →» не кликается мышью

**Severity:** P3 (Low)
**Страница:** Sidebar на всех страницах /app/*
**Статус:** REGRESSION — в V25 был отмечен как FIXED, в V26 физический клик не работает

**Описание:** Ссылка «Обновить до Pro →» в нижней части sidebar не реагирует на физический клик мыши. При этом:
- `document.elementFromPoint(x, y)` корректно находит элемент `<a class="plan-upgrade" href="/app/settings/subscription">`
- Программный `element.click()` через JavaScript — навигация работает
- `dispatchEvent(new MouseEvent('click'))` показывает `{hasOnClick: true, dispatched: false}` — обработчик вызывает `preventDefault()`

**Шаги воспроизведения:**
1. Войти в аккаунт
2. На любой странице /app/* посмотреть sidebar внизу
3. Кликнуть мышью на «Обновить до Pro →»
4. Навигация НЕ происходит

**Ожидаемое поведение:** Клик мышью навигирует на /app/settings/subscription

**Вероятная причина:** Один из вариантов:
1. CSS-элемент (overlay, pseudo-element, или контейнер с `pointer-events: none`) перекрывает ссылку, перехватывая клик
2. React onClick handler на ссылке или родительском элементе вызывает `e.preventDefault()` без последующей навигации
3. Z-index конфликт — другой элемент выше по z-stack перекрывает ссылку

### Файлы для исправления:

#### Вариант 1: CSS overlay проблема
```css
/* Проверить sidebar компонент на наличие overlay элементов */
/* Файл: src/components/Sidebar.tsx или src/components/Layout.tsx */

/* Проверить, что .plan-upgrade (или аналогичный класс) имеет: */
.plan-upgrade {
  position: relative;
  z-index: 10; /* достаточно высокий */
  pointer-events: auto; /* разрешить клики */
  cursor: pointer;
}

/* Убрать любые overlay с pointer-events: auto поверх sidebar */
/* Проверить ::before и ::after pseudo-elements родительских контейнеров */
```

#### Вариант 2: React Router handler
```tsx
/* Файл: src/components/Sidebar.tsx */

/* Было (вероятно): */
<a href="/app/settings/subscription" onClick={(e) => {
  e.preventDefault();
  navigate('/app/settings/subscription');
}}>
  Обновить до Pro →
</a>

/* Правильный вариант — использовать Link из react-router-dom: */
import { Link } from 'react-router-dom';

<Link to="/app/settings/subscription" className="plan-upgrade">
  Обновить до Pro →
</Link>

/* ИЛИ убрать preventDefault, если <a> с href достаточно: */
<a href="/app/settings/subscription">
  Обновить до Pro →
</a>
```

#### Диагностика (запустить в DevTools)
```javascript
// 1. Проверить z-index стек над ссылкой
const link = document.querySelector('a[href*="subscription"]');
const rect = link.getBoundingClientRect();
const centerX = rect.left + rect.width / 2;
const centerY = rect.top + rect.height / 2;
const topElement = document.elementFromPoint(centerX, centerY);
console.log('Top element:', topElement, topElement === link);

// 2. Проверить event listeners
getEventListeners(link); // Chrome DevTools only

// 3. Проверить pointer-events
const computed = window.getComputedStyle(link);
console.log('pointer-events:', computed.pointerEvents);
console.log('z-index:', computed.zIndex);
console.log('position:', computed.position);

// 4. Проверить все родители на overflow/pointer-events
let el = link;
while (el && el !== document.body) {
  const s = window.getComputedStyle(el);
  if (s.pointerEvents === 'none' || s.overflow === 'hidden') {
    console.log('BLOCKER:', el, s.pointerEvents, s.overflow);
  }
  el = el.parentElement;
}
```

---

## ДЕФЕКТ 2: EMAIL-VERIFY-001 — Противоречие верификации email

**Severity:** P3 (Low / Cosmetic)
**Страницы:** /app/dashboard + /app/settings/profile
**Тип:** Несогласованность данных

**Описание:** Dashboard показывает жёлтый баннер «Подтвердите email qa_v25_test@example.com для полного доступа ко всем функциям», но Profile показывает email как «Подтверждён» с зелёной галочкой.

**Шаги воспроизведения:**
1. Войти под qa_v25_test@example.com
2. На /app/dashboard видно жёлтый баннер «Подтвердите email...»
3. Перейти на /app/settings/profile
4. Поле Email показывает зелёную галочку «Подтверждён»

**Ожидаемое поведение:**
- Если email подтверждён → баннер НЕ показывается
- Если email НЕ подтверждён → Profile НЕ показывает «Подтверждён»

### Файлы для исправления:

#### Backend — проверить единый источник истины
```python
# Файл: app/api/routes/auth.py или app/api/routes/users.py

# Убедиться, что поле email_verified одинаково во всех ответах API:
# GET /api/user/profile -> {"email_verified": true/false}
# GET /api/user/me -> {"email_verified": true/false}
# JWT token claims -> {"email_verified": true/false}

# Все три должны использовать ОДНО поле из БД:
# user.email_verified (boolean)
```

#### Frontend — Dashboard баннер
```tsx
/* Файл: src/pages/Dashboard.tsx или src/components/EmailVerificationBanner.tsx */

/* Проверить условие показа баннера: */
/* Было (вероятно): */
{!user.emailVerified && (
  <Banner>Подтвердите email...</Banner>
)}

/* Убедиться, что user.emailVerified берётся из того же источника,
   что и на странице Profile */

/* Если баннер использует старые данные из JWT — обновить при логине: */
const { data: profile } = useQuery('profile', fetchProfile);
{!profile?.email_verified && (
  <Banner>Подтвердите email...</Banner>
)}
```

#### Frontend — Profile
```tsx
/* Файл: src/pages/Settings/Profile.tsx */

/* Проверить, откуда берётся статус «Подтверждён»: */
/* Если из другого API-эндпоинта — унифицировать */

/* Оба компонента должны использовать один источник: */
const isVerified = user.email_verified; // из одного API-ответа
```

---

## ДЕФЕКТ 3: GIGACHAT-001 — Ошибка биллинга GigaChat

**Severity:** P2 (Medium — провайдер недоступен)
**Тип:** Проблема на стороне провайдера (НЕ баг приложения)
**Описание:** GigaChat Pro API возвращает «Недостаточно средств на балансе провайдера».

**Обработка ошибки в приложении:** ✅ КОРРЕКТНАЯ
- Понятное сообщение об ошибке на русском ✅
- Кнопки «Выбрать другую модель» и «Настроить ключи» ✅
- Слот оптимизации НЕ расходуется при ошибке ✅

**Рекомендации:**
1. Пополнить баланс на https://developers.sber.ru/
2. Проверить, что API-ключ привязан к аккаунту с активной подпиской GigaChat Pro
3. Альтернатива: временно скрыть GigaChat из списка провайдеров, если баланс не будет пополнен

---

## CHANGELOG V26

### Fixed (подтверждено ретестом V26)
- ✅ DASHBOARD-001: Recent resumes section now shows resume cards (DevOps Engineer + QA Engineer)
- ✅ Dashboard "Загружено резюме" counter fixed: now shows 5 (was 0)
- ✅ P0-3-CLAUDE: Confirmed — optimization results render as formatted text
- ✅ GROQ-KEY: Confirmed — Groq API key saves with green checkmark
- ✅ AVATAR-001: Confirmed — initials "QT" match "QA Tester V25"
- ✅ LOGOUT-001: Confirmed — dropdown with "Профиль" and "Выйти" on avatar click
- ✅ FAQ expanded from 10 to 12 questions

### Known Issues
- ⚠️ NAV-001: "Обновить до Pro →" does not respond to physical mouse clicks (P3, regression)
- 🔵 EMAIL-VERIFY-001: Email verification banner contradicts Profile page status (P3, new)
- ⚠️ GIGACHAT-001: GigaChat billing error (provider-side, not app bug)

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

### test_nav_upgrade_link.py
```python
"""Тесты для ссылки 'Обновить до Pro' в sidebar."""
import pytest
from playwright.sync_api import Page, expect

class TestNavUpgradeLink:
    """NAV-001: Ссылка 'Обновить до Pro' должна навигировать при клике мышью."""

    def test_upgrade_link_clickable(self, page: Page, auth_session):
        """Физический клик мышью на ссылку навигирует на /app/settings/subscription."""
        page.goto("/app/dashboard")

        # Найти ссылку
        link = page.locator('a[href*="subscription"]').filter(has_text="Pro")
        expect(link).to_be_visible()

        # Клик мышью (не JS)
        link.click()

        # Проверить навигацию
        expect(page).to_have_url("/app/settings/subscription")

    def test_upgrade_link_not_covered_by_overlay(self, page: Page, auth_session):
        """Ссылка не перекрыта другими элементами."""
        page.goto("/app/dashboard")

        link = page.locator('a[href*="subscription"]').filter(has_text="Pro")
        box = link.bounding_box()

        # Проверить, что elementFromPoint возвращает саму ссылку
        top_element = page.evaluate("""({x, y}) => {
            const el = document.elementFromPoint(x, y);
            return {
                tagName: el.tagName,
                href: el.href || el.closest('a')?.href,
                className: el.className
            };
        }""", {"x": box["x"] + box["width"] / 2, "y": box["y"] + box["height"] / 2})

        assert "subscription" in (top_element.get("href") or "")

    def test_upgrade_link_pointer_events(self, page: Page, auth_session):
        """CSS pointer-events не блокирует клик."""
        page.goto("/app/dashboard")

        link = page.locator('a[href*="subscription"]').filter(has_text="Pro")

        # Проверить computed styles
        pointer_events = link.evaluate("el => window.getComputedStyle(el).pointerEvents")
        assert pointer_events != "none"

        # Проверить всю цепочку родителей
        has_blocker = link.evaluate("""el => {
            let current = el;
            while (current && current !== document.body) {
                const style = window.getComputedStyle(current);
                if (style.pointerEvents === 'none') return current.tagName + '.' + current.className;
                current = current.parentElement;
            }
            return null;
        }""")
        assert has_blocker is None, f"Parent blocks pointer events: {has_blocker}"
```

### test_email_verification_consistency.py
```python
"""Тесты консистентности верификации email."""
import pytest

class TestEmailVerificationConsistency:
    """EMAIL-VERIFY-001: Статус верификации email должен быть единым."""

    def test_dashboard_banner_matches_profile(self, auth_client, test_user):
        """Баннер на дашборде соответствует статусу на Profile."""
        # Получить статус из Profile API
        profile = auth_client.get("/api/user/profile")
        assert profile.status_code == 200
        is_verified_profile = profile.json().get("email_verified", False)

        # Получить данные дашборда
        dashboard = auth_client.get("/api/dashboard")
        assert dashboard.status_code == 200
        show_banner = dashboard.json().get("show_email_verification_banner", True)

        # Если Profile говорит "подтверждён" — баннер НЕ должен показываться
        if is_verified_profile:
            assert not show_banner, "Dashboard shows verification banner but profile says email is verified"
        else:
            assert show_banner, "Dashboard hides banner but profile says email is NOT verified"

    def test_jwt_email_verified_matches_db(self, auth_client, test_user):
        """JWT claims совпадают с данными из БД."""
        # Получить данные из JWT (через /api/user/me)
        me = auth_client.get("/api/user/me")
        jwt_verified = me.json().get("email_verified")

        # Получить данные из Profile API (из БД)
        profile = auth_client.get("/api/user/profile")
        db_verified = profile.json().get("email_verified")

        assert jwt_verified == db_verified, \
            f"JWT says email_verified={jwt_verified}, DB says email_verified={db_verified}"

    def test_email_verification_single_source(self, auth_client):
        """Все API-эндпоинты возвращают одинаковый статус верификации."""
        endpoints = ["/api/user/me", "/api/user/profile", "/api/dashboard"]
        statuses = {}

        for endpoint in endpoints:
            resp = auth_client.get(endpoint)
            if resp.status_code == 200:
                data = resp.json()
                verified = data.get("email_verified") or \
                          data.get("user", {}).get("email_verified") or \
                          not data.get("show_email_verification_banner", True)
                statuses[endpoint] = verified

        # Все значения должны быть одинаковы
        values = list(statuses.values())
        assert len(set(values)) <= 1, \
            f"Inconsistent email verification status across endpoints: {statuses}"
```

### test_all_providers_e2e.py (обновлён)
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
        assert not optimized_text.strip().startswith("{")
        assert "```json" not in optimized_text
        assert "```" not in optimized_text[:10]
```

---

## ПРИОРИТЕТ ДОРАБОТОК

1. ⚠️ **NAV-001** (P3/Low) — исправить клик мышью на «Обновить до Pro →»
2. 🔵 **EMAIL-VERIFY-001** (P3/Low) — унифицировать статус верификации email
3. ⚠️ **GIGACHAT-001** (Provider) — пополнить баланс GigaChat или скрыть провайдер

---

## ИТОГО

**Статус проекта: ✅ PRODUCTION READY**

Все критические баги исправлены. Из V25 осталось 0 критических проблем. Два минорных косметических бага (NAV-001 regression + EMAIL-VERIFY-001 new) и проблема биллинга GigaChat на стороне провайдера.

**Прогресс с V25:**
- DASHBOARD-001: 🔵→✅ Исправлен
- NAV-001: ✅→⚠️ Регрессия (физический клик)
- EMAIL-VERIFY-001: — → 🔵 Новый
- Общая оценка: 9.5/10 → 9.3/10 (минус за регрессию NAV-001)

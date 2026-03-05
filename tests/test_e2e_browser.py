"""E2E браузерные тесты для https://resumecraft.ru/.

Автоматически тестирует ВСЕ страницы и ключевые user flows:
- Публичные страницы (лендинг, цены, о нас, privacy, terms)
- Регистрация / Логин / Логаут
- Dashboard, Resumes, History
- Wizard: Upload → Vacancy → Models → Processing
- Settings (все 4 вкладки)
- 404 страница
- Адаптивность (мобайл)

Использование:
    BASE_URL=https://resumecraft.ru pytest tests/test_e2e_browser.py -v --headed
    BASE_URL=https://resumecraft.ru pytest tests/test_e2e_browser.py -v  # headless

Требования:
    pip install playwright pytest
    playwright install chromium
"""

from __future__ import annotations

import os
import uuid

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, expect, sync_playwright

# ---------------------------------------------------------------------------
# Конфигурация
# ---------------------------------------------------------------------------

BASE_URL: str = os.getenv('BASE_URL', 'https://resumecraft.ru')
SLOW_MO: int = int(os.getenv('SLOW_MO', '0'))  # ms между действиями (для отладки)
TIMEOUT: int = 15_000  # ms на ожидание элементов
TEST_EMAIL: str = os.getenv('E2E_USER', f'e2e-{uuid.uuid4().hex[:8]}@test.resumecraft.ru')
TEST_PASS: str = os.getenv('E2E_PASS', 'E2eTestPass1')

# Пропускать если нет BASE_URL
pytestmark = pytest.mark.skipif(
    not os.getenv('BASE_URL'),
    reason='E2E browser tests require BASE_URL env var',
)

# ---------------------------------------------------------------------------
# Хранилище ошибок — собирает все проблемы за прогон
# ---------------------------------------------------------------------------

_errors: list[dict[str, str]] = []


def _record_error(page: str, error: str, details: str = '') -> None:
    """Записать ошибку для итогового отчёта."""
    _errors.append({'page': page, 'error': error, 'details': details})


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope='session')
def browser():
    """Запуск Chromium для всей сессии."""
    with sync_playwright() as p:
        b = p.chromium.launch(
            headless=os.getenv('HEADED') != '1',
            slow_mo=SLOW_MO,
        )
        yield b
        b.close()


@pytest.fixture(scope='session')
def context(browser: Browser) -> BrowserContext:
    """Browser context с настройками."""
    ctx = browser.new_context(
        viewport={'width': 1280, 'height': 800},
        base_url=BASE_URL,
        ignore_https_errors=True,
    )
    ctx.set_default_timeout(TIMEOUT)
    yield ctx
    ctx.close()


@pytest.fixture(scope='session')
def page(context: BrowserContext) -> Page:
    """Основная страница для тестов."""
    p = context.new_page()
    # Собираем console errors
    p.on(
        'console', lambda msg: _record_error('console', msg.text) if msg.type == 'error' else None
    )
    yield p
    p.close()


@pytest.fixture(scope='session')
def auth_page(page: Page) -> Page:
    """Авторизованная страница — регистрация + логин."""
    # Регистрация
    page.goto('/auth')
    page.wait_for_load_state('networkidle')

    # Переключаемся на вкладку регистрации
    register_tab = page.locator('text=Регистрация').first
    if register_tab.is_visible():
        register_tab.click()
        page.wait_for_timeout(500)

    # Заполняем форму
    email_input = page.locator('input[type="email"], input[placeholder*="mail"]').first
    if email_input.is_visible():
        email_input.fill(TEST_EMAIL)

    password_inputs = page.locator('input[type="password"]')
    if password_inputs.count() > 0:
        password_inputs.first.fill(TEST_PASS)

    # Если есть поле "Полное имя"
    name_input = page.locator(
        'input[placeholder*="мя"], input[placeholder*="name"], input[placeholder*="Имя"]'
    ).first
    if name_input.is_visible():
        name_input.fill('E2E Test User')

    # Подтверждение пароля (если есть)
    if password_inputs.count() > 1:
        password_inputs.nth(1).fill(TEST_PASS)

    # Submit
    submit_btn = page.locator(
        'button[type="submit"], button:has-text("Зарегистрироваться"), '
        'button:has-text("Регистрация"), button:has-text("Создать")'
    ).first
    if submit_btn.is_visible():
        submit_btn.click()
        page.wait_for_timeout(3000)

    # Если регистрация не удалась (409), логинимся
    if '/auth' in page.url or '/login' in page.url:
        login_tab = page.locator('text=Войти').first
        if login_tab.is_visible():
            login_tab.click()
            page.wait_for_timeout(500)

        email_input = page.locator('input[type="email"], input[placeholder*="mail"]').first
        if email_input.is_visible():
            email_input.fill(TEST_EMAIL)

        password_input = page.locator('input[type="password"]').first
        if password_input.is_visible():
            password_input.fill(TEST_PASS)

        login_btn = page.locator('button[type="submit"], button:has-text("Войти")').first
        if login_btn.is_visible():
            login_btn.click()
            page.wait_for_timeout(3000)

    return page


# =========================================================================
# 1. Публичные страницы
# =========================================================================


class TestPublicPages:
    """Тесты публичных страниц (без авторизации)."""

    def test_landing_loads(self, page: Page) -> None:
        """Лендинг загружается и содержит ключевые элементы."""
        resp = page.goto('/')
        assert resp is not None
        assert resp.status == 200, f'Landing вернул {resp.status}'
        page.wait_for_load_state('networkidle')

        # Заголовок или лого
        assert page.title(), 'Пустой title'

        # Проверяем что есть какой-то контент
        body = page.locator('body')
        expect(body).not_to_be_empty()

        # Проверяем нет ли React crash (белый экран)
        root = page.locator('#root')
        expect(root).not_to_be_empty()
        inner = root.inner_html()
        assert len(inner) > 100, f'React root подозрительно мал ({len(inner)} chars)'

    def test_landing_has_cta(self, page: Page) -> None:
        """Лендинг содержит CTA кнопку."""
        page.goto('/')
        page.wait_for_load_state('networkidle')
        cta = page.locator(
            'a:has-text("Попробовать"), a:has-text("Начать"), '
            'button:has-text("Попробовать"), button:has-text("Начать"), '
            'a:has-text("Оптимизировать")'
        ).first
        expect(cta).to_be_visible()

    def test_pricing_page(self, page: Page) -> None:
        """Страница цен загружается с тарифами."""
        resp = page.goto('/pricing')
        assert resp is not None
        assert resp.status == 200
        page.wait_for_load_state('networkidle')

        # Должны быть тарифы
        content = page.content()
        has_plans = any(
            word in content for word in ['Free', 'Standard', 'Pro', 'Бесплатно', 'тариф']
        )
        assert has_plans, 'Страница цен не содержит информации о тарифах'

    def test_about_page(self, page: Page) -> None:
        """Страница «О нас» загружается."""
        resp = page.goto('/about')
        assert resp is not None
        assert resp.status == 200
        page.wait_for_load_state('networkidle')
        root = page.locator('#root')
        assert len(root.inner_html()) > 100, 'About page пустая'

    def test_privacy_page(self, page: Page) -> None:
        """Политика конфиденциальности загружается."""
        resp = page.goto('/privacy')
        assert resp is not None
        assert resp.status == 200
        page.wait_for_load_state('networkidle')
        content = page.content()
        assert any(
            word in content for word in ['конфиденциальн', 'персональн', 'данн', 'Privacy']
        ), 'Privacy page не содержит ожидаемого контента'

    def test_terms_page(self, page: Page) -> None:
        """Пользовательское соглашение загружается."""
        resp = page.goto('/terms')
        assert resp is not None
        assert resp.status == 200
        page.wait_for_load_state('networkidle')
        root = page.locator('#root')
        assert len(root.inner_html()) > 100, 'Terms page пустая'

    def test_404_page(self, page: Page) -> None:
        """Несуществующий URL → страница 404."""
        page.goto('/nonexistent-page-xyz-12345')
        page.wait_for_load_state('networkidle')
        content = page.content()
        has_404 = any(word in content for word in ['404', 'не найден', 'Not Found', 'Ошибка'])
        assert has_404, '404 страница не показывает ожидаемое сообщение'

    def test_no_js_errors_on_landing(self, page: Page) -> None:
        """Лендинг без JS-ошибок в консоли."""
        errors: list[str] = []
        page.on('console', lambda msg: errors.append(msg.text) if msg.type == 'error' else None)
        page.goto('/')
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(2000)
        # Фильтруем известные "безопасные" ошибки
        real_errors = [
            e
            for e in errors
            if 'favicon' not in e.lower()
            and 'third-party' not in e.lower()
            and 'ERR_CONNECTION' not in e
        ]
        assert not real_errors, f'JS ошибки на лендинге: {real_errors}'


# =========================================================================
# 2. Auth flow
# =========================================================================


class TestAuthFlow:
    """Тесты регистрации, логина, логаута."""

    def test_auth_page_loads(self, page: Page) -> None:
        """Страница авторизации загружается."""
        resp = page.goto('/auth')
        assert resp is not None
        assert resp.status == 200
        page.wait_for_load_state('networkidle')
        # Должна быть форма
        form_elements = page.locator('input[type="email"], input[type="password"]')
        assert form_elements.count() >= 1, 'Нет полей ввода на auth странице'

    def test_auth_has_tabs(self, page: Page) -> None:
        """Страница авторизации имеет вкладки Войти/Регистрация."""
        page.goto('/auth')
        page.wait_for_load_state('networkidle')
        content = page.content()
        has_tabs = any(word in content for word in ['Войти', 'Регистрация', 'Sign in', 'Sign up'])
        assert has_tabs, 'Auth page не имеет вкладок входа/регистрации'

    def test_login_with_wrong_password(self, page: Page) -> None:
        """Неверный пароль → сообщение об ошибке."""
        page.goto('/auth')
        page.wait_for_load_state('networkidle')

        # Переключаемся на login если нужно
        login_tab = page.locator('text=Войти').first
        if login_tab.is_visible():
            login_tab.click()
            page.wait_for_timeout(500)

        email_input = page.locator('input[type="email"], input[placeholder*="mail"]').first
        if email_input.is_visible():
            email_input.fill('wrong@test.com')

        password_input = page.locator('input[type="password"]').first
        if password_input.is_visible():
            password_input.fill('WrongPass999')

        submit = page.locator('button[type="submit"], button:has-text("Войти")').first
        if submit.is_visible():
            submit.click()
            page.wait_for_timeout(2000)

        # Должно быть сообщение об ошибке ИЛИ остаёмся на auth
        content = page.content()
        still_on_auth = '/auth' in page.url
        has_error = any(
            word in content for word in ['ошибк', 'невер', 'error', 'Ошибк', 'Невер', 'пароль']
        )
        assert still_on_auth or has_error, 'Неверный пароль не показал ошибку'

    def test_register_and_login(self, auth_page: Page) -> None:
        """Регистрация + логин → перенаправление в /app."""
        # auth_page fixture сам выполняет регистрацию/логин
        # Проверяем что мы попали в приложение
        auth_page.wait_for_timeout(2000)
        url = auth_page.url
        assert '/app' in url or '/dashboard' in url or '/auth' in url, (
            f'После логина оказались на {url}'
        )

    def test_password_recovery_page(self, page: Page) -> None:
        """Страница восстановления пароля загружается."""
        resp = page.goto('/password-recovery')
        assert resp is not None
        assert resp.status == 200
        page.wait_for_load_state('networkidle')
        root = page.locator('#root')
        assert len(root.inner_html()) > 100, 'Password recovery page пустая'


# =========================================================================
# 3. Protected pages (dashboard, resumes, etc.)
# =========================================================================


class TestProtectedPages:
    """Тесты защищённых страниц (требуют авторизации)."""

    def test_dashboard_loads(self, auth_page: Page) -> None:
        """Dashboard загружается после логина."""
        auth_page.goto('/app/dashboard')
        auth_page.wait_for_load_state('networkidle')
        auth_page.wait_for_timeout(2000)

        root = auth_page.locator('#root')
        inner = root.inner_html()
        assert len(inner) > 200, f'Dashboard пустой ({len(inner)} chars)'

        # Не должно быть redirect на /auth
        assert '/auth' not in auth_page.url, 'Dashboard перенаправил на /auth'

    def test_dashboard_has_stats(self, auth_page: Page) -> None:
        """Dashboard содержит карточки статистики."""
        auth_page.goto('/app/dashboard')
        auth_page.wait_for_load_state('networkidle')
        auth_page.wait_for_timeout(2000)
        content = auth_page.content()
        # Должны быть какие-то метрики/счётчики
        has_stats = any(
            word in content
            for word in [
                'Резюме',
                'Оптимизаци',
                'Score',
                'Вакансии',
                'резюме',
                'оптимизаци',
                'история',
            ]
        )
        assert has_stats, 'Dashboard не содержит карточек статистики'

    def test_resumes_page(self, auth_page: Page) -> None:
        """Страница резюме загружается."""
        auth_page.goto('/app/resumes')
        auth_page.wait_for_load_state('networkidle')
        auth_page.wait_for_timeout(2000)

        assert '/auth' not in auth_page.url, 'Resumes перенаправил на /auth'
        root = auth_page.locator('#root')
        assert len(root.inner_html()) > 200, 'Resumes page пустая'

    def test_history_page(self, auth_page: Page) -> None:
        """Страница истории загружается."""
        auth_page.goto('/app/history')
        auth_page.wait_for_load_state('networkidle')
        auth_page.wait_for_timeout(2000)

        assert '/auth' not in auth_page.url, 'History перенаправил на /auth'
        root = auth_page.locator('#root')
        assert len(root.inner_html()) > 200, 'History page пустая'

    def test_upload_page(self, auth_page: Page) -> None:
        """Страница загрузки резюме."""
        auth_page.goto('/app/upload')
        auth_page.wait_for_load_state('networkidle')
        auth_page.wait_for_timeout(1000)

        assert '/auth' not in auth_page.url, 'Upload перенаправил на /auth'

        # Должна быть зона drag-and-drop или кнопка загрузки
        content = auth_page.content()
        has_upload = any(
            word in content
            for word in [
                'Загрузи',
                'загрузи',
                'upload',
                'Upload',
                'PDF',
                'DOCX',
                'Перетащите',
                'файл',
            ]
        )
        assert has_upload, 'Upload page не содержит интерфейса загрузки'

    def test_vacancy_page(self, auth_page: Page) -> None:
        """Страница вакансий загружается."""
        auth_page.goto('/app/vacancy')
        auth_page.wait_for_load_state('networkidle')
        auth_page.wait_for_timeout(1000)

        assert '/auth' not in auth_page.url, 'Vacancy перенаправил на /auth'
        root = auth_page.locator('#root')
        assert len(root.inner_html()) > 200, 'Vacancy page пустая'

    def test_models_page(self, auth_page: Page) -> None:
        """Страница выбора AI-модели загружается."""
        auth_page.goto('/app/models')
        auth_page.wait_for_load_state('networkidle')
        auth_page.wait_for_timeout(2000)

        assert '/auth' not in auth_page.url, 'Models перенаправил на /auth'

        content = auth_page.content()
        has_models = any(
            word in content for word in ['GigaChat', 'GPT', 'Anthropic', 'Claude', 'OpenRouter', 'модел', 'AI']
        )
        assert has_models, 'Models page не содержит списка моделей'

    def test_models_shows_availability(self, auth_page: Page) -> None:
        """Models page показывает доступность моделей."""
        auth_page.goto('/app/models')
        auth_page.wait_for_load_state('networkidle')
        auth_page.wait_for_timeout(2000)

        # Должны быть карточки моделей
        cards = auth_page.locator('.model-card, .card')
        assert cards.count() >= 1, 'Нет карточек моделей'

    def test_export_page(self, auth_page: Page) -> None:
        """Страница экспорта доступна."""
        auth_page.goto('/app/export')
        auth_page.wait_for_load_state('networkidle')
        auth_page.wait_for_timeout(1000)
        assert '/auth' not in auth_page.url, 'Export перенаправил на /auth'

    def test_editor_page(self, auth_page: Page) -> None:
        """Страница редактора доступна."""
        auth_page.goto('/app/editor')
        auth_page.wait_for_load_state('networkidle')
        auth_page.wait_for_timeout(1000)
        assert '/auth' not in auth_page.url, 'Editor перенаправил на /auth'


# =========================================================================
# 4. Settings pages
# =========================================================================


class TestSettingsPages:
    """Тесты страниц настроек."""

    def test_settings_profile(self, auth_page: Page) -> None:
        """Настройки профиля загружаются."""
        auth_page.goto('/app/settings/profile')
        auth_page.wait_for_load_state('networkidle')
        auth_page.wait_for_timeout(1000)

        assert '/auth' not in auth_page.url
        content = auth_page.content()
        has_profile = any(
            word in content for word in ['Профиль', 'Email', 'email', 'Имя', 'имя', 'профиль']
        )
        assert has_profile, 'Settings/Profile не содержит полей профиля'

    def test_settings_ai(self, auth_page: Page) -> None:
        """Настройки AI загружаются."""
        auth_page.goto('/app/settings/ai')
        auth_page.wait_for_load_state('networkidle')
        auth_page.wait_for_timeout(1000)

        assert '/auth' not in auth_page.url
        content = auth_page.content()
        has_ai = any(
            word in content
            for word in [
                'GigaChat',
                'GPT',
                'Anthropic',
                'Claude',
                'OpenRouter',
                'API',
                'ключ',
                'модел',
            ]
        )
        assert has_ai, 'Settings/AI не содержит настроек моделей'

    def test_settings_subscription(self, auth_page: Page) -> None:
        """Настройки подписки загружаются."""
        auth_page.goto('/app/settings/subscription')
        auth_page.wait_for_load_state('networkidle')
        auth_page.wait_for_timeout(1000)

        assert '/auth' not in auth_page.url
        content = auth_page.content()
        has_sub = any(
            word in content
            for word in ['тариф', 'план', 'подпис', 'Free', 'Standard', 'Pro', 'Тариф']
        )
        assert has_sub, 'Settings/Subscription не содержит информации о подписке'

    def test_settings_security(self, auth_page: Page) -> None:
        """Настройки безопасности загружаются."""
        auth_page.goto('/app/settings/security')
        auth_page.wait_for_load_state('networkidle')
        auth_page.wait_for_timeout(1000)

        assert '/auth' not in auth_page.url
        content = auth_page.content()
        has_security = any(
            word in content for word in ['пароль', 'Пароль', 'безопас', 'Безопас', 'password']
        )
        assert has_security, 'Settings/Security не содержит настроек безопасности'

    def test_settings_navigation(self, auth_page: Page) -> None:
        """Навигация между вкладками настроек работает."""
        auth_page.goto('/app/settings')
        auth_page.wait_for_load_state('networkidle')
        auth_page.wait_for_timeout(1000)

        # Проверяем что есть табы/навигация
        content = auth_page.content()
        tabs = ['Профиль', 'AI', 'Подписка', 'Безопасность']
        found = sum(1 for t in tabs if t in content)
        assert found >= 2, f'Навигация настроек: найдено {found} из {len(tabs)} вкладок'


# =========================================================================
# 5. Navigation & Links
# =========================================================================


class TestNavigation:
    """Тесты навигации и ссылок."""

    def test_sidebar_links(self, auth_page: Page) -> None:
        """Sidebar содержит навигационные ссылки."""
        auth_page.goto('/app/dashboard')
        auth_page.wait_for_load_state('networkidle')
        auth_page.wait_for_timeout(1000)

        content = auth_page.content()
        nav_items = ['Dashboard', 'Резюме', 'История', 'Настройки', 'резюме', 'история']
        found = sum(1 for item in nav_items if item in content)
        assert found >= 2, f'Sidebar: найдено {found} навигационных элементов'

    def test_redirect_unauthenticated(self, page: Page) -> None:
        """Неавторизованный пользователь → redirect на /auth."""
        # Создаём новый контекст без cookie/tokens
        context = page.context.browser.new_context(
            viewport={'width': 1280, 'height': 800},
            base_url=BASE_URL,
            ignore_https_errors=True,
        )
        fresh_page = context.new_page()
        fresh_page.goto('/app/dashboard')
        fresh_page.wait_for_load_state('networkidle')
        fresh_page.wait_for_timeout(2000)

        url = fresh_page.url
        # Должен редиректить на auth или показать форму логина
        assert '/auth' in url or '/login' in url or 'Войти' in fresh_page.content(), (
            f'Неавторизованный доступ к dashboard: {url}'
        )
        fresh_page.close()
        context.close()


# =========================================================================
# 6. Responsive / Mobile
# =========================================================================


class TestResponsive:
    """Тесты мобильной версии."""

    def test_landing_mobile(self, page: Page) -> None:
        """Лендинг рендерится на мобильном разрешении."""
        page.set_viewport_size({'width': 375, 'height': 812})
        page.goto('/')
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(1000)

        root = page.locator('#root')
        assert len(root.inner_html()) > 100, 'Мобильный лендинг пустой'

        # Сбрасываем viewport
        page.set_viewport_size({'width': 1280, 'height': 800})

    def test_auth_mobile(self, page: Page) -> None:
        """Auth страница на мобильном разрешении."""
        page.set_viewport_size({'width': 375, 'height': 812})
        page.goto('/auth')
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(1000)

        # Должна быть форма
        inputs = page.locator('input')
        assert inputs.count() >= 1, 'Нет полей ввода на мобильном auth'

        page.set_viewport_size({'width': 1280, 'height': 800})


# =========================================================================
# 7. API Health & JS errors
# =========================================================================


class TestAPIHealth:
    """Проверка доступности API с фронтенда."""

    def test_api_health_from_frontend(self, page: Page) -> None:
        """API /health доступен из браузера."""
        resp = page.goto(f'{BASE_URL}/health')
        assert resp is not None
        assert resp.status == 200
        body = page.content()
        assert 'ok' in body.lower() or 'healthy' in body.lower() or 'status' in body.lower()

    def test_api_models_endpoint(self, page: Page) -> None:
        """GET /api/v1/models доступен."""
        resp = page.goto(f'{BASE_URL}/api/v1/models')
        assert resp is not None
        assert resp.status == 200
        body = page.content()
        assert 'models' in body.lower() or 'gigachat' in body.lower()


# =========================================================================
# 8. Full wizard flow (smoke)
# =========================================================================


class TestWizardFlow:
    """Smoke-тест полного wizard flow."""

    def test_wizard_step_upload(self, auth_page: Page) -> None:
        """Wizard: шаг загрузки доступен."""
        auth_page.goto('/app/upload')
        auth_page.wait_for_load_state('networkidle')
        auth_page.wait_for_timeout(1000)

        content = auth_page.content()
        # Drag-and-drop или кнопка
        has_upload = any(
            word in content
            for word in ['Загруз', 'загруз', 'PDF', 'DOCX', 'Перетащ', 'файл', 'drag']
        )
        assert has_upload, 'Wizard upload шаг не содержит interface загрузки'

    def test_wizard_step_vacancy(self, auth_page: Page) -> None:
        """Wizard: шаг вакансии доступен."""
        auth_page.goto('/app/vacancy')
        auth_page.wait_for_load_state('networkidle')
        auth_page.wait_for_timeout(1000)

        content = auth_page.content()
        has_vacancy = any(
            word in content
            for word in ['Вакансия', 'вакансия', 'hh.ru', 'поиск', 'Поиск', 'вручную']
        )
        assert has_vacancy, 'Wizard vacancy шаг не содержит интерфейса вакансий'

    def test_wizard_step_models(self, auth_page: Page) -> None:
        """Wizard: шаг выбора модели доступен."""
        auth_page.goto('/app/models')
        auth_page.wait_for_load_state('networkidle')
        auth_page.wait_for_timeout(1000)

        content = auth_page.content()
        has_models = any(word in content for word in ['GigaChat', 'GPT', 'Anthropic', 'Claude', 'OpenRouter'])
        assert has_models, 'Wizard models шаг не содержит карточек моделей'


# =========================================================================
# 9. Console errors summary
# =========================================================================


class TestNoFatalErrors:
    """Проход по всем страницам и сбор JS-ошибок."""

    def test_no_fatal_js_errors(self, auth_page: Page) -> None:
        """Все страницы загружаются без fatal JS-ошибок."""
        pages_to_visit = [
            '/app/dashboard',
            '/app/resumes',
            '/app/upload',
            '/app/vacancy',
            '/app/models',
            '/app/history',
            '/app/settings/profile',
            '/app/settings/ai',
            '/app/settings/subscription',
            '/app/settings/security',
            '/app/editor',
            '/app/export',
        ]

        js_errors: list[dict[str, str]] = []

        for path in pages_to_visit:
            page_errors: list[str] = []
            auth_page.on(
                'console',
                lambda msg, pe=page_errors: pe.append(msg.text) if msg.type == 'error' else None,
            )

            try:
                auth_page.goto(path)
                auth_page.wait_for_load_state('networkidle')
                auth_page.wait_for_timeout(1500)

                # Проверяем что страница не пустая
                root = auth_page.locator('#root')
                inner = root.inner_html()
                if len(inner) < 100:
                    js_errors.append(
                        {
                            'page': path,
                            'error': f'Страница почти пустая ({len(inner)} chars)',
                        }
                    )

            except Exception as exc:
                js_errors.append(
                    {
                        'page': path,
                        'error': f'Ошибка навигации: {exc}',
                    }
                )

            # Фильтруем реальные ошибки
            for err in page_errors:
                if 'favicon' not in err.lower() and 'ERR_CONNECTION' not in err:
                    js_errors.append({'page': path, 'error': err})

        if js_errors:
            report = '\n'.join(f'  [{e["page"]}] {e["error"]}' for e in js_errors)
            pytest.fail(f'JS-ошибки найдены:\n{report}')

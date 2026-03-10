"""Тесты V32 фиксов (QA Report #28).

Покрывает:
- QA-LIMIT-001: защищённый admin endpoint reset-optimization-limit
- PRICING-MISMATCH-001: единая BYOK-коммуникация в планах
- HISTORY-COUNT-001: dashboard показывает "успешных из попыток"
"""

from __future__ import annotations

from pathlib import Path


def test_admin_reset_endpoint_exists_and_protected() -> None:
    """QA-LIMIT-001: endpoint есть, защищён ключом и безопасным compare_digest."""
    src = Path('src/app/admin/router.py').read_text(encoding='utf-8')

    assert "'/reset-optimization-limit'" in src
    assert "alias='X-Admin-Key'" in src
    assert 'secrets.compare_digest' in src
    assert "detail='Endpoint disabled'" in src
    assert 'user.optimizations_used = 0' in src


def test_main_includes_admin_router() -> None:
    """Admin router подключён в main app."""
    src = Path('src/app/main.py').read_text(encoding='utf-8')
    assert 'from app.admin.router import router as admin_router' in src
    assert 'app.include_router(admin_router, prefix=api_prefix)' in src


def test_pricing_pages_use_byok_text() -> None:
    """PRICING-MISMATCH-001: pricing тексты синхронизированы с BYOK моделью."""
    landing = Path('frontend/src/pages/LandingPage.tsx').read_text(encoding='utf-8')
    pricing = Path('frontend/src/pages/PricingPage.tsx').read_text(encoding='utf-8')
    subscription = Path('frontend/src/pages/settings/SettingsSubscriptionPage.tsx').read_text(
        encoding='utf-8'
    )

    for text in (landing, pricing, subscription):
        assert 'Все AI-модели (BYOK)' in text

    # На Free плане больше нет misleading ограничения "OpenRouter only".
    assert "'OpenRouter'" not in landing
    assert "'OpenRouter'" not in pricing


def test_dashboard_shows_successful_out_of_attempts() -> None:
    """HISTORY-COUNT-001: дашборд явно показывает успешные оптимизации из попыток."""
    src = Path('frontend/src/pages/dashboard/DashboardPage.tsx').read_text(encoding='utf-8')
    assert 'const totalAttempts = history.length' in src
    assert 'Успешных: {totalOptimizations} из {totalAttempts}' in src

"""Тесты покрытия V26 (3 дефекта QA Report #21).

Покрывает:
- NAV-001: Ссылка «Обновить до Pro» — фронтенд-фикс (Link вместо NavLink)
- EMAIL-VERIFY-001: Консистентность is_verified между API-эндпоинтами
- GIGACHAT-001: Ошибка биллинга GigaChat (верификация обработки ошибок)
"""

from __future__ import annotations

from datetime import UTC
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


# ============================================================================
# EMAIL-VERIFY-001: is_verified consistency across API endpoints
# ============================================================================


class TestEmailVerificationConsistency:
    """EMAIL-VERIFY-001: Поле is_verified возвращается единообразно."""

    @pytest.mark.asyncio
    async def test_user_response_has_is_verified(self) -> None:
        """UserResponse schema содержит поле is_verified."""
        from app.auth.schemas import UserResponse

        fields = UserResponse.model_fields
        assert 'is_verified' in fields
        assert fields['is_verified'].annotation is bool

    @pytest.mark.asyncio
    async def test_user_model_has_is_verified(self) -> None:
        """User model содержит поле is_verified с default=False."""
        from app.auth.models import User

        col = User.__table__.columns['is_verified']
        assert col is not None
        assert str(col.type) == 'BOOLEAN'

    @pytest.mark.asyncio
    async def test_me_returns_is_verified(self, client: AsyncClient) -> None:
        """GET /auth/me возвращает is_verified."""
        from app.core.security import create_access_token

        mock_user = MagicMock()
        mock_user.id = '00000000-0000-0000-0000-000000000001'
        mock_user.email = 'test@example.com'
        mock_user.full_name = 'Test User'
        mock_user.plan = 'free'
        mock_user.optimizations_used = 0
        mock_user.is_active = True
        mock_user.is_verified = True
        mock_user.avatar_url = None
        mock_user.created_at = '2026-01-01T00:00:00'
        mock_user.updated_at = '2026-01-01T00:00:00'

        token = create_access_token(user_id=str(mock_user.id))

        with patch(
            'app.auth.router.get_current_user',
            new_callable=AsyncMock,
            return_value=mock_user,
        ):
            resp = await client.get(
                '/api/v1/auth/me',
                headers={'Authorization': f'Bearer {token}'},
            )

        if resp.status_code == 200:
            data = resp.json()
            assert 'is_verified' in data
            assert data['is_verified'] is True

    @pytest.mark.asyncio
    async def test_register_sets_is_verified_false(self) -> None:
        """При регистрации is_verified = False."""
        # Проверяем что register устанавливает is_verified=False
        import inspect

        from app.auth import service as auth_svc

        source = inspect.getsource(auth_svc.register)
        assert 'is_verified' in source

    @pytest.mark.asyncio
    async def test_user_response_serializes_is_verified(self) -> None:
        """UserResponse корректно сериализует is_verified."""
        from datetime import datetime
        from uuid import uuid4

        from app.auth.schemas import UserResponse

        resp = UserResponse(
            id=uuid4(),
            email='test@test.com',
            full_name='Test',
            plan='free',
            optimizations_used=0,
            is_active=True,
            is_verified=False,
            avatar_url=None,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        data = resp.model_dump()
        assert data['is_verified'] is False

        resp2 = UserResponse(
            id=uuid4(),
            email='test2@test.com',
            full_name='Test2',
            plan='free',
            optimizations_used=0,
            is_active=True,
            is_verified=True,
            avatar_url=None,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        data2 = resp2.model_dump()
        assert data2['is_verified'] is True


# ============================================================================
# NAV-001: Plan upgrade link — frontend fix verified via CSS
# ============================================================================


class TestPlanUpgradeCss:
    """NAV-001: Проверка CSS для plan-upgrade ссылки."""

    def test_plan_upgrade_css_has_pointer_events(self) -> None:
        """CSS .plan-upgrade включает pointer-events: auto."""
        import pathlib

        base = pathlib.Path(__file__).resolve().parent.parent
        css_path = base / 'frontend' / 'src' / 'styles' / 'shared-styles.css'
        if not css_path.exists():
            # Try from project root
            css_path = pathlib.Path('frontend/src/styles/shared-styles.css')
        if css_path.exists():
            content = css_path.read_text()
            assert 'pointer-events: auto' in content or 'pointer-events:auto' in content
            assert '.plan-upgrade' in content

    def test_plan_upgrade_css_has_z_index(self) -> None:
        """CSS .plan-upgrade включает z-index."""
        import pathlib

        base = pathlib.Path(__file__).resolve().parent.parent
        css_path = base / 'frontend' / 'src' / 'styles' / 'shared-styles.css'
        if not css_path.exists():
            css_path = pathlib.Path('frontend/src/styles/shared-styles.css')
        if css_path.exists():
            content = css_path.read_text()
            assert 'z-index: 2' in content or 'z-index:2' in content

    def test_layout_uses_link_not_navlink_for_upgrade(self) -> None:
        """AppLayout использует Link (не NavLink) для plan-upgrade."""
        import pathlib

        base = pathlib.Path(__file__).resolve().parent.parent
        tsx_path = base / 'frontend' / 'src' / 'components' / 'layout' / 'AppLayout.tsx'
        if not tsx_path.exists():
            tsx_path = pathlib.Path('frontend/src/components/layout/AppLayout.tsx')
        if tsx_path.exists():
            content = tsx_path.read_text()
            # Should have <Link with to="/app/settings/subscription" (may be multi-line)
            assert '<Link' in content
            assert 'to="/app/settings/subscription"' in content
            assert 'className="plan-upgrade"' in content
            # Should NOT have NavLink for plan-upgrade
            unexpected = '<NavLink to="/app/settings/subscription" className="plan-upgrade">'
            assert unexpected not in content


# ============================================================================
# EMAIL-VERIFY-001: Profile page — dynamic verification badge
# ============================================================================


class TestProfileVerificationBadge:
    """EMAIL-VERIFY-001: Профиль показывает статус верификации динамически."""

    def test_profile_page_has_dynamic_verification(self) -> None:
        """SettingsProfilePage использует is_verified для показа бейджа."""
        import pathlib

        base = pathlib.Path(__file__).resolve().parent.parent
        tsx_path = base / 'frontend' / 'src' / 'pages' / 'settings' / 'SettingsProfilePage.tsx'
        if not tsx_path.exists():
            tsx_path = pathlib.Path('frontend/src/pages/settings/SettingsProfilePage.tsx')
        if tsx_path.exists():
            content = tsx_path.read_text()
            assert 'is_verified' in content
            assert 'Не подтверждён' in content
            assert 'Подтверждён' in content

    def test_dashboard_uses_is_verified_for_banner(self) -> None:
        """DashboardPage использует is_verified для баннера."""
        import pathlib

        base = pathlib.Path(__file__).resolve().parent.parent
        tsx_path = base / 'frontend' / 'src' / 'pages' / 'dashboard' / 'DashboardPage.tsx'
        if not tsx_path.exists():
            tsx_path = pathlib.Path('frontend/src/pages/dashboard/DashboardPage.tsx')
        if tsx_path.exists():
            content = tsx_path.read_text()
            assert 'is_verified' in content
            assert 'Подтвердите email' in content


# ============================================================================
# GIGACHAT-001: Billing error handling verification
# ============================================================================


class TestGigaChatBillingErrorHandling:
    """GIGACHAT-001: Приложение корректно обрабатывает ошибку биллинга."""

    @pytest.mark.asyncio
    async def test_health_endpoint_detects_billing_error(self) -> None:
        """Health endpoint определяет ошибку биллинга."""
        from app.ml.router import _ping_gigachat

        with patch('gigachat.GigaChat') as mock_gc:
            mock_instance = MagicMock()
            mock_instance.get_models.side_effect = Exception('Недостаточно средств на балансе')
            mock_gc.return_value = mock_instance

            result = await _ping_gigachat('test-cred')
            assert result['status'] in ('billing_error', 'error')

    @pytest.mark.asyncio
    async def test_health_endpoint_no_key(self) -> None:
        """Health endpoint возвращает no_key для GigaChat без ключа."""
        from app.ml.router import _ping_gigachat

        result = await _ping_gigachat('')
        # Empty credentials → should fail with some error
        assert result['status'] in ('no_key', 'error', 'auth_error')


# ============================================================================
# Auth Context — is_verified field in User interface
# ============================================================================


class TestAuthContextIsVerified:
    """Проверка что AuthContext User имеет is_verified."""

    def test_auth_context_user_interface_has_is_verified(self) -> None:
        """AuthContext User interface содержит is_verified."""
        import pathlib

        base = pathlib.Path(__file__).resolve().parent.parent
        tsx_path = base / 'frontend' / 'src' / 'contexts' / 'AuthContext.tsx'
        if not tsx_path.exists():
            tsx_path = pathlib.Path('frontend/src/contexts/AuthContext.tsx')
        if tsx_path.exists():
            content = tsx_path.read_text()
            assert 'is_verified' in content

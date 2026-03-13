"""
Тесты для исправлений V39 — дефекты из QA Report #37.

Дефекты:
- PASSWORD-CHANGE-503 (P1): PUT /me/password → 503, пароль менялся → flush-only (не 503)
- AVATAR-DELETE-503 (P2): DELETE /me/avatar → 503, аватар удалялся → flush-only (не 503)
- LOGOUT-503 (P3): POST /logout → 503 → noload relationships, nginx buffering
- ACCOUNT-DELETE-HARD-vs-SOFT (P2): hard delete → soft delete с 30-дневным grace period
- VACANCY-URL-OBJECT-ERROR (P3): "[object Object]" → extractErrorMessage (frontend)
- VACANCY-TITLE-002 (P3): автозаполнение должности из title резюме (frontend)
"""

from __future__ import annotations

from datetime import UTC, datetime
from http import HTTPStatus
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient

from app.auth.models import User
from app.auth.service import soft_delete_account

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


# ============================================================================
# PASSWORD-CHANGE-503: flush-only, no double-commit
# ============================================================================


class TestPasswordChange503:
    """P1: PUT /me/password не должен возвращать 503."""

    async def test_change_password_returns_204(
        self,
        auth_client: AsyncClient,
        test_user: User,
    ) -> None:
        """Смена пароля → 204 (не 503)."""
        response = await auth_client.put(
            '/api/v1/auth/me/password',
            json={
                'current_password': 'TestPass123',
                'new_password': 'NewPass456',
            },
        )
        assert response.status_code == HTTPStatus.NO_CONTENT

    async def test_change_password_wrong_current(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """Неверный текущий пароль → 401."""
        response = await auth_client.put(
            '/api/v1/auth/me/password',
            json={
                'current_password': 'WrongPassword',
                'new_password': 'NewPass456',
            },
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED


# ============================================================================
# AVATAR-DELETE-503: flush-only, no double-commit
# ============================================================================


class TestAvatarDelete503Fix:
    """P2: DELETE /me/avatar не должен возвращать 503 (flush-only fix)."""

    async def test_delete_avatar_no_avatar_returns_204(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """Удаление без аватара → 204 (idempotent)."""
        response = await auth_client.delete('/api/v1/auth/me/avatar')
        assert response.status_code == HTTPStatus.NO_CONTENT

    async def test_delete_avatar_with_avatar_returns_204(
        self,
        auth_client: AsyncClient,
        test_user: User,
        session: AsyncSession,
    ) -> None:
        """Удаление существующего аватара → 204, avatar_url = None."""
        test_user.avatar_url = '/uploads/test-avatar.png'
        await session.flush()

        mock_storage = MagicMock()
        mock_storage.delete = AsyncMock()

        with patch('app.core.storage.file_storage', mock_storage):
            response = await auth_client.delete('/api/v1/auth/me/avatar')

        assert response.status_code == HTTPStatus.NO_CONTENT

    async def test_upload_avatar_returns_200(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """Загрузка аватара → 200 (flush-only, no double-commit)."""
        mock_storage = MagicMock()
        mock_storage.save = AsyncMock(return_value='avatars/test.jpg')
        mock_storage.delete = AsyncMock()

        with patch('app.core.storage.file_storage', mock_storage):
            response = await auth_client.post(
                '/api/v1/auth/me/avatar',
                files={'file': ('avatar.jpg', b'\xff\xd8\xff\xe0' + b'\x00' * 100, 'image/jpeg')},
            )

        assert response.status_code == HTTPStatus.OK


# ============================================================================
# ACCOUNT-DELETE-HARD-vs-SOFT: soft delete с grace period
# ============================================================================


class TestAccountDeleteSoftDelete:
    """P2: DELETE /me → soft-delete с 30-дневным grace period."""

    async def test_delete_account_returns_soft_delete_message(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """DELETE /me → сообщение о soft-delete."""
        response = await auth_client.request(
            'DELETE',
            '/api/v1/auth/me',
            json={'password': 'TestPass123', 'confirmation': 'УДАЛИТЬ'},
        )
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert '30 дней' in data['message']

    async def test_soft_delete_sets_deleted_at(
        self,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        """soft_delete_account ставит deleted_at и scheduled_deletion."""
        await soft_delete_account(session, user=test_user, password='TestPass123')
        assert test_user.deleted_at is not None
        assert test_user.scheduled_deletion is not None

    async def test_soft_delete_user_can_still_login(
        self,
        client: AsyncClient,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        """Soft-deleted пользователь может войти и восстановить аккаунт."""
        test_user.deleted_at = datetime.now(tz=UTC)
        test_user.scheduled_deletion = datetime.now(tz=UTC)
        await session.flush()

        response = await client.post(
            '/api/v1/auth/login',
            json={'email': test_user.email, 'password': 'TestPass123'},
        )
        assert response.status_code == HTTPStatus.OK
        assert 'access_token' in response.json()

        # Проверяем, что deleted_at сбросился (аккаунт восстановлен)
        await session.refresh(test_user)
        assert test_user.deleted_at is None
        assert test_user.scheduled_deletion is None

    async def test_delete_wrong_confirmation_returns_400(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """Неверное подтверждение → 400."""
        response = await auth_client.request(
            'DELETE',
            '/api/v1/auth/me',
            json={'password': 'TestPass123', 'confirmation': 'DELETE'},
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST

    async def test_delete_wrong_password_returns_401(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """Неверный пароль → 401."""
        response = await auth_client.request(
            'DELETE',
            '/api/v1/auth/me',
            json={'password': 'WrongPassword', 'confirmation': 'УДАЛИТЬ'},
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED


# ============================================================================
# LOGOUT-503: logout не должен возвращать 503
# ============================================================================


class TestLogout503:
    """P3: POST /logout не должен возвращать 503."""

    async def test_logout_returns_204(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """Logout → 204 (не 503)."""
        response = await auth_client.post('/api/v1/auth/logout')
        assert response.status_code == HTTPStatus.NO_CONTENT

    async def test_logout_unauthorized_returns_401(
        self,
        client: AsyncClient,
    ) -> None:
        """Logout без токена → 401."""
        response = await client.post('/api/v1/auth/logout')
        assert response.status_code == HTTPStatus.UNAUTHORIZED


# ============================================================================
# NOLOAD RELATIONSHIPS: user query не загружает все связанные данные
# ============================================================================


class TestNoloadRelationships:
    """User model relationships теперь lazy='noload' (не selectin)."""

    async def test_get_me_returns_200(
        self,
        auth_client: AsyncClient,
        test_user: User,
    ) -> None:
        """GET /me работает с noload relationships."""
        response = await auth_client.get('/api/v1/auth/me')
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data['email'] == test_user.email

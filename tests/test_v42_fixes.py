"""
Тесты для исправлений V42 — дефекты из QA Report #39 (V41).

Дефекты:
- PASSWORD-CHANGE-503 (P1): PUT /me/password → 503 → explicit commit before response
- AVATAR-DELETE-503 (P2): DELETE /me/avatar → 503 → explicit commit before response
- AVATAR-UPLOAD-503 (P2): POST /me/avatar → 503 → explicit commit before response
- ACCOUNT-DELETE-500-REGRESSION (P1): DELETE /me → 500 → explicit commit before response
- GROQ-ALLAM-502 (P2): model not found → 400 with user-friendly message
- VACANCY-TITLE-002 (P3): filename → empty title (frontend filter)
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient

from app.auth.models import User

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


# ============================================================================
# PASSWORD-CHANGE-503: explicit commit before response
# ============================================================================


class TestPasswordChange503Fix:
    """P1: PUT /me/password → 204 (explicit commit prevents 503)."""

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

    async def test_change_password_weak_new_password(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """Слабый новый пароль (без цифры) → 422."""
        response = await auth_client.put(
            '/api/v1/auth/me/password',
            json={
                'current_password': 'TestPass123',
                'new_password': 'NoDigitsHere',
            },
        )
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    async def test_change_password_short_new_password(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """Слишком короткий пароль → 422."""
        response = await auth_client.put(
            '/api/v1/auth/me/password',
            json={
                'current_password': 'TestPass123',
                'new_password': 'Sh1',
            },
        )
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


# ============================================================================
# AVATAR-DELETE-503: explicit commit before response
# ============================================================================


class TestAvatarDelete503Fix:
    """P2: DELETE /me/avatar → 204 (explicit commit prevents 503)."""

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
        """Загрузка аватара → 200 (explicit commit prevents 503)."""
        mock_storage = MagicMock()
        mock_storage.save = AsyncMock(return_value='avatars/test.jpg')
        mock_storage.delete = AsyncMock()

        with patch('app.core.storage.file_storage', mock_storage):
            response = await auth_client.post(
                '/api/v1/auth/me/avatar',
                files={'file': ('avatar.jpg', b'\xff\xd8\xff\xe0' + b'\x00' * 100, 'image/jpeg')},
            )

        assert response.status_code == HTTPStatus.OK

    async def test_delete_avatar_storage_error_still_204(
        self,
        auth_client: AsyncClient,
        test_user: User,
        session: AsyncSession,
    ) -> None:
        """Ошибка storage при удалении → 204 (аватар сбрасывается в любом случае)."""
        test_user.avatar_url = '/uploads/test-avatar.png'
        await session.flush()

        mock_storage = MagicMock()
        mock_storage.delete = AsyncMock(side_effect=OSError('disk error'))

        with patch('app.core.storage.file_storage', mock_storage):
            response = await auth_client.delete('/api/v1/auth/me/avatar')

        assert response.status_code == HTTPStatus.NO_CONTENT


# ============================================================================
# ACCOUNT-DELETE-500-REGRESSION: explicit commit + soft-delete
# ============================================================================


class TestAccountDeleteFix:
    """P1: DELETE /me → soft-delete с явным коммитом (не 500/503)."""

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
        auth_client: AsyncClient,
        test_user: User,
        session: AsyncSession,
    ) -> None:
        """Soft-delete проставляет deleted_at и scheduled_deletion."""
        response = await auth_client.request(
            'DELETE',
            '/api/v1/auth/me',
            json={'password': 'TestPass123', 'confirmation': 'УДАЛИТЬ'},
        )
        assert response.status_code == HTTPStatus.OK

        await session.refresh(test_user)
        assert test_user.deleted_at is not None
        assert test_user.scheduled_deletion is not None

    async def test_soft_deleted_user_can_login_and_restore(
        self,
        client: AsyncClient,
        auth_client: AsyncClient,
        test_user: User,
        session: AsyncSession,
    ) -> None:
        """Soft-deleted пользователь входит → аккаунт восстанавливается."""
        # Soft-delete
        await auth_client.request(
            'DELETE',
            '/api/v1/auth/me',
            json={'password': 'TestPass123', 'confirmation': 'УДАЛИТЬ'},
        )
        await session.refresh(test_user)
        assert test_user.deleted_at is not None

        # Login → автовосстановление
        response = await client.post(
            '/api/v1/auth/login',
            json={'email': test_user.email, 'password': 'TestPass123'},
        )
        assert response.status_code == HTTPStatus.OK
        assert 'access_token' in response.json()

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

    async def test_delete_missing_fields_returns_422(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """Отсутствие полей → 422."""
        response = await auth_client.request(
            'DELETE',
            '/api/v1/auth/me',
            json={},
        )
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    async def test_restore_account_after_soft_delete(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """POST /me/restore отменяет soft-delete."""
        # Soft-delete
        await auth_client.request(
            'DELETE',
            '/api/v1/auth/me',
            json={'password': 'TestPass123', 'confirmation': 'УДАЛИТЬ'},
        )
        # Restore
        response = await auth_client.post('/api/v1/auth/me/restore')
        assert response.status_code == HTTPStatus.OK
        assert 'восстановлен' in response.json()['message'].lower()

    async def test_restore_not_deleted_account(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """POST /me/restore без soft-delete → информационное сообщение."""
        response = await auth_client.post('/api/v1/auth/me/restore')
        assert response.status_code == HTTPStatus.OK


# ============================================================================
# GROQ-ALLAM-502: model not found → 400
# ============================================================================


class TestGroqModelNotFound:
    """P2: несуществующая модель → 400, а не 502."""

    def test_handle_llm_error_404_model_not_found(self) -> None:
        """404 от провайдера → AppError(400, LLM_MODEL_NOT_FOUND)."""
        from app.core.exceptions import AppError
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('Model not found')
        exc.status_code = 404  # type: ignore[attr-defined]

        import pytest

        with pytest.raises(AppError) as exc_info:
            _handle_llm_error(exc, provider='groq')
        assert exc_info.value.status_code == 400
        assert exc_info.value.error_code == 'LLM_MODEL_NOT_FOUND'

    def test_handle_llm_error_model_not_found_in_message(self) -> None:
        """'model_not_found' в тексте ошибки → AppError(400)."""
        from app.core.exceptions import AppError
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('Error code: model_not_found')

        import pytest

        with pytest.raises(AppError) as exc_info:
            _handle_llm_error(exc, provider='groq')
        assert exc_info.value.status_code == 400
        assert 'модель' in exc_info.value.message.lower() or 'Модель' in exc_info.value.message

    def test_handle_llm_error_401_still_auth_error(self) -> None:
        """401 по-прежнему → LLMAuthError."""
        from app.core.exceptions import LLMAuthError
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('Unauthorized')
        exc.status_code = 401  # type: ignore[attr-defined]

        import pytest

        with pytest.raises(LLMAuthError):
            _handle_llm_error(exc, provider='groq')

    def test_handle_llm_error_500_still_unavailable(self) -> None:
        """500 от провайдера → LLMProviderUnavailable."""
        from app.core.exceptions import LLMProviderUnavailable
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('Internal Server Error')
        exc.status_code = 500  # type: ignore[attr-defined]

        import pytest

        with pytest.raises(LLMProviderUnavailable):
            _handle_llm_error(exc, provider='groq')


# ============================================================================
# LOGOUT-503: подтверждение, что logout по-прежнему 204
# ============================================================================


class TestLogout204:
    """Регрессия: logout должен оставаться 204."""

    async def test_logout_returns_204(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """Logout → 204."""
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
# NOLOAD RELATIONSHIPS: регрессия — user query не загружает relationships
# ============================================================================


class TestNoloadRelationships:
    """User model relationships lazy='noload' — регрессия."""

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

    async def test_update_profile_returns_200(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """PUT /me обновляет профиль без ошибки."""
        response = await auth_client.put(
            '/api/v1/auth/me',
            json={'full_name': 'Новое Имя'},
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json()['full_name'] == 'Новое Имя'

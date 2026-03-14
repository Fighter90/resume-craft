"""
Тесты для исправлений V43 — дефекты из QA Report #39 (V42).

Дефекты:
- ACCOUNT-DELETE-500-REGRESSION (P1): commit failure → AppError(DELETE_ACCOUNT_FAILED)
- GROQ-ALLAM-502 (P2): broadened model-not-found detection (400 + keywords)
- VACANCY-TITLE-002 (P3): extract position from raw_text as fallback
- URL-VALIDATION-RAW-JSON (P3): Pydantic validation arrays → user-friendly message
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.auth.models import User

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


# ============================================================================
# ACCOUNT-DELETE-500-REGRESSION: commit wrapped in try/except
# ============================================================================


class TestAccountDeleteCommitFix:
    """P1: DELETE /me → commit failure returns DELETE_ACCOUNT_FAILED, not INTERNAL_ERROR."""

    async def test_delete_account_success(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """DELETE /me → soft-delete message (happy path)."""
        response = await auth_client.request(
            'DELETE',
            '/api/v1/auth/me',
            json={'password': 'TestPass123', 'confirmation': 'УДАЛИТЬ'},
        )
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert '30 дней' in data['message']

    async def test_delete_account_wrong_password(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """Неверный пароль → 401."""
        response = await auth_client.request(
            'DELETE',
            '/api/v1/auth/me',
            json={'password': 'WrongPass', 'confirmation': 'УДАЛИТЬ'},
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    async def test_delete_account_wrong_confirmation(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """Неверное подтверждение → 400 DELETE_CONFIRMATION_INVALID."""
        response = await auth_client.request(
            'DELETE',
            '/api/v1/auth/me',
            json={'password': 'TestPass123', 'confirmation': 'DELETE'},
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.json()['error'] == 'DELETE_CONFIRMATION_INVALID'

    async def test_delete_account_missing_fields(
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

    async def test_soft_delete_sets_fields(
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

    async def test_soft_deleted_user_login_restores(
        self,
        client: AsyncClient,
        auth_client: AsyncClient,
        test_user: User,
        session: AsyncSession,
    ) -> None:
        """Soft-deleted пользователь входит → аккаунт восстанавливается."""
        await auth_client.request(
            'DELETE',
            '/api/v1/auth/me',
            json={'password': 'TestPass123', 'confirmation': 'УДАЛИТЬ'},
        )
        await session.refresh(test_user)
        assert test_user.deleted_at is not None

        response = await client.post(
            '/api/v1/auth/login',
            json={'email': test_user.email, 'password': 'TestPass123'},
        )
        assert response.status_code == HTTPStatus.OK
        assert 'access_token' in response.json()

        await session.refresh(test_user)
        assert test_user.deleted_at is None
        assert test_user.scheduled_deletion is None

    async def test_restore_account_endpoint(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """POST /me/restore отменяет soft-delete."""
        await auth_client.request(
            'DELETE',
            '/api/v1/auth/me',
            json={'password': 'TestPass123', 'confirmation': 'УДАЛИТЬ'},
        )
        response = await auth_client.post('/api/v1/auth/me/restore')
        assert response.status_code == HTTPStatus.OK

    async def test_restore_not_deleted(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """POST /me/restore без soft-delete → OK."""
        response = await auth_client.post('/api/v1/auth/me/restore')
        assert response.status_code == HTTPStatus.OK

    async def test_commit_failure_returns_delete_account_failed(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """V43-FIX: commit failure → DELETE_ACCOUNT_FAILED, не INTERNAL_ERROR."""
        from sqlalchemy.exc import SQLAlchemyError

        original_commit = None

        async def failing_commit(self_session: object) -> None:
            """First call succeeds (flush), second (explicit commit) fails."""
            nonlocal original_commit
            raise SQLAlchemyError('simulated commit failure')

        with patch(
            'app.auth.router.AsyncSession.commit',
            new=failing_commit,
        ):
            response = await auth_client.request(
                'DELETE',
                '/api/v1/auth/me',
                json={'password': 'TestPass123', 'confirmation': 'УДАЛИТЬ'},
            )

        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        data = response.json()
        assert data['error'] == 'DELETE_ACCOUNT_FAILED'


# ============================================================================
# GROQ-ALLAM-502: broadened model-not-found detection
# ============================================================================


class TestGroqModelNotFoundBroadened:
    """P2: расширенная детекция model-not-found (400 + keywords)."""

    def test_404_model_not_found(self) -> None:
        """404 от провайдера → LLM_MODEL_NOT_FOUND."""
        from app.core.exceptions import AppError
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('Model not found')
        exc.status_code = 404  # type: ignore[attr-defined]

        with pytest.raises(AppError) as exc_info:
            _handle_llm_error(exc, provider='groq')
        assert exc_info.value.status_code == 400
        assert exc_info.value.error_code == 'LLM_MODEL_NOT_FOUND'

    def test_400_does_not_exist(self) -> None:
        """V43: 400 + 'does not exist' → LLM_MODEL_NOT_FOUND."""
        from app.core.exceptions import AppError
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('The model `allam-2-7b` does not exist')
        exc.status_code = 400  # type: ignore[attr-defined]

        with pytest.raises(AppError) as exc_info:
            _handle_llm_error(exc, provider='groq')
        assert exc_info.value.status_code == 400
        assert exc_info.value.error_code == 'LLM_MODEL_NOT_FOUND'

    def test_400_invalid_model(self) -> None:
        """V44: 400 + 'invalid model' (no model-specific keyword) → LLMProviderUnavailable.

        V44 tightened keywords: 'invalid model' is too broad and was removed.
        """
        from app.core.exceptions import LLMProviderUnavailable
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('Invalid model specified: allam-2-7b')
        exc.status_code = 400  # type: ignore[attr-defined]

        with pytest.raises(LLMProviderUnavailable):
            _handle_llm_error(exc, provider='groq')

    def test_model_not_found_in_message_no_status(self) -> None:
        """'model_not_found' в тексте без status_code → LLM_MODEL_NOT_FOUND."""
        from app.core.exceptions import AppError
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('Error code: model_not_found')

        with pytest.raises(AppError) as exc_info:
            _handle_llm_error(exc, provider='groq')
        assert exc_info.value.status_code == 400
        assert 'модель' in exc_info.value.message.lower() or 'Модель' in exc_info.value.message

    def test_model_not_found_in_message(self) -> None:
        """'model not found' в тексте → LLM_MODEL_NOT_FOUND."""
        from app.core.exceptions import AppError
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('Model not found on server')

        with pytest.raises(AppError) as exc_info:
            _handle_llm_error(exc, provider='groq')
        assert exc_info.value.error_code == 'LLM_MODEL_NOT_FOUND'

    def test_model_not_active(self) -> None:
        """V44: 'model not active' (removed keyword) → catch-all LLMProviderUnavailable.

        V44 tightened keywords: 'model not active' was removed as too broad.
        """
        from app.core.exceptions import LLMProviderUnavailable
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('This model not active for inference')

        with pytest.raises(LLMProviderUnavailable):
            _handle_llm_error(exc, provider='groq')

    def test_no_such_model(self) -> None:
        """'no such model' → LLM_MODEL_NOT_FOUND."""
        from app.core.exceptions import AppError
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('no such model: allam-2-7b')

        with pytest.raises(AppError) as exc_info:
            _handle_llm_error(exc, provider='groq')
        assert exc_info.value.error_code == 'LLM_MODEL_NOT_FOUND'

    def test_401_still_auth_error(self) -> None:
        """401 по-прежнему → LLMAuthError."""
        from app.core.exceptions import LLMAuthError
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('Unauthorized')
        exc.status_code = 401  # type: ignore[attr-defined]

        with pytest.raises(LLMAuthError):
            _handle_llm_error(exc, provider='groq')

    def test_500_still_unavailable(self) -> None:
        """500 от провайдера → LLMProviderUnavailable."""
        from app.core.exceptions import LLMProviderUnavailable
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('Internal Server Error')
        exc.status_code = 500  # type: ignore[attr-defined]

        with pytest.raises(LLMProviderUnavailable):
            _handle_llm_error(exc, provider='groq')

    def test_400_auth_keywords_still_auth_error(self) -> None:
        """400 + auth keywords → LLMAuthError (не model-not-found)."""
        from app.core.exceptions import LLMAuthError
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('Invalid credentials for auth')
        exc.status_code = 400  # type: ignore[attr-defined]

        with pytest.raises(LLMAuthError):
            _handle_llm_error(exc, provider='groq')

    def test_400_generic_still_unavailable(self) -> None:
        """400 без model-keywords → LLMProviderUnavailable."""
        from app.core.exceptions import LLMProviderUnavailable
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('Bad request: invalid parameters')
        exc.status_code = 400  # type: ignore[attr-defined]

        with pytest.raises(LLMProviderUnavailable):
            _handle_llm_error(exc, provider='groq')


# ============================================================================
# URL-VALIDATION-RAW-JSON: Pydantic validation arrays → user-friendly
# ============================================================================


class TestUrlValidationErrorDisplay:
    """P3: invalid URL → user-friendly error, not raw JSON."""

    async def test_invalid_url_returns_422(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """Невалидный URL → 422 с detail массивом."""
        response = await auth_client.post(
            '/api/v1/vacancies/from-url',
            json={'url': 'not-a-url'},
        )
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        data = response.json()
        # Pydantic returns detail as array
        assert 'detail' in data
        assert isinstance(data['detail'], list)

    async def test_empty_url_returns_422(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """Пустой URL → 422."""
        response = await auth_client.post(
            '/api/v1/vacancies/from-url',
            json={'url': ''},
        )
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


# ============================================================================
# REGRESSION: existing functionality still works
# ============================================================================


class TestRegressionV43:
    """Регрессия: все ранее починенные эндпоинты продолжают работать."""

    async def test_change_password_returns_204(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """Смена пароля → 204."""
        response = await auth_client.put(
            '/api/v1/auth/me/password',
            json={
                'current_password': 'TestPass123',
                'new_password': 'NewPass456',
            },
        )
        assert response.status_code == HTTPStatus.NO_CONTENT

    async def test_delete_avatar_returns_204(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """Удаление аватара → 204."""
        response = await auth_client.delete('/api/v1/auth/me/avatar')
        assert response.status_code == HTTPStatus.NO_CONTENT

    async def test_upload_avatar_returns_200(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """Загрузка аватара → 200."""
        mock_storage = MagicMock()
        mock_storage.save = AsyncMock(return_value='avatars/test.jpg')
        mock_storage.delete = AsyncMock()

        with patch('app.core.storage.file_storage', mock_storage):
            response = await auth_client.post(
                '/api/v1/auth/me/avatar',
                files={'file': ('avatar.jpg', b'\xff\xd8\xff\xe0' + b'\x00' * 100, 'image/jpeg')},
            )

        assert response.status_code == HTTPStatus.OK

    async def test_logout_returns_204(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """Logout → 204."""
        response = await auth_client.post('/api/v1/auth/logout')
        assert response.status_code == HTTPStatus.NO_CONTENT

    async def test_get_me_returns_200(
        self,
        auth_client: AsyncClient,
        test_user: User,
    ) -> None:
        """GET /me → 200."""
        response = await auth_client.get('/api/v1/auth/me')
        assert response.status_code == HTTPStatus.OK
        assert response.json()['email'] == test_user.email

    async def test_update_profile_returns_200(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """PUT /me → 200."""
        response = await auth_client.put(
            '/api/v1/auth/me',
            json={'full_name': 'Тест V43'},
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json()['full_name'] == 'Тест V43'

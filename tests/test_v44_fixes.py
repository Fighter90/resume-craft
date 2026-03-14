"""
Тесты для исправлений V44 — дефекты из QA Report #40 (V43).

Дефекты:
- OPENAI-MODEL-MAPPING (P1): frontend sent stale subModel across providers
- ANTHROPIC-MODEL-MAPPING (P1): same root cause as OPENAI-MODEL-MAPPING
- ACCOUNT-DELETE-500-REGRESSION (P1): broader try/except, logger moved to top
- GROQ-ALLAM-502 (P2): tightened model-not-found keywords (V44 refinement)
- HH-RESUME-LINK-400 (P2): Playwright-based hh.ru resume parser (optional)
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
# OPENAI-MODEL-MAPPING / ANTHROPIC-MODEL-MAPPING: model-not-found detection
# ============================================================================


class TestModelNotFoundV44:
    """V44: tightened model-not-found detection — specific keywords only."""

    def test_404_status_code(self) -> None:
        """404 от провайдера → LLM_MODEL_NOT_FOUND."""
        from app.core.exceptions import AppError
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('Not Found')
        exc.status_code = 404  # type: ignore[attr-defined]

        with pytest.raises(AppError) as exc_info:
            _handle_llm_error(exc, provider='openai')
        assert exc_info.value.error_code == 'LLM_MODEL_NOT_FOUND'

    def test_model_not_found_keyword(self) -> None:
        """'model not found' в тексте → LLM_MODEL_NOT_FOUND."""
        from app.core.exceptions import AppError
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('Error: model not found on server')

        with pytest.raises(AppError) as exc_info:
            _handle_llm_error(exc, provider='openai')
        assert exc_info.value.error_code == 'LLM_MODEL_NOT_FOUND'

    def test_model_not_found_underscore(self) -> None:
        """'model_not_found' в тексте → LLM_MODEL_NOT_FOUND."""
        from app.core.exceptions import AppError
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('Error code: model_not_found')

        with pytest.raises(AppError) as exc_info:
            _handle_llm_error(exc, provider='groq')
        assert exc_info.value.error_code == 'LLM_MODEL_NOT_FOUND'

    def test_does_not_exist_groq(self) -> None:
        """V44: 'does not exist' (Groq allam-2-7b) → LLM_MODEL_NOT_FOUND."""
        from app.core.exceptions import AppError
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('The model `allam-2-7b` does not exist')
        exc.status_code = 400  # type: ignore[attr-defined]

        with pytest.raises(AppError) as exc_info:
            _handle_llm_error(exc, provider='groq')
        assert exc_info.value.error_code == 'LLM_MODEL_NOT_FOUND'
        assert exc_info.value.status_code == 400

    def test_no_such_model(self) -> None:
        """'no such model' → LLM_MODEL_NOT_FOUND."""
        from app.core.exceptions import AppError
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('no such model: allam-2-7b')

        with pytest.raises(AppError) as exc_info:
            _handle_llm_error(exc, provider='groq')
        assert exc_info.value.error_code == 'LLM_MODEL_NOT_FOUND'

    def test_not_found_alone_is_not_model_error(self) -> None:
        """V44: bare 'not found' (without 'model') → NOT LLM_MODEL_NOT_FOUND.

        This was the V42 bug: 'not found' matched 'Endpoint not found' etc.
        V44 tightened to 'model not found'.
        """
        from app.core.exceptions import LLMProviderUnavailable
        from app.ml.llm_client import _handle_llm_error

        # 'Endpoint not found' should NOT trigger model-not-found
        exc = Exception('Endpoint not found')
        exc.status_code = 400  # type: ignore[attr-defined]

        with pytest.raises(LLMProviderUnavailable):
            _handle_llm_error(exc, provider='openai')

    def test_user_not_found_is_not_model_error(self) -> None:
        """V44: 'User not found' → NOT LLM_MODEL_NOT_FOUND."""
        from app.core.exceptions import LLMProviderUnavailable
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('User not found')
        exc.status_code = 400  # type: ignore[attr-defined]

        with pytest.raises(LLMProviderUnavailable):
            _handle_llm_error(exc, provider='anthropic')

    def test_401_still_auth_error(self) -> None:
        """401 по-прежнему → LLMAuthError."""
        from app.core.exceptions import LLMAuthError
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('Unauthorized')
        exc.status_code = 401  # type: ignore[attr-defined]

        with pytest.raises(LLMAuthError):
            _handle_llm_error(exc, provider='openai')

    def test_500_still_unavailable(self) -> None:
        """500 от провайдера → LLMProviderUnavailable."""
        from app.core.exceptions import LLMProviderUnavailable
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('Internal Server Error')
        exc.status_code = 500  # type: ignore[attr-defined]

        with pytest.raises(LLMProviderUnavailable):
            _handle_llm_error(exc, provider='openai')

    def test_400_auth_keywords_still_auth_error(self) -> None:
        """400 + auth keywords → LLMAuthError."""
        from app.core.exceptions import LLMAuthError
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('Invalid credentials for auth')
        exc.status_code = 400  # type: ignore[attr-defined]

        with pytest.raises(LLMAuthError):
            _handle_llm_error(exc, provider='openai')

    def test_400_generic_still_unavailable(self) -> None:
        """400 без model-keywords → LLMProviderUnavailable."""
        from app.core.exceptions import LLMProviderUnavailable
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('Bad request: invalid parameters')
        exc.status_code = 400  # type: ignore[attr-defined]

        with pytest.raises(LLMProviderUnavailable):
            _handle_llm_error(exc, provider='openai')

    def test_429_rate_limit(self) -> None:
        """429 → LLMProviderUnavailable."""
        from app.core.exceptions import LLMProviderUnavailable
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('Rate limit exceeded')
        exc.status_code = 429  # type: ignore[attr-defined]

        with pytest.raises(LLMProviderUnavailable):
            _handle_llm_error(exc, provider='openai')

    def test_402_billing(self) -> None:
        """402 → LLMProviderUnavailable (billing)."""
        from app.core.exceptions import LLMProviderUnavailable
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('Payment required')
        exc.status_code = 402  # type: ignore[attr-defined]

        with pytest.raises(LLMProviderUnavailable):
            _handle_llm_error(exc, provider='openai')

    def test_timeout(self) -> None:
        """Timeout → LLMProviderUnavailable."""
        from app.core.exceptions import LLMProviderUnavailable
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('Connection timed out')

        with pytest.raises(LLMProviderUnavailable):
            _handle_llm_error(exc, provider='groq')


# ============================================================================
# ACCOUNT-DELETE-500-REGRESSION: broader try/except, logger at module top
# ============================================================================


class TestAccountDeleteV44:
    """V44: delete_me wraps entire body in try/except."""

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
        """V44-FIX: any exception → DELETE_ACCOUNT_FAILED, не INTERNAL_ERROR."""
        from sqlalchemy.exc import SQLAlchemyError

        async def failing_commit(self_session: object) -> None:
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

    async def test_flush_failure_returns_delete_account_failed(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """V44-FIX: flush failure in soft_delete → DELETE_ACCOUNT_FAILED."""
        from sqlalchemy.exc import SQLAlchemyError

        async def failing_flush(self_session: object) -> None:
            raise SQLAlchemyError('simulated flush failure')

        with patch(
            'app.auth.router.AsyncSession.flush',
            new=failing_flush,
        ):
            response = await auth_client.request(
                'DELETE',
                '/api/v1/auth/me',
                json={'password': 'TestPass123', 'confirmation': 'УДАЛИТЬ'},
            )

        # The exception from flush propagates through soft_delete_account
        # and is caught by the V44 try/except in delete_me
        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        data = response.json()
        assert data['error'] == 'DELETE_ACCOUNT_FAILED'


# ============================================================================
# URL-VALIDATION: Pydantic validation arrays → user-friendly
# ============================================================================


class TestUrlValidationV44:
    """URL validation errors → user-friendly messages."""

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
# HH-RESUME-LINK: parser module unit tests
# ============================================================================


class TestHHParserModule:
    """Unit-тесты для hh_parser модуля."""

    def test_is_available_returns_bool(self) -> None:
        """is_available() возвращает bool."""
        from app.resumes.hh_parser import is_available

        result = is_available()
        assert isinstance(result, bool)

    async def test_parse_raises_runtime_error_without_playwright(self) -> None:
        """parse_hh_resume → RuntimeError если playwright не установлен."""
        from app.resumes import hh_parser

        with (
            patch.object(hh_parser, '_HAS_PLAYWRIGHT', False),
            pytest.raises(RuntimeError, match='playwright'),
        ):
            await hh_parser.parse_hh_resume('https://hh.ru/resume/abc123')

    async def test_from_url_endpoint_invalid_url(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """POST /resumes/from-url с невалидным URL → 400."""
        response = await auth_client.post(
            '/api/v1/resumes/from-url',
            json={'url': 'https://example.com/not-hh'},
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert 'hh.ru' in response.json().get('detail', '')

    async def test_from_url_endpoint_no_playwright(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """POST /resumes/from-url без playwright → 400 с инструкцией."""
        from app.resumes import hh_parser

        with patch.object(hh_parser, '_HAS_PLAYWRIGHT', False):
            response = await auth_client.post(
                '/api/v1/resumes/from-url',
                json={'url': 'https://hh.ru/resume/abc123def'},
            )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        detail = response.json().get('detail', '')
        assert 'вручную' in detail.lower() or 'текст' in detail.lower()

    async def test_from_url_endpoint_with_playwright_success(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """POST /resumes/from-url с playwright → 201 (mocked)."""
        from app.resumes import hh_parser

        mock_result = {
            'name': 'Иван Иванов',
            'position': 'Frontend-разработчик',
            'salary': '200 000 руб.',
            'skills': ['React', 'TypeScript'],
            'experience': [
                {'title': 'Разработчик', 'company': 'ООО Тест', 'period': '2020-2024'},
            ],
            'raw_text': 'Иван Иванов\nДолжность: Frontend-разработчик\nНавыки: React, TypeScript',
        }

        with (
            patch.object(hh_parser, '_HAS_PLAYWRIGHT', True),
            patch.object(
                hh_parser,
                'parse_hh_resume',
                new_callable=AsyncMock,
                return_value=mock_result,
            ),
        ):
            response = await auth_client.post(
                '/api/v1/resumes/from-url',
                json={'url': 'https://hh.ru/resume/abc123def'},
            )

        assert response.status_code == HTTPStatus.CREATED
        data = response.json()
        assert data['title'] == 'Frontend-разработчик'

    async def test_from_url_endpoint_with_playwright_parse_error(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """POST /resumes/from-url с playwright но ошибка парсинга → 400 fallback."""
        from app.resumes import hh_parser

        with (
            patch.object(hh_parser, '_HAS_PLAYWRIGHT', True),
            patch.object(
                hh_parser,
                'parse_hh_resume',
                new_callable=AsyncMock,
                side_effect=RuntimeError('Browser launch failed'),
            ),
        ):
            response = await auth_client.post(
                '/api/v1/resumes/from-url',
                json={'url': 'https://hh.ru/resume/abc123def'},
            )

        # Falls through to manual instruction fallback
        assert response.status_code == HTTPStatus.BAD_REQUEST
        detail = response.json().get('detail', '').lower()
        assert 'вручную' in detail or 'текст' in detail


# ============================================================================
# LLM Factory: model mapping validation
# ============================================================================


class TestLLMFactoryModelMapping:
    """Проверка корректного маппинга моделей в фабрике."""

    def test_openai_default_model(self) -> None:
        """OpenAI по умолчанию → gpt-4o-mini."""
        from app.ml.llm_factory import _MODEL_NAMES

        assert _MODEL_NAMES['openai'] == 'gpt-4o-mini'

    def test_anthropic_default_model(self) -> None:
        """Anthropic по умолчанию → claude-sonnet-4-20250514."""
        from app.ml.llm_factory import _MODEL_NAMES

        assert _MODEL_NAMES['anthropic'] == 'claude-sonnet-4-20250514'

    def test_groq_default_model(self) -> None:
        """Groq по умолчанию → llama-3.3-70b-versatile (не allam-2-7b)."""
        from app.ml.llm_factory import _MODEL_NAMES

        assert _MODEL_NAMES['groq'] == 'llama-3.3-70b-versatile'
        assert 'allam' not in _MODEL_NAMES['groq']

    def test_sub_model_overrides_default(self) -> None:
        """Фабрика использует sub_model вместо дефолта."""
        from app.ml.llm_client import OpenAIClient
        from app.ml.llm_factory import LLMClientFactory

        client = LLMClientFactory.create('openai', sub_model='gpt-4o', api_key='test-key')
        assert isinstance(client, OpenAIClient)
        assert client._model == 'gpt-4o'

    def test_gigachat_not_in_sub_model_providers(self) -> None:
        """GigaChat не в SUB_MODEL_PROVIDERS — sub_model игнорируется."""
        from app.ml.llm_factory import SUB_MODEL_PROVIDERS

        assert 'gigachat-pro' not in SUB_MODEL_PROVIDERS

    def test_openai_in_sub_model_providers(self) -> None:
        """OpenAI в SUB_MODEL_PROVIDERS — sub_model используется."""
        from app.ml.llm_factory import SUB_MODEL_PROVIDERS

        assert 'openai' in SUB_MODEL_PROVIDERS


# ============================================================================
# REGRESSION: existing functionality still works
# ============================================================================


class TestRegressionV44:
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
            json={'full_name': 'Тест V44'},
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json()['full_name'] == 'Тест V44'

    async def test_register_new_user(
        self,
        client: AsyncClient,
    ) -> None:
        """Регистрация нового пользователя → 201."""
        response = await client.post(
            '/api/v1/auth/register',
            json={
                'email': 'v44-new@example.com',
                'password': 'StrongPass123',
                'full_name': 'Новый V44',
            },
        )
        assert response.status_code == HTTPStatus.CREATED
        assert 'access_token' in response.json()

    async def test_create_resume_from_text(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """Создание резюме из текста → 201."""
        response = await auth_client.post(
            '/api/v1/resumes/from-text',
            json={
                'text': 'Иван Иванов\nДолжность: Frontend-разработчик\nОпыт: 5 лет',
                'title': 'Резюме V44',
            },
        )
        assert response.status_code == HTTPStatus.CREATED
        assert response.json()['title'] == 'Резюме V44'

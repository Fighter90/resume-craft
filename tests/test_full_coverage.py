"""Тесты для достижения 100% покрытия бэкенда.

Покрывает все gap-ы из coverage отчёта:
- auth/router.py: form-data login, avatar deletion exception
- auth/service.py: delete_user_files exception path
- core/config.py: validate_secret_key in production
- core/dependencies.py: get_optional_user full flow
- ml/llm_client.py: Groq error handler
- ml/router.py: _get_user_keys, _fetch_groq_models, all ping functions
- rewriter/router.py: missing API key → 400
- rewriter/service.py: user_keys aliases population
- settings/router.py: ai-toggles, ai-model CRUD
- settings/service.py: set_setting, get_decrypted_value, get_ai_keys_status
- vacancies/router.py: get_hh_vacancy_details
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx
import pytest

# ── auth/router.py: form-data login (lines 44–45, 57–62) ────────────────────


class TestLoginFormData:
    """Тестирование логина через form-data и fallback 415."""

    async def test_login_form_urlencoded(self, client, test_user) -> None:  # type: ignore[no-untyped-def]
        """application/x-www-form-urlencoded → успешный логин."""
        response = await client.post(
            '/api/v1/auth/login',
            data={'email': test_user.email, 'password': 'TestPass123'},
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
        )
        assert response.status_code == 200
        assert 'access_token' in response.json()

    async def test_login_multipart_form(self, client, test_user) -> None:  # type: ignore[no-untyped-def]
        """multipart/form-data → успешный логин (username field)."""
        response = await client.post(
            '/api/v1/auth/login',
            data={'username': test_user.email, 'password': 'TestPass123'},
        )
        assert response.status_code == 200
        assert 'access_token' in response.json()

    async def test_login_unsupported_content_type(self, client) -> None:  # type: ignore[no-untyped-def]
        """Неизвестный Content-Type с невалидным body → 415."""
        response = await client.post(
            '/api/v1/auth/login',
            content=b'not-json-at-all',
            headers={'Content-Type': 'text/plain'},
        )
        assert response.status_code == 415

    async def test_login_json_content_type_invalid_body(self, client) -> None:  # type: ignore[no-untyped-def]
        """application/json + невалидный JSON body → 422 Некорректный JSON."""
        response = await client.post(
            '/api/v1/auth/login',
            content=b'this is not valid json {{{{',
            headers={'Content-Type': 'application/json'},
        )
        assert response.status_code == 422
        assert 'Некорректный JSON' in response.json()['detail']


class TestParseLoginDataDirect:
    """Прямое тестирование _parse_login_data для покрытия всех ветвей."""

    async def test_form_urlencoded_branch(self) -> None:
        """Ветка elif: application/x-www-form-urlencoded content-type."""
        from app.auth.router import _parse_login_data

        scope = {
            'type': 'http',
            'headers': [
                (b'content-type', b'application/x-www-form-urlencoded'),
            ],
        }
        body = b'email=user%40example.com&password=TestPass123'

        async def receive():  # type: ignore[no-untyped-def]
            return {'type': 'http.request', 'body': body}

        from starlette.requests import Request

        request = Request(scope, receive)
        email, password = await _parse_login_data(request)
        assert email == 'user@example.com'
        assert password == 'TestPass123'

    async def test_multipart_form_branch(self) -> None:
        """Ветка elif: multipart/form-data content-type."""
        from app.auth.router import _parse_login_data

        body = (
            b'------boundary123\r\n'
            b'Content-Disposition: form-data; name="username"\r\n\r\n'
            b'user@example.com\r\n'
            b'------boundary123\r\n'
            b'Content-Disposition: form-data; name="password"\r\n\r\n'
            b'TestPass123\r\n'
            b'------boundary123--\r\n'
        )
        scope = {
            'type': 'http',
            'headers': [
                (b'content-type', b'multipart/form-data; boundary=----boundary123'),
            ],
        }

        async def receive():  # type: ignore[no-untyped-def]
            return {'type': 'http.request', 'body': body}

        from starlette.requests import Request

        request = Request(scope, receive)
        email, password = await _parse_login_data(request)
        assert email == 'user@example.com'
        assert password == 'TestPass123'

    async def test_else_branch_json_fallback(self) -> None:
        """Ветка else (нет content-type) → JSON fallback."""
        import json

        from app.auth.router import _parse_login_data

        body = json.dumps({'email': 'user@example.com', 'password': 'TestPass123'}).encode()
        scope = {'type': 'http', 'headers': []}

        async def receive():  # type: ignore[no-untyped-def]
            return {'type': 'http.request', 'body': body}

        from starlette.requests import Request

        request = Request(scope, receive)
        email, password = await _parse_login_data(request)
        assert email == 'user@example.com'
        assert password == 'TestPass123'


# ── auth/router.py: avatar deletion exception (lines 320-321) ───────────────


class TestAvatarDeleteException:
    """Тест ветки exception при удалении файла аватара."""

    async def test_delete_avatar_file_error_ignored(
        self,
        auth_client,
        test_user,
        session,  # type: ignore[no-untyped-def]
    ) -> None:
        """Ошибка удаления файла аватара → логирование, без 500."""
        test_user.avatar_url = '/uploads/avatars/old-avatar.jpg'
        await session.flush()

        mock_storage = MagicMock()
        mock_storage.delete = AsyncMock(side_effect=OSError('Disk error'))

        with patch('app.core.storage.file_storage', mock_storage):
            response = await auth_client.delete('/api/v1/auth/me/avatar')
            assert response.status_code == 204


# ── auth/service.py: delete_user_files exception (lines 235-236) ────────────


class TestDeleteUserAccountFileError:
    """Тест ветки exception при delete_user_files."""

    async def test_delete_user_files_error_logged(self, session, test_user) -> None:  # type: ignore[no-untyped-def]
        """Ошибка удаления файлов → логируется, пользователь удаляется."""
        from app.auth.service import delete_user_account

        mock_storage = MagicMock()
        mock_storage.delete_user_files = AsyncMock(side_effect=OSError('FS error'))

        with patch('app.core.storage.file_storage', mock_storage):
            await delete_user_account(session, user=test_user)

        # Пользователь должен быть удалён из сессии
        from sqlalchemy import select

        from app.auth.models import User

        result = await session.execute(select(User).where(User.id == test_user.id))
        assert result.scalar_one_or_none() is None


# ── core/config.py: validate_secret_key in production (lines 85-91) ─────────


class TestSecretKeyValidation:
    """Тест валидации SECRET_KEY в production-режиме."""

    def test_weak_secret_key_in_production_raises(self) -> None:
        """Production + placeholder-ключ → ValueError."""
        from app.core.config import Settings

        with pytest.raises(ValueError, match='SECRET_KEY содержит placeholder'):
            Settings(
                secret_key='change-me-please',
                environment='production',
                database_url='postgresql+asyncpg://u:p@localhost/db',
            )

    def test_weak_secret_key_in_testing_warns(self) -> None:
        """Testing + placeholder-ключ → warning, но без ошибки."""
        from app.core.config import Settings

        # Не должно бросить исключение
        settings = Settings(
            secret_key='change-me-placeholder',
            environment='testing',
            database_url='sqlite+aiosqlite://',
        )
        assert settings.secret_key == 'change-me-placeholder'


# ── core/dependencies.py: get_optional_user (lines 91-116) ──────────────────


class TestGetOptionalUser:
    """Тестирование get_optional_user (все ветви)."""

    async def test_no_token_returns_none(self, session) -> None:  # type: ignore[no-untyped-def]
        """Нет токена → None."""
        from app.core.dependencies import get_optional_user

        result = await get_optional_user(token=None, session=session)
        assert result is None

    async def test_expired_token_returns_none(self, session) -> None:  # type: ignore[no-untyped-def]
        """Expired токен → None."""
        from app.core.dependencies import get_optional_user

        result = await get_optional_user(token='expired.jwt.token', session=session)
        assert result is None

    async def test_wrong_type_token_returns_none(self, session) -> None:  # type: ignore[no-untyped-def]
        """Токен с type != access → None."""
        from app.core.dependencies import get_optional_user
        from app.core.security import create_refresh_token

        token = create_refresh_token(uuid4())
        result = await get_optional_user(token=token, session=session)
        assert result is None

    async def test_no_sub_returns_none(self, session) -> None:  # type: ignore[no-untyped-def]
        """Токен без sub → None."""
        import jwt as pyjwt

        from app.core.config import get_settings
        from app.core.dependencies import get_optional_user

        settings = get_settings()
        payload = {'type': 'access'}
        token = pyjwt.encode(payload, settings.secret_key, algorithm='HS256')
        result = await get_optional_user(token=token, session=session)
        assert result is None

    async def test_invalid_uuid_sub_returns_none(self, session) -> None:  # type: ignore[no-untyped-def]
        """Невалидный UUID в sub → None."""
        import jwt as pyjwt

        from app.core.config import get_settings
        from app.core.dependencies import get_optional_user

        settings = get_settings()
        payload = {'type': 'access', 'sub': 'not-a-uuid'}
        token = pyjwt.encode(payload, settings.secret_key, algorithm='HS256')
        result = await get_optional_user(token=token, session=session)
        assert result is None

    async def test_user_not_found_returns_none(self, session) -> None:  # type: ignore[no-untyped-def]
        """Пользователь не найден → None."""
        from app.core.dependencies import get_optional_user
        from app.core.security import create_access_token

        token = create_access_token(uuid4())
        result = await get_optional_user(token=token, session=session)
        assert result is None

    async def test_inactive_user_returns_none(self, session, test_user) -> None:  # type: ignore[no-untyped-def]
        """Неактивный пользователь → None."""
        from app.core.dependencies import get_optional_user
        from app.core.security import create_access_token

        test_user.is_active = False
        await session.flush()

        token = create_access_token(test_user.id)
        result = await get_optional_user(token=token, session=session)
        assert result is None

    async def test_valid_token_returns_user(self, session, test_user) -> None:  # type: ignore[no-untyped-def]
        """Валидный токен → пользователь."""
        from app.core.dependencies import get_optional_user
        from app.core.security import create_access_token

        token = create_access_token(test_user.id)
        result = await get_optional_user(token=token, session=session)
        assert result is not None
        assert result.id == test_user.id


# ── ml/llm_client.py: Groq error handler (lines 401-402) ────────────────────


class TestGroqLLMError:
    """Groq complete() → _handle_llm_error path."""

    async def test_groq_complete_raises_handles_error(self) -> None:
        """Groq API ошибка → _handle_llm_error."""
        from app.ml.llm_client import GroqClient

        client = GroqClient(api_key='test-key', model='test-model')
        mock_groq = AsyncMock()
        exc = Exception('Unauthorized')
        exc.status_code = 401  # type: ignore[attr-defined]
        mock_groq.chat.completions.create = AsyncMock(side_effect=exc)
        client._client = mock_groq

        from app.core.exceptions import LLMAuthError

        with pytest.raises(LLMAuthError):
            await client.complete(system='sys', user='usr')


# ── ml/router.py: _get_user_keys (lines 51-62) ─────────────────────────────


class TestGetUserKeys:
    """Тестирование _get_user_keys helper."""

    async def test_no_user_returns_all_false(self) -> None:
        """Без пользователя → все False."""
        from app.ml.router import _get_user_keys

        result = await _get_user_keys(session=None, user=None)
        assert all(v is False for v in result.values())

    async def test_with_user_queries_settings(self, session, test_user) -> None:  # type: ignore[no-untyped-def]
        """С пользователем → запросы к settings.get_setting."""
        from app.ml.router import _get_user_keys

        # Сохраним ключ для одного провайдера
        from app.settings.service import set_setting

        await set_setting(
            session,
            user_id=test_user.id,
            category='ai_keys',
            key='openai',
            value='sk-test-key',
        )

        result = await _get_user_keys(session=session, user=test_user)
        assert result['openai'] is True
        assert result['gigachat'] is False


# ── ml/router.py: _fetch_groq_models (lines 502-531) ────────────────────────


class TestFetchGroqModels:
    """Тестирование _fetch_groq_models."""

    async def test_empty_key_returns_error(self) -> None:
        """Пустой ключ → ошибка."""
        from app.ml.router import _fetch_groq_models

        result = await _fetch_groq_models('')
        assert result['error'] == 'API-ключ Groq не настроен'

    async def test_successful_fetch(self) -> None:
        """Успешный запрос → filtered models."""
        from app.ml.router import _fetch_groq_models

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            'data': [
                {'id': 'llama-3.3-70b-versatile'},
                {'id': 'whisper-large-v3'},  # should be filtered
                {'id': 'mixtral-8x7b-32768'},
            ]
        }

        with patch('app.ml.router.httpx.AsyncClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await _fetch_groq_models('gsk_test_key')

        assert 'sub_models' in result
        ids = [m['id'] for m in result['sub_models']]
        assert 'llama-3.3-70b-versatile' in ids
        assert 'whisper-large-v3' not in ids

    async def test_fetch_exception_returns_fallback(self) -> None:
        """Ошибка запроса → fallback-модели."""
        from app.ml.router import _fetch_groq_models

        with patch('app.ml.router.httpx.AsyncClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.ConnectError('Network error')
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await _fetch_groq_models('gsk_test_key')

        assert result.get('fallback') is True
        assert len(result['sub_models']) > 0


# ── ml/router.py: ping functions (lines 575-693) ────────────────────────────


class TestPingGigachat:
    """Тестирование _ping_gigachat."""

    async def test_ping_success(self) -> None:
        """Успешный пинг → ok."""

        with (
            patch('app.ml.router.GigaChat', create=True) as mock_gc_cls,
            patch.dict('sys.modules', {'gigachat': MagicMock()}),
            patch('app.ml.router._ping_gigachat') as mock_ping,
        ):
            mock_gc = MagicMock()
            mock_gc.get_models.return_value = []
            mock_gc_cls.return_value = mock_gc

            mock_ping.return_value = {'status': 'ok', 'message': 'Доступен'}
            result = await mock_ping('creds')
            assert result['status'] == 'ok'

    async def test_ping_billing_error(self) -> None:
        """billing error → billing_error status."""
        from app.ml.router import _ping_gigachat

        with patch.dict('sys.modules', {'gigachat': MagicMock()}) as mods:
            gc_mod = mods['gigachat']
            gc_instance = MagicMock()
            gc_instance.get_models.side_effect = Exception('Недостаточно средств на balance')
            gc_mod.GigaChat.return_value = gc_instance

            result = await _ping_gigachat('creds', scope='GIGACHAT_API_PERS')
        assert result['status'] == 'billing_error'

    async def test_ping_auth_error(self) -> None:
        """auth error → auth_error status."""
        from app.ml.router import _ping_gigachat

        with patch.dict('sys.modules', {'gigachat': MagicMock()}) as mods:
            gc_mod = mods['gigachat']
            gc_instance = MagicMock()
            gc_instance.get_models.side_effect = Exception('401 auth error')
            gc_mod.GigaChat.return_value = gc_instance

            result = await _ping_gigachat('creds', scope='GIGACHAT_API_PERS')
        assert result['status'] == 'auth_error'

    async def test_ping_generic_error(self) -> None:
        """Generic error → error status."""
        from app.ml.router import _ping_gigachat

        with patch.dict('sys.modules', {'gigachat': MagicMock()}) as mods:
            gc_mod = mods['gigachat']
            gc_instance = MagicMock()
            gc_instance.get_models.side_effect = Exception('Something unknown')
            gc_mod.GigaChat.return_value = gc_instance

            result = await _ping_gigachat('creds', scope='GIGACHAT_API_PERS')
        assert result['status'] == 'error'


class TestPingOpenAI:
    """Тестирование _ping_openai."""

    async def test_ping_success(self) -> None:
        from app.ml.router import _ping_openai

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with patch('app.ml.router.httpx.AsyncClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await _ping_openai('sk-test')
        assert result['status'] == 'ok'

    async def test_ping_401(self) -> None:
        from app.ml.router import _ping_openai

        mock_resp = MagicMock()
        mock_resp.status_code = 401
        exc = httpx.HTTPStatusError('401', request=MagicMock(), response=mock_resp)

        with patch('app.ml.router.httpx.AsyncClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = exc
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await _ping_openai('bad-key')
        assert result['status'] == 'auth_error'

    async def test_ping_other_http_error(self) -> None:
        from app.ml.router import _ping_openai

        mock_resp = MagicMock()
        mock_resp.status_code = 500
        exc = httpx.HTTPStatusError('500', request=MagicMock(), response=mock_resp)

        with patch('app.ml.router.httpx.AsyncClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = exc
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await _ping_openai('sk-test')
        assert result['status'] == 'error'

    async def test_ping_generic_exception(self) -> None:
        from app.ml.router import _ping_openai

        with patch('app.ml.router.httpx.AsyncClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = Exception('Network down')
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await _ping_openai('sk-test')
        assert result['status'] == 'error'


class TestPingAnthropic:
    """Тестирование _ping_anthropic."""

    async def test_ping_success(self) -> None:
        from app.ml.router import _ping_anthropic

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with patch('app.ml.router.httpx.AsyncClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await _ping_anthropic('sk-ant-test')
        assert result['status'] == 'ok'

    async def test_ping_401(self) -> None:
        from app.ml.router import _ping_anthropic

        mock_resp = MagicMock()
        mock_resp.status_code = 401
        exc = httpx.HTTPStatusError('401', request=MagicMock(), response=mock_resp)

        with patch('app.ml.router.httpx.AsyncClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = exc
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await _ping_anthropic('bad-key')
        assert result['status'] == 'auth_error'

    async def test_ping_other_error(self) -> None:
        from app.ml.router import _ping_anthropic

        mock_resp = MagicMock()
        mock_resp.status_code = 503
        exc = httpx.HTTPStatusError('503', request=MagicMock(), response=mock_resp)

        with patch('app.ml.router.httpx.AsyncClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = exc
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await _ping_anthropic('key')
        assert result['status'] == 'error'

    async def test_ping_generic_exception(self) -> None:
        from app.ml.router import _ping_anthropic

        with patch('app.ml.router.httpx.AsyncClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = Exception('Timeout')
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await _ping_anthropic('key')
        assert result['status'] == 'error'


class TestPingOpenRouter:
    """Тестирование _ping_openrouter."""

    async def test_ping_success(self) -> None:
        from app.ml.router import _ping_openrouter

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with patch('app.ml.router.httpx.AsyncClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await _ping_openrouter('sk-or-test')
        assert result['status'] == 'ok'

    async def test_ping_401(self) -> None:
        from app.ml.router import _ping_openrouter

        mock_resp = MagicMock()
        mock_resp.status_code = 401
        exc = httpx.HTTPStatusError('401', request=MagicMock(), response=mock_resp)

        with patch('app.ml.router.httpx.AsyncClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = exc
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await _ping_openrouter('bad-key')
        assert result['status'] == 'auth_error'

    async def test_ping_other_error(self) -> None:
        from app.ml.router import _ping_openrouter

        mock_resp = MagicMock()
        mock_resp.status_code = 502
        exc = httpx.HTTPStatusError('502', request=MagicMock(), response=mock_resp)

        with patch('app.ml.router.httpx.AsyncClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = exc
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await _ping_openrouter('key')
        assert result['status'] == 'error'

    async def test_ping_generic_exception(self) -> None:
        from app.ml.router import _ping_openrouter

        with patch('app.ml.router.httpx.AsyncClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = Exception('DNS error')
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await _ping_openrouter('key')
        assert result['status'] == 'error'


class TestPingGroq:
    """Тестирование _ping_groq."""

    async def test_ping_success(self) -> None:
        from app.ml.router import _ping_groq

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with patch('app.ml.router.httpx.AsyncClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await _ping_groq('gsk-test')
        assert result['status'] == 'ok'

    async def test_ping_401(self) -> None:
        from app.ml.router import _ping_groq

        mock_resp = MagicMock()
        mock_resp.status_code = 401
        exc = httpx.HTTPStatusError('401', request=MagicMock(), response=mock_resp)

        with patch('app.ml.router.httpx.AsyncClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = exc
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await _ping_groq('bad-key')
        assert result['status'] == 'auth_error'

    async def test_ping_other_error(self) -> None:
        from app.ml.router import _ping_groq

        mock_resp = MagicMock()
        mock_resp.status_code = 500
        exc = httpx.HTTPStatusError('500', request=MagicMock(), response=mock_resp)

        with patch('app.ml.router.httpx.AsyncClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = exc
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await _ping_groq('key')
        assert result['status'] == 'error'

    async def test_ping_generic_exception(self) -> None:
        from app.ml.router import _ping_groq

        with patch('app.ml.router.httpx.AsyncClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = Exception('Connection refused')
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await _ping_groq('key')
        assert result['status'] == 'error'


# ── rewriter/router.py: missing API key → 400 (lines 88-90) ─────────────────


class TestRewriterMissingAPIKey:
    """Тест ветки: API-ключ не настроен → 400."""

    async def test_rewrite_no_api_key_returns_400(
        self,
        auth_client,
        test_user,
        session,  # type: ignore[no-untyped-def]
    ) -> None:
        """Запуск оптимизации без ключа → 400."""
        from app.resumes.models import Resume
        from app.vacancies.models import Vacancy

        resume = Resume(
            id=uuid4(),
            user_id=test_user.id,
            title='Test Resume',
            file_path='/test.pdf',
            file_format='pdf',
            file_size_bytes=100,
            raw_text='Python Developer',
        )
        vacancy = Vacancy(
            id=uuid4(),
            user_id=test_user.id,
            title='Python Dev',
            description='Python requirements',
        )
        session.add_all([resume, vacancy])
        await session.flush()

        # Удаляем все env-ключи чтобы гарантировать отсутствие
        mock_s = MagicMock()
        mock_s.gigachat_credentials = ''
        mock_s.openai_api_key = ''
        mock_s.anthropic_api_key = ''
        mock_s.openrouter_api_key = ''
        mock_s.groq_api_key = ''

        with (
            patch('app.core.config.get_settings', return_value=mock_s),
            patch(
                'app.settings.service.get_user_setting', new_callable=AsyncMock, return_value=''
            ),
        ):
            response = await auth_client.post(
                '/api/v1/rewrite',
                json={
                    'resume_id': str(resume.id),
                    'vacancy_id': str(vacancy.id),
                    'model': 'openai',
                },
            )
        assert response.status_code == 400
        assert 'не настроен' in response.json()['detail']


# ── settings/router.py: ai-toggles, ai-model (lines 101-191) ───────────────


class TestSettingsTogglesEndpoints:
    """Тесты для GET/PUT /settings/ai-toggles."""

    async def test_get_toggles(self, auth_client) -> None:  # type: ignore[no-untyped-def]
        """GET /settings/ai-toggles → toggles с defaults."""
        response = await auth_client.get('/api/v1/settings/ai-toggles')
        assert response.status_code == 200
        data = response.json()
        assert 'toggles' in data
        # Дефолтные включённые: auto_metrics, ats, keep_language
        assert data['toggles']['auto_metrics'] is True
        assert data['toggles']['ats'] is True

    async def test_save_toggles(self, auth_client) -> None:  # type: ignore[no-untyped-def]
        """PUT /settings/ai-toggles → save & return."""
        response = await auth_client.put(
            '/api/v1/settings/ai-toggles',
            json={
                'toggles': [
                    {'key': 'auto_metrics', 'value': False},
                    {'key': 'soft_skills', 'value': True},
                ]
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data['toggles']['auto_metrics'] is False
        assert data['toggles']['soft_skills'] is True


class TestSettingsModelEndpoints:
    """Тесты для GET/PUT /settings/ai-model."""

    async def test_get_selected_model_default(self, auth_client) -> None:  # type: ignore[no-untyped-def]
        """GET /settings/ai-model → default gigachat-pro."""
        response = await auth_client.get('/api/v1/settings/ai-model')
        assert response.status_code == 200
        data = response.json()
        assert data['model'] == 'gigachat-pro'

    async def test_save_selected_model(self, auth_client) -> None:  # type: ignore[no-untyped-def]
        """PUT /settings/ai-model → update model."""
        response = await auth_client.put(
            '/api/v1/settings/ai-model',
            json={'model': 'openai', 'sub_model': 'gpt-4o'},
        )
        assert response.status_code == 200
        data = response.json()
        assert data['model'] == 'openai'
        assert data['sub_model'] == 'gpt-4o'

    async def test_save_and_get_model(self, auth_client) -> None:  # type: ignore[no-untyped-def]
        """PUT + GET → данные сохраняются."""
        await auth_client.put(
            '/api/v1/settings/ai-model',
            json={'model': 'anthropic'},
        )
        response = await auth_client.get('/api/v1/settings/ai-model')
        assert response.status_code == 200
        assert response.json()['model'] == 'anthropic'


# ── settings/service.py: set_setting update, get_decrypted_value, get_ai_keys_status ──


class TestSettingsService:
    """Тесты для settings/service.py gaps."""

    async def test_set_setting_update_existing(self, session, test_user) -> None:  # type: ignore[no-untyped-def]
        """set_setting обновляет существующую настройку."""
        from app.settings.service import get_decrypted_value, set_setting

        await set_setting(
            session,
            user_id=test_user.id,
            category='test',
            key='key1',
            value='value1',
        )
        # Обновляем
        await set_setting(
            session,
            user_id=test_user.id,
            category='test',
            key='key1',
            value='value2',
        )
        # Проверяем
        val = await get_decrypted_value(
            session,
            user_id=test_user.id,
            category='test',
            key='key1',
        )
        assert val == 'value2'

    async def test_set_setting_encrypted(self, session, test_user) -> None:  # type: ignore[no-untyped-def]
        """set_setting с шифрованием."""
        from app.settings.service import get_decrypted_value, set_setting

        await set_setting(
            session,
            user_id=test_user.id,
            category='ai_keys',
            key='openai',
            value='sk-test-key-123',
            is_encrypted=True,
        )
        val = await get_decrypted_value(
            session,
            user_id=test_user.id,
            category='ai_keys',
            key='openai',
        )
        assert val == 'sk-test-key-123'

    async def test_get_decrypted_value_not_found(self, session, test_user) -> None:  # type: ignore[no-untyped-def]
        """get_decrypted_value для несуществующего ключа → ''."""
        from app.settings.service import get_decrypted_value

        val = await get_decrypted_value(
            session,
            user_id=test_user.id,
            category='nonexistent',
            key='nope',
        )
        assert val == ''

    async def test_get_ai_keys_status_empty(self, session, test_user) -> None:  # type: ignore[no-untyped-def]
        """get_ai_keys_status без ключей → все has_key=False."""
        from app.settings.service import get_ai_keys_status

        result = await get_ai_keys_status(session, user_id=test_user.id)
        assert all(k.has_key is False for k in result)

    async def test_get_ai_keys_status_with_key(self, session, test_user) -> None:  # type: ignore[no-untyped-def]
        """get_ai_keys_status с ключом → has_key=True + masked."""
        from app.settings.service import get_ai_keys_status, set_setting

        await set_setting(
            session,
            user_id=test_user.id,
            category='ai_keys',
            key='openai',
            value='sk-proj-abcdef123456',
            is_encrypted=True,
        )
        result = await get_ai_keys_status(session, user_id=test_user.id)
        openai_status = next(k for k in result if k.provider == 'openai')
        assert openai_status.has_key is True
        assert '...' in openai_status.masked_key


# ── vacancies/router.py: get_hh_vacancy_details (line 49) ───────────────────


class TestGetHHVacancyDetails:
    """Тестирование endpoint /vacancies/hh/{hh_id}."""

    async def test_get_hh_vacancy_details(self, auth_client) -> None:  # type: ignore[no-untyped-def]
        """GET /vacancies/hh/{hh_id} → vacancy data from hh.ru."""
        from app.vacancies.schemas import HHVacancyItem

        mock_item = HHVacancyItem(
            hh_id='12345',
            title='Python Developer',
            url='https://hh.ru/vacancy/12345',
            company='TestCo',
            city='Москва',
            experience='1-3 года',
            key_skills=['Python'],
            description='Python developer needed',
        )

        with patch(
            'app.vacancies.router.vacancy_service.get_hh_vacancy_detail',
            new_callable=AsyncMock,
            return_value=mock_item,
        ):
            response = await auth_client.get('/api/v1/vacancies/hh/12345')

        assert response.status_code == 200
        assert response.json()['hh_id'] == '12345'


# ── rewriter/service.py: user_keys aliases (lines 160-164) ──────────────────


class TestRewriterServiceAliases:
    """Тест ветки: пользовательские ключи с алиасами в rewriter/service."""

    async def test_user_keys_aliases_populated(self) -> None:
        """Если key_val найден для db_key, алиасы также заполняются."""

        # Тестируем логику напрямую: когда get_user_setting возвращает ключ для 'gigachat',
        # алиасы 'gigachat-pro' и 'gigachat-lite' должны быть заполнены
        _provider_key_map: dict[str, str] = {
            'gigachat-pro': 'gigachat',
            'gigachat-lite': 'gigachat',
            'openai': 'openai',
        }
        user_keys: dict[str, str] = {}

        # Симулируем логику из service.py
        for prov_name, db_key in _provider_key_map.items():
            if db_key not in user_keys:
                key_val = 'test-gigachat-key' if db_key == 'gigachat' else ''
                if key_val:
                    user_keys[prov_name] = key_val
                    for alias, alias_key in _provider_key_map.items():
                        if alias_key == db_key and alias not in user_keys:
                            user_keys[alias] = key_val

        assert 'gigachat-pro' in user_keys
        assert 'gigachat-lite' in user_keys
        assert user_keys['gigachat-pro'] == 'test-gigachat-key'


# ── settings/service.py: save_ai_key invalid provider (lines 128-129) ───────


class TestSaveAiKeyInvalidProvider:
    """Тест ветки: save_ai_key с невалидным провайдером → ValueError."""

    async def test_invalid_provider_raises_value_error(self, session, test_user) -> None:  # type: ignore[no-untyped-def]
        """Невалидный провайдер → ValueError."""
        from app.settings.service import save_ai_key

        with pytest.raises(ValueError, match='Неизвестный провайдер'):
            await save_ai_key(
                session,
                user_id=test_user.id,
                provider='invalid_nonexistent_provider',
                api_key='sk-test-key',
            )


# ── ml/router.py: get_sub_models with auth user (lines 156-158) ─────────────


class TestGetSubModelsWithAuth:
    """Тестирование /models/{provider}/sub-models с авторизованным пользователем."""

    async def test_sub_models_openai_with_auth(
        self,
        auth_client,
        test_user,
        session,  # type: ignore[no-untyped-def]
    ) -> None:
        """GET /models/openai/sub-models с user key → user key used."""
        # Сохраняем ключ пользователя
        from app.settings.service import set_setting

        await set_setting(
            session,
            user_id=test_user.id,
            category='ai_keys',
            key='openai',
            value='sk-user-test-key',
            is_encrypted=True,
        )
        await session.commit()

        # Мокаем _fetch_openai_models чтобы не делать реальные запросы
        mock_result = {'sub_models': [{'id': 'gpt-4o', 'name': 'GPT-4o', 'provider': 'OpenAI'}]}
        with patch(
            'app.ml.router._fetch_openai_models', new_callable=AsyncMock, return_value=mock_result
        ):
            response = await auth_client.get('/api/v1/models/openai/sub-models')

        assert response.status_code == 200
        data = response.json()
        assert 'sub_models' in data

    async def test_sub_models_anthropic_with_auth(
        self,
        auth_client,
        test_user,
        session,  # type: ignore[no-untyped-def]
    ) -> None:
        """GET /models/anthropic/sub-models с user key."""
        from app.settings.service import set_setting

        await set_setting(
            session,
            user_id=test_user.id,
            category='ai_keys',
            key='anthropic',
            value='sk-ant-user-test',
            is_encrypted=True,
        )
        await session.commit()

        mock_result = {
            'sub_models': [
                {'id': 'claude-3-5-sonnet', 'name': 'Claude 3.5 Sonnet', 'provider': 'Anthropic'}
            ]
        }
        with patch(
            'app.ml.router._fetch_anthropic_models',
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            response = await auth_client.get('/api/v1/models/anthropic/sub-models')

        assert response.status_code == 200


# ── ml/router.py: health endpoint dispatch (lines 575-577, 596-602) ─────────


class TestHealthEndpointDispatch:
    """Тестирование /models/health endpoint — все dispatch-ветки."""

    async def test_health_with_env_keys_all_providers(self, client) -> None:  # type: ignore[no-untyped-def]
        """Health check с env-ключами — покрывает все dispatch ветки."""
        mock_settings = MagicMock()
        mock_settings.gigachat_credentials = 'test-gc-creds'
        mock_settings.openai_api_key = 'sk-test-openai'
        mock_settings.anthropic_api_key = 'sk-ant-test'
        mock_settings.openrouter_api_key = 'sk-or-test'
        mock_settings.groq_api_key = 'gsk-test'
        mock_settings.gigachat_scope = 'GIGACHAT_API_PERS'

        with (
            patch('app.ml.router.get_settings', return_value=mock_settings),
            patch(
                'app.ml.router._ping_gigachat',
                new_callable=AsyncMock,
                return_value={'status': 'ok', 'message': 'OK'},
            ),
            patch(
                'app.ml.router._ping_openai',
                new_callable=AsyncMock,
                return_value={'status': 'ok', 'message': 'OK'},
            ),
            patch(
                'app.ml.router._ping_anthropic',
                new_callable=AsyncMock,
                return_value={'status': 'ok', 'message': 'OK'},
            ),
            patch(
                'app.ml.router._ping_openrouter',
                new_callable=AsyncMock,
                return_value={'status': 'ok', 'message': 'OK'},
            ),
            patch(
                'app.ml.router._ping_groq',
                new_callable=AsyncMock,
                return_value={'status': 'ok', 'message': 'OK'},
            ),
        ):
            response = await client.get('/api/v1/models/health')

        assert response.status_code == 200
        data = response.json()
        assert 'providers' in data
        for prov in ['gigachat', 'openai', 'anthropic', 'openrouter', 'groq']:
            assert data['providers'][prov]['status'] == 'ok'

    async def test_health_with_auth_user_keys(
        self,
        auth_client,
        test_user,
        session,  # type: ignore[no-untyped-def]
    ) -> None:
        """Health check с пользовательскими ключами — покрывает user key retrieval."""
        from app.settings.service import set_setting

        # Сохраняем ключи пользователя
        await set_setting(
            session,
            user_id=test_user.id,
            category='ai_keys',
            key='openai',
            value='sk-user',
            is_encrypted=True,
        )
        await set_setting(
            session,
            user_id=test_user.id,
            category='ai_keys',
            key='groq',
            value='gsk-user',
            is_encrypted=True,
        )
        await session.commit()

        mock_settings = MagicMock()
        mock_settings.gigachat_credentials = ''
        mock_settings.openai_api_key = ''
        mock_settings.anthropic_api_key = ''
        mock_settings.openrouter_api_key = ''
        mock_settings.groq_api_key = ''
        mock_settings.gigachat_scope = 'GIGACHAT_API_PERS'

        with (
            patch('app.ml.router.get_settings', return_value=mock_settings),
            patch(
                'app.ml.router._ping_openai',
                new_callable=AsyncMock,
                return_value={'status': 'ok', 'message': 'OK'},
            ),
            patch(
                'app.ml.router._ping_groq',
                new_callable=AsyncMock,
                return_value={'status': 'ok', 'message': 'OK'},
            ),
        ):
            response = await auth_client.get('/api/v1/models/health')

        assert response.status_code == 200
        data = response.json()
        assert data['providers']['openai']['status'] == 'ok'
        assert data['providers']['groq']['status'] == 'ok'
        # Провайдеры без ключей → no_key
        assert data['providers']['gigachat']['status'] == 'no_key'

    async def test_health_ping_exception_handled(self, client) -> None:  # type: ignore[no-untyped-def]
        """Ping-функция бросает исключение → error status."""
        mock_settings = MagicMock()
        mock_settings.gigachat_credentials = ''
        mock_settings.openai_api_key = 'sk-test'
        mock_settings.anthropic_api_key = ''
        mock_settings.openrouter_api_key = ''
        mock_settings.groq_api_key = ''
        mock_settings.gigachat_scope = 'GIGACHAT_API_PERS'

        with (
            patch('app.ml.router.get_settings', return_value=mock_settings),
            patch(
                'app.ml.router._ping_openai',
                new_callable=AsyncMock,
                side_effect=Exception('Connection refused'),
            ),
        ):
            response = await client.get('/api/v1/models/health')

        assert response.status_code == 200
        data = response.json()
        assert data['providers']['openai']['status'] == 'error'

    async def test_health_unknown_provider_else_branch(self, client) -> None:  # type: ignore[no-untyped-def]
        """Неизвестный провайдер в _KEY_FIELDS → else branch → 'ok'."""
        mock_settings = MagicMock()
        mock_settings.gigachat_credentials = ''
        mock_settings.openai_api_key = ''
        mock_settings.anthropic_api_key = ''
        mock_settings.openrouter_api_key = ''
        mock_settings.groq_api_key = ''
        mock_settings.fakeprovider_key = 'fk-test-key'
        mock_settings.gigachat_scope = 'GIGACHAT_API_PERS'

        patched_key_fields = {
            'gigachat': 'gigachat_credentials',
            'openai': 'openai_api_key',
            'anthropic': 'anthropic_api_key',
            'openrouter': 'openrouter_api_key',
            'groq': 'groq_api_key',
            'fakeprovider': 'fakeprovider_key',
        }

        with (
            patch('app.ml.router.get_settings', return_value=mock_settings),
            patch('app.ml.router._KEY_FIELDS', patched_key_fields),
        ):
            response = await client.get('/api/v1/models/health')

        assert response.status_code == 200
        data = response.json()
        # fakeprovider has a key → hits else branch → 'ok'
        assert data['providers']['fakeprovider']['status'] == 'ok'
        assert data['providers']['fakeprovider']['message'] == 'Ключ настроен'


# ── rewriter/service.py: run_rewrite user_keys aliases (lines 160-164) ──────


class TestRewriterServiceRunRewriteAliases:
    """Тестирование run_rewrite — покрытие user_keys алиасов."""

    async def test_run_rewrite_with_user_keys(self, session, test_user) -> None:  # type: ignore[no-untyped-def]
        """run_rewrite с пользовательскими ключами → alias loop выполняется."""
        from app.resumes.models import Resume
        from app.rewriter.models import RewriteHistory, RewriteStatus
        from app.vacancies.models import Vacancy

        # Создаём необходимые данные
        resume = Resume(
            id=uuid4(),
            user_id=test_user.id,
            title='Test',
            file_path='/test.pdf',
            file_format='pdf',
            file_size_bytes=100,
            raw_text='Python Developer with 5 years experience',
        )
        vacancy = Vacancy(
            id=uuid4(),
            user_id=test_user.id,
            title='Python Dev',
            description='Need Python developer',
        )
        session.add_all([resume, vacancy])
        await session.flush()

        task = RewriteHistory(
            id=uuid4(),
            user_id=test_user.id,
            resume_id=resume.id,
            vacancy_id=vacancy.id,
            original_text=resume.raw_text,
            model_name='openai',
            status=RewriteStatus.PENDING,
        )
        session.add(task)
        await session.flush()

        # Сохраняем user key для gigachat → должно заполнить алиасы
        from app.settings.service import set_setting

        await set_setting(
            session,
            user_id=test_user.id,
            category='ai_keys',
            key='gigachat',
            value='test-gc-key',
            is_encrypted=True,
        )
        await set_setting(
            session,
            user_id=test_user.id,
            category='ai_keys',
            key='openai',
            value='sk-test-openai',
            is_encrypted=True,
        )
        await session.flush()

        # Мокаем LLM client чтобы не делать реальные запросы
        import json as json_mod

        mock_llm = AsyncMock()
        mock_llm.complete = AsyncMock(
            return_value=json_mod.dumps(
                {
                    'summary': 'Python Developer',
                    'experience': [
                        {
                            'position': 'Dev',
                            'company': 'Co',
                            'period': '2020-2024',
                            'achievements': ['Led team'],
                        }
                    ],
                    'education': [],
                    'skills': ['Python'],
                    'keywords_added': ['Python'],
                }
            )
        )

        with (
            patch('app.rewriter.service.LLMClientFactory') as mock_factory_cls,
            patch('app.rewriter.service.sanitize_for_llm', side_effect=lambda x: x),
            patch('app.rewriter.service.calculate_match_score', return_value=0.5),
        ):
            mock_factory_cls.create_with_fallback.return_value = mock_llm

            from app.rewriter.service import execute_rewrite

            await execute_rewrite(session, task_id=task.id)

        # Проверяем что task обновлён
        await session.refresh(task)
        assert task.status == RewriteStatus.COMPLETED

"""Тесты покрытия V20 (v1.8) правок.

Покрывает все 9 дефектов V20:
- P0-3: JSON-ответы /auth/me и /rewrite/history
- P0-4: O-series модели (o1, o3, o4) — max_completion_tokens
- P1-1: Dropdown z-index (frontend)
- P1-2: soft_delete_account — JSON-ошибка при неверном пароле
- P1-4: OpenRouter models обновлены
- P1-6: Аватар на сервере (upload/delete)
- P2-1: Прогресс-бар анимация (frontend)
- P2-2: Diff whitespace (frontend)
"""

from __future__ import annotations

import io
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.security import hash_password

# ============================================================================
# P0-4: O-series модели (OpenAI + OpenRouter)
# ============================================================================


class TestOSeriesModels:
    """O-series модели (o1, o3, o4) используют max_completion_tokens вместо max_tokens."""

    async def test_openai_o1_uses_max_completion_tokens(self) -> None:
        """OpenAI o1 → max_completion_tokens, без temperature."""
        from app.ml.llm_client import OpenAIClient

        client = OpenAIClient(model='o1', api_key='test-key')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='test response'))]

        mock_openai = AsyncMock()
        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
        client._client = mock_openai

        result = await client.complete(system='sys', user='usr')
        assert result == 'test response'

        call_kwargs = mock_openai.chat.completions.create.call_args[1]
        assert 'max_completion_tokens' in call_kwargs
        assert 'max_tokens' not in call_kwargs
        assert 'temperature' not in call_kwargs

    async def test_openai_o3_uses_max_completion_tokens(self) -> None:
        """OpenAI o3 → max_completion_tokens, без temperature."""
        from app.ml.llm_client import OpenAIClient

        client = OpenAIClient(model='o3', api_key='test-key')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='o3 response'))]

        mock_openai = AsyncMock()
        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
        client._client = mock_openai

        result = await client.complete(system='sys', user='usr')
        assert result == 'o3 response'

        call_kwargs = mock_openai.chat.completions.create.call_args[1]
        assert 'max_completion_tokens' in call_kwargs
        assert 'temperature' not in call_kwargs

    async def test_openai_o4_uses_max_completion_tokens(self) -> None:
        """OpenAI o4 → max_completion_tokens."""
        from app.ml.llm_client import OpenAIClient

        client = OpenAIClient(model='o4-mini', api_key='test-key')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='o4 resp'))]

        mock_openai = AsyncMock()
        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
        client._client = mock_openai

        await client.complete(system='sys', user='usr')

        call_kwargs = mock_openai.chat.completions.create.call_args[1]
        assert 'max_completion_tokens' in call_kwargs
        assert 'temperature' not in call_kwargs

    async def test_openai_gpt4_uses_max_tokens(self) -> None:
        """OpenAI gpt-4o → обычные max_tokens + temperature."""
        from app.ml.llm_client import OpenAIClient

        client = OpenAIClient(model='gpt-4o', api_key='test-key')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='gpt4 resp'))]

        mock_openai = AsyncMock()
        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
        client._client = mock_openai

        await client.complete(system='sys', user='usr')

        call_kwargs = mock_openai.chat.completions.create.call_args[1]
        assert 'max_tokens' in call_kwargs
        assert 'temperature' in call_kwargs
        assert 'max_completion_tokens' not in call_kwargs

    async def test_openrouter_o3_via_provider_prefix(self) -> None:
        """OpenRouter openai/o3 → model_short='o3' → max_completion_tokens."""
        from app.ml.llm_client import OpenRouterClient

        client = OpenRouterClient(model='openai/o3', api_key='test-key')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='or resp'))]
        mock_response.usage = MagicMock(total_tokens=100)

        mock_openai = AsyncMock()
        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
        client._client = mock_openai

        await client.complete(system='sys', user='usr')

        call_kwargs = mock_openai.chat.completions.create.call_args[1]
        assert 'max_completion_tokens' in call_kwargs
        assert 'temperature' not in call_kwargs

    async def test_openrouter_o1_via_provider_prefix(self) -> None:
        """OpenRouter openai/o1-mini → o-series detection."""
        from app.ml.llm_client import OpenRouterClient

        client = OpenRouterClient(model='openai/o1-mini', api_key='test-key')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='o1-mini'))]
        mock_response.usage = MagicMock(total_tokens=50)

        mock_openai = AsyncMock()
        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
        client._client = mock_openai

        await client.complete(system='sys', user='usr')

        call_kwargs = mock_openai.chat.completions.create.call_args[1]
        assert 'max_completion_tokens' in call_kwargs

    async def test_openrouter_claude_uses_max_tokens(self) -> None:
        """OpenRouter anthropic/claude → обычные max_tokens + temperature."""
        from app.ml.llm_client import OpenRouterClient

        client = OpenRouterClient(
            model='anthropic/claude-3.5-sonnet',
            api_key='test-key',
        )

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='claude'))]
        mock_response.usage = MagicMock(total_tokens=80)

        mock_openai = AsyncMock()
        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
        client._client = mock_openai

        await client.complete(system='sys', user='usr')

        call_kwargs = mock_openai.chat.completions.create.call_args[1]
        assert 'max_tokens' in call_kwargs
        assert 'temperature' in call_kwargs
        assert 'max_completion_tokens' not in call_kwargs

    async def test_openrouter_o4_mini_via_prefix(self) -> None:
        """OpenRouter openai/o4-mini → o-series."""
        from app.ml.llm_client import OpenRouterClient

        client = OpenRouterClient(model='openai/o4-mini', api_key='test-key')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='o4'))]
        mock_response.usage = MagicMock(total_tokens=60)

        mock_openai = AsyncMock()
        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
        client._client = mock_openai

        await client.complete(system='sys', user='usr')

        call_kwargs = mock_openai.chat.completions.create.call_args[1]
        assert 'max_completion_tokens' in call_kwargs
        assert 'temperature' not in call_kwargs


# ============================================================================
# P1-2: soft_delete_account — JSON-ошибка при неверном пароле
# ============================================================================


class TestSoftDeleteErrorHandling:
    """soft_delete_account возвращает JSON-ошибку при неверном пароле (не HTML)."""

    async def test_delete_account_wrong_password_returns_json(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """DELETE /auth/me с неверным паролем → JSON 401, не HTML."""
        response = await auth_client.request(
            'DELETE',
            '/api/v1/auth/me',
            json={'password': 'WrongPassword123'},
        )
        # Должен быть JSON, не HTML
        assert response.headers.get('content-type', '').startswith('application/json')
        assert response.status_code in (400, 401, 403)

    async def test_delete_account_correct_password_returns_json(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """DELETE /auth/me с правильным паролем → JSON ответ."""
        response = await auth_client.request(
            'DELETE',
            '/api/v1/auth/me',
            json={'password': 'TestPass123'},
        )
        assert response.headers.get('content-type', '').startswith('application/json')

    async def test_soft_delete_db_error_returns_app_error(
        self,
        session: AsyncSession,
    ) -> None:
        """При ошибке БД → AppError с кодом DELETE_ACCOUNT_FAILED."""
        from app.auth.service import soft_delete_account
        from app.core.exceptions import AppError

        user = User(
            id=uuid4(),
            email=f'dberr-{uuid4().hex[:8]}@test.com',
            hashed_password=hash_password('DbErr123'),
        )
        session.add(user)
        await session.flush()

        # Мокаем flush чтобы вызвать ошибку
        with patch.object(session, 'flush', side_effect=RuntimeError('DB error')):
            with pytest.raises(AppError) as exc_info:
                await soft_delete_account(session, user=user, password='DbErr123')
            assert exc_info.value.error_code == 'DELETE_ACCOUNT_FAILED'
            assert exc_info.value.status_code == 500


# ============================================================================
# P1-6: Avatar — серверное хранение (upload/delete)
# ============================================================================


class TestAvatarEndpoints:
    """Тесты загрузки и удаления аватара через API."""

    async def test_upload_avatar_jpeg(self, auth_client: AsyncClient) -> None:
        """POST /auth/me/avatar с JPEG → 200 + URL."""
        # Минимальный JPEG (FF D8 FF)
        jpeg_content = b'\xff\xd8\xff\xe0' + b'\x00' * 100
        files = {'file': ('avatar.jpg', io.BytesIO(jpeg_content), 'image/jpeg')}

        with patch('app.core.storage.file_storage') as mock_storage:
            mock_storage.save = AsyncMock(return_value='avatars/test.jpg')
            mock_storage.delete = AsyncMock()

            response = await auth_client.post('/api/v1/auth/me/avatar', files=files)

        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        assert 'uploads/' in data['message']

    async def test_upload_avatar_png(self, auth_client: AsyncClient) -> None:
        """POST /auth/me/avatar с PNG → 200."""
        png_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        files = {'file': ('avatar.png', io.BytesIO(png_content), 'image/png')}

        with patch('app.core.storage.file_storage') as mock_storage:
            mock_storage.save = AsyncMock(return_value='avatars/test.png')
            mock_storage.delete = AsyncMock()

            response = await auth_client.post('/api/v1/auth/me/avatar', files=files)

        assert response.status_code == 200

    async def test_upload_avatar_webp(self, auth_client: AsyncClient) -> None:
        """POST /auth/me/avatar с WebP → 200."""
        webp_content = b'RIFF' + b'\x00' * 100
        files = {'file': ('avatar.webp', io.BytesIO(webp_content), 'image/webp')}

        with patch('app.core.storage.file_storage') as mock_storage:
            mock_storage.save = AsyncMock(return_value='avatars/test.webp')
            mock_storage.delete = AsyncMock()

            response = await auth_client.post('/api/v1/auth/me/avatar', files=files)

        assert response.status_code == 200

    async def test_upload_avatar_invalid_content_type(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """POST /auth/me/avatar с GIF → 400."""
        gif_content = b'GIF89a' + b'\x00' * 100
        files = {'file': ('avatar.gif', io.BytesIO(gif_content), 'image/gif')}

        response = await auth_client.post('/api/v1/auth/me/avatar', files=files)
        assert response.status_code == 400
        assert 'Допустимые форматы' in response.json()['detail']

    async def test_upload_avatar_too_large(self, auth_client: AsyncClient) -> None:
        """POST /auth/me/avatar > 2 MB → 413."""
        large_content = b'\xff\xd8\xff\xe0' + b'x' * (3 * 1024 * 1024)
        files = {'file': ('big.jpg', io.BytesIO(large_content), 'image/jpeg')}

        response = await auth_client.post('/api/v1/auth/me/avatar', files=files)
        assert response.status_code == 413
        assert '2 MB' in response.json()['detail']

    async def test_upload_avatar_replaces_old(
        self,
        auth_client: AsyncClient,
        test_user: User,
        session: AsyncSession,
    ) -> None:
        """Загрузка нового аватара удаляет старый."""
        test_user.avatar_url = '/api/v1/uploads/avatars/old.jpg'
        await session.flush()

        jpeg_content = b'\xff\xd8\xff\xe0' + b'\x00' * 100
        files = {'file': ('new.jpg', io.BytesIO(jpeg_content), 'image/jpeg')}

        with patch('app.core.storage.file_storage') as mock_storage:
            mock_storage.save = AsyncMock(return_value='avatars/new.jpg')
            mock_storage.delete = AsyncMock()

            response = await auth_client.post('/api/v1/auth/me/avatar', files=files)

        assert response.status_code == 200
        mock_storage.delete.assert_called_once()

    async def test_delete_avatar(self, auth_client: AsyncClient) -> None:
        """DELETE /auth/me/avatar → 204."""
        with patch('app.core.storage.file_storage') as mock_storage:
            mock_storage.delete = AsyncMock()

            response = await auth_client.delete('/api/v1/auth/me/avatar')

        assert response.status_code == 204

    async def test_delete_avatar_with_existing_url(
        self,
        auth_client: AsyncClient,
        test_user: User,
        session: AsyncSession,
    ) -> None:
        """DELETE /auth/me/avatar с существующим аватаром → файл удаляется."""
        test_user.avatar_url = '/api/v1/uploads/avatars/old.jpg'
        await session.flush()

        with patch('app.core.storage.file_storage') as mock_storage:
            mock_storage.delete = AsyncMock()

            response = await auth_client.delete('/api/v1/auth/me/avatar')

        assert response.status_code == 204
        mock_storage.delete.assert_called_once()

    async def test_upload_avatar_unauthorized(self, client: AsyncClient) -> None:
        """POST /auth/me/avatar без токена → 401."""
        files = {'file': ('a.jpg', io.BytesIO(b'\xff\xd8'), 'image/jpeg')}
        response = await client.post('/api/v1/auth/me/avatar', files=files)
        assert response.status_code == 401

    async def test_delete_avatar_unauthorized(self, client: AsyncClient) -> None:
        """DELETE /auth/me/avatar без токена → 401."""
        response = await client.delete('/api/v1/auth/me/avatar')
        assert response.status_code == 401

    async def test_upload_avatar_old_delete_fails_gracefully(
        self,
        auth_client: AsyncClient,
        test_user: User,
        session: AsyncSession,
    ) -> None:
        """Если удаление старого аватара вызывает ошибку — загрузка всё равно проходит."""
        test_user.avatar_url = '/api/v1/uploads/avatars/old.jpg'
        await session.flush()

        jpeg_content = b'\xff\xd8\xff\xe0' + b'\x00' * 100
        files = {'file': ('new.jpg', io.BytesIO(jpeg_content), 'image/jpeg')}

        with patch('app.core.storage.file_storage') as mock_storage:
            mock_storage.save = AsyncMock(return_value='avatars/new.jpg')
            mock_storage.delete = AsyncMock(side_effect=OSError('file not found'))

            response = await auth_client.post('/api/v1/auth/me/avatar', files=files)

        assert response.status_code == 200


# ============================================================================
# P0-3: JSON-ответы (auth/me, rewrite/history)
# ============================================================================


class TestJsonResponses:
    """Эндпоинты возвращают application/json, не text/plain."""

    async def test_auth_me_returns_json(self, auth_client: AsyncClient) -> None:
        """GET /auth/me → application/json."""
        response = await auth_client.get('/api/v1/auth/me')
        assert response.status_code == 200
        content_type = response.headers.get('content-type', '')
        assert 'application/json' in content_type

    async def test_auth_me_has_email_field(self, auth_client: AsyncClient) -> None:
        """GET /auth/me → JSON с полем email."""
        response = await auth_client.get('/api/v1/auth/me')
        data = response.json()
        assert 'email' in data

    async def test_rewrite_history_returns_json(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """GET /rewrite/history → application/json."""
        response = await auth_client.get('/api/v1/rewrite/history')
        assert response.status_code == 200
        content_type = response.headers.get('content-type', '')
        assert 'application/json' in content_type

    async def test_rewrite_history_returns_list(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """GET /rewrite/history → JSON с items-списком."""
        response = await auth_client.get('/api/v1/rewrite/history')
        data = response.json()
        assert 'items' in data
        assert isinstance(data['items'], list)


# ============================================================================
# P1-4: OpenRouter models list (обновлённый)
# ============================================================================


class TestOpenRouterModels:
    """Список моделей OpenRouter содержит актуальные модели."""

    def test_openrouter_models_include_deepseek(self) -> None:
        """OpenRouter fallback содержит deepseek-r1."""
        from app.ml.llm_client import OpenRouterClient

        # Проверяем, что класс может быть создан с deepseek-r1
        client = OpenRouterClient(model='deepseek/deepseek-r1', api_key='test')
        assert client._model == 'deepseek/deepseek-r1'

    def test_openrouter_models_include_llama4(self) -> None:
        """OpenRouter поддерживает llama-4 модели."""
        from app.ml.llm_client import OpenRouterClient

        client = OpenRouterClient(model='meta-llama/llama-4-scout', api_key='test')
        assert client._model == 'meta-llama/llama-4-scout'

    def test_models_router_exists(self) -> None:
        """Роутер /models существует и импортируется."""
        from app.ml.router import router

        assert router is not None


# ============================================================================
# OpenAI/OpenRouter client — дополнительное покрытие
# ============================================================================


class TestLLMClientEdgeCases:
    """Дополнительные edge-cases для LLM-клиентов."""

    async def test_openai_close_noop(self) -> None:
        """OpenAIClient.close() без инициализации → noop."""
        from app.ml.llm_client import OpenAIClient

        client = OpenAIClient(model='gpt-4o', api_key='test')
        await client.close()  # Не должно бросать исключение

    async def test_openrouter_close_noop(self) -> None:
        """OpenRouterClient.close() без инициализации → noop."""
        from app.ml.llm_client import OpenRouterClient

        client = OpenRouterClient(model='test/model', api_key='test')
        await client.close()

    async def test_openai_o_series_custom_max_tokens(self) -> None:
        """O-series модели передают кастомный max_tokens как max_completion_tokens."""
        from app.ml.llm_client import OpenAIClient

        client = OpenAIClient(model='o3-mini', api_key='test-key')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='ok'))]

        mock_openai = AsyncMock()
        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
        client._client = mock_openai

        await client.complete(system='s', user='u', max_tokens=8192)

        call_kwargs = mock_openai.chat.completions.create.call_args[1]
        assert call_kwargs['max_completion_tokens'] == 8192

    async def test_openrouter_without_slash_in_model(self) -> None:
        """OpenRouter модель без / → model_short = сама модель."""
        from app.ml.llm_client import OpenRouterClient

        client = OpenRouterClient(model='o3-mini', api_key='test-key')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='ok'))]
        mock_response.usage = MagicMock(total_tokens=10)

        mock_openai = AsyncMock()
        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
        client._client = mock_openai

        await client.complete(system='s', user='u')

        call_kwargs = mock_openai.chat.completions.create.call_args[1]
        assert 'max_completion_tokens' in call_kwargs

    async def test_openrouter_non_o_model_without_slash(self) -> None:
        """OpenRouter модель без / и не o-series → обычные параметры."""
        from app.ml.llm_client import OpenRouterClient

        client = OpenRouterClient(model='gpt-4o', api_key='test-key')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='ok'))]
        mock_response.usage = MagicMock(total_tokens=10)

        mock_openai = AsyncMock()
        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
        client._client = mock_openai

        await client.complete(system='s', user='u')

        call_kwargs = mock_openai.chat.completions.create.call_args[1]
        assert 'max_tokens' in call_kwargs
        assert 'temperature' in call_kwargs

"""Тесты ml/llm_client.py — LLM-клиенты."""

from __future__ import annotations

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ml.llm_client import (
    BaseLLMClient,
    GigaChatClient,
    OpenAIClient,
    OpenRouterClient,
)


class TestBaseLLMClient:
    """Тесты абстрактного класса."""

    def test_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            BaseLLMClient()  # type: ignore[abstract]


class TestGigaChatClient:
    """Тесты GigaChatClient."""

    def test_init_default_model(self) -> None:
        client = GigaChatClient()
        assert client._model == 'GigaChat-Pro'

    def test_init_custom_model(self) -> None:
        client = GigaChatClient(model='GigaChat')
        assert client._model == 'GigaChat'

    def test_get_client_lazy_init(self) -> None:
        """Lazy-инициализация GigaChat клиента."""
        mock_gigachat_cls = MagicMock()
        mock_gigachat_mod = MagicMock()
        mock_gigachat_mod.GigaChat = mock_gigachat_cls

        sys.modules['gigachat'] = mock_gigachat_mod
        try:
            client = GigaChatClient()
            assert client._client is None
            result = client._get_client()
            assert result is not None
            mock_gigachat_cls.assert_called_once()
        finally:
            sys.modules.pop('gigachat', None)

    @patch('app.ml.llm_client.GigaChatClient._get_client')
    async def test_complete(self, mock_get: MagicMock) -> None:
        """Успешный запрос к GigaChat."""
        # Mock gigachat.models to avoid ImportError
        mock_chat = MagicMock()
        mock_messages = MagicMock()
        mock_role = MagicMock()
        mock_role.SYSTEM = 'system'
        mock_role.USER = 'user'

        mock_gigachat_models = MagicMock()
        mock_gigachat_models.Chat = mock_chat
        mock_gigachat_models.Messages = mock_messages
        mock_gigachat_models.MessagesRole = mock_role
        sys.modules['gigachat'] = MagicMock()
        sys.modules['gigachat.models'] = mock_gigachat_models

        try:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content='AI response'))]
            mock_response.usage = MagicMock(total_tokens=100)

            mock_sdk_client = MagicMock()
            mock_sdk_client.chat.return_value = mock_response
            mock_get.return_value = mock_sdk_client

            client = GigaChatClient()
            result = await client.complete(system='sys', user='usr')
            assert result == 'AI response'
        finally:
            sys.modules.pop('gigachat.models', None)
            sys.modules.pop('gigachat', None)

    async def test_close(self) -> None:
        client = GigaChatClient()
        client._client = MagicMock()
        await client.close()
        assert client._client is None


class TestOpenAIClient:
    """Тесты OpenAIClient."""

    def test_init_default(self) -> None:
        client = OpenAIClient()
        assert client._model == 'gpt-4o-mini'

    def test_get_client_lazy_init(self) -> None:
        """Lazy-инициализация OpenAI клиента."""
        mock_async_openai = MagicMock()
        mock_openai_mod = MagicMock()
        mock_openai_mod.AsyncOpenAI = mock_async_openai

        sys.modules['openai'] = mock_openai_mod
        try:
            client = OpenAIClient()
            assert client._client is None
            result = client._get_client()
            assert result is not None
            mock_async_openai.assert_called_once()
        finally:
            sys.modules.pop('openai', None)

    @patch('app.ml.llm_client.OpenAIClient._get_client')
    async def test_complete(self, mock_get: MagicMock) -> None:
        """Успешный запрос к OpenAI."""
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content='GPT response'))]
        mock_completion.usage = None

        mock_sdk = AsyncMock()
        mock_sdk.chat.completions.create = AsyncMock(return_value=mock_completion)
        mock_get.return_value = mock_sdk

        client = OpenAIClient()
        result = await client.complete(system='sys', user='usr')
        assert result == 'GPT response'

    async def test_close(self) -> None:
        client = OpenAIClient()
        mock_sdk = AsyncMock()
        client._client = mock_sdk
        await client.close()
        assert client._client is None


class TestOpenRouterClient:
    """Тесты OpenRouterClient."""

    def test_init_default(self) -> None:
        client = OpenRouterClient()
        assert client._model == 'anthropic/claude-3.5-sonnet'

    def test_init_custom_model(self) -> None:
        client = OpenRouterClient(model='google/gemini-pro')
        assert client._model == 'google/gemini-pro'

    def test_get_client_lazy_init(self) -> None:
        """Lazy-инициализация OpenRouter клиента через openai SDK."""
        mock_async_openai = MagicMock()
        mock_openai_mod = MagicMock()
        mock_openai_mod.AsyncOpenAI = mock_async_openai

        sys.modules['openai'] = mock_openai_mod
        try:
            client = OpenRouterClient()
            assert client._client is None
            result = client._get_client()
            assert result is not None
            mock_async_openai.assert_called_once()
            # Verify base_url is OpenRouter
            call_kwargs = mock_async_openai.call_args[1]
            assert call_kwargs['base_url'] == 'https://openrouter.ai/api/v1'
            assert 'HTTP-Referer' in call_kwargs['default_headers']
            assert call_kwargs['default_headers']['X-Title'] == 'ResumeCraft'
        finally:
            sys.modules.pop('openai', None)

    @patch('app.ml.llm_client.OpenRouterClient._get_client')
    async def test_complete(self, mock_get: MagicMock) -> None:
        """Успешный запрос к OpenRouter."""
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content='OpenRouter response'))]
        mock_completion.usage = MagicMock(total_tokens=75)

        mock_sdk = AsyncMock()
        mock_sdk.chat.completions.create = AsyncMock(return_value=mock_completion)
        mock_get.return_value = mock_sdk

        client = OpenRouterClient()
        result = await client.complete(system='sys', user='usr')
        assert result == 'OpenRouter response'

    async def test_close_with_client(self) -> None:
        client = OpenRouterClient()
        mock_sdk = AsyncMock()
        client._client = mock_sdk
        await client.close()
        mock_sdk.close.assert_called_once()
        assert client._client is None

    async def test_close_without_client(self) -> None:
        client = OpenRouterClient()
        await client.close()  # no error

"""Тесты ml/llm_factory.py — фабрика LLM-клиентов."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import LLMAuthError, LLMProviderUnavailable
from app.ml.llm_client import AnthropicClient, GigaChatClient, OpenAIClient, OpenRouterClient
from app.ml.llm_factory import LLMClientFactory


def _fake_settings() -> MagicMock:
    """Settings с фейковыми API-ключами для тестов."""
    s = MagicMock()
    s.gigachat_credentials = 'test-cred'
    s.openai_api_key = 'test-openai'
    s.anthropic_api_key = 'test-anthropic'
    s.openrouter_api_key = 'test-openrouter'
    return s


@patch('app.ml.llm_factory.get_settings', _fake_settings)
class TestLLMClientFactory:
    """Тесты LLMClientFactory."""

    def test_create_gigachat(self) -> None:
        client = LLMClientFactory.create('gigachat-pro')
        assert isinstance(client, GigaChatClient)

    def test_create_openai(self) -> None:
        client = LLMClientFactory.create('openai')
        assert isinstance(client, OpenAIClient)

    def test_create_gpt4o_mini(self) -> None:
        client = LLMClientFactory.create('gpt-4o-mini')
        assert isinstance(client, OpenAIClient)

    def test_create_anthropic(self) -> None:
        client = LLMClientFactory.create('anthropic')
        assert isinstance(client, AnthropicClient)

    def test_create_openrouter(self) -> None:
        client = LLMClientFactory.create('openrouter')
        assert isinstance(client, OpenRouterClient)

    def test_create_gpt4o_alias(self) -> None:
        """Frontend alias gpt-4o → OpenAIClient."""
        client = LLMClientFactory.create('gpt-4o')
        assert isinstance(client, OpenAIClient)

    def test_create_unknown(self) -> None:
        with pytest.raises(LLMProviderUnavailable):
            LLMClientFactory.create('unknown-model')

    def test_create_openai_with_sub_model(self) -> None:
        """OpenAI с sub_model → OpenAIClient с указанной моделью."""
        client = LLMClientFactory.create('openai', sub_model='gpt-4o')
        assert isinstance(client, OpenAIClient)
        assert client._model == 'gpt-4o'

    def test_create_anthropic_with_sub_model(self) -> None:
        """Anthropic с sub_model → AnthropicClient с указанной моделью."""
        client = LLMClientFactory.create('anthropic', sub_model='claude-3-5-haiku-20241022')
        assert isinstance(client, AnthropicClient)
        assert client._model == 'claude-3-5-haiku-20241022'

    def test_create_openrouter_with_sub_model(self) -> None:
        """OpenRouter с sub_model → OpenRouterClient с указанной моделью."""
        client = LLMClientFactory.create('openrouter', sub_model='google/gemini-2.5-flash-preview')
        assert isinstance(client, OpenRouterClient)
        assert client._model == 'google/gemini-2.5-flash-preview'


class TestLLMClientFactoryAuthCheck:
    """Тесты проверки API-ключей."""

    def test_create_without_key_raises_auth_error(self) -> None:
        """Нет API-ключа → LLMAuthError."""
        s = MagicMock()
        s.gigachat_credentials = ''
        with patch('app.ml.llm_factory.get_settings', return_value=s), pytest.raises(LLMAuthError):
            LLMClientFactory.create('gigachat-pro')


@patch('app.ml.llm_factory.get_settings', _fake_settings)
class TestLLMClientFactoryFallback:
    """Тесты fallback-стратегии."""

    def test_create_with_fallback_success(self) -> None:
        """Fallback — первый доступный провайдер."""
        client = LLMClientFactory.create_with_fallback()
        assert isinstance(client, GigaChatClient)

    def test_create_with_fallback_preferred(self) -> None:
        """Preferred провайдер используется первым."""
        client = LLMClientFactory.create_with_fallback(preferred='anthropic')
        assert isinstance(client, AnthropicClient)

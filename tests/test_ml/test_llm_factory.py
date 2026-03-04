"""Тесты ml/llm_factory.py — фабрика LLM-клиентов."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import LLMAuthError, LLMProviderUnavailable
from app.ml.llm_client import GigaChatClient, GroqClient, OpenAIClient, OpenRouterClient
from app.ml.llm_factory import LLMClientFactory


def _fake_settings() -> MagicMock:
    """Settings с фейковыми API-ключами для тестов."""
    s = MagicMock()
    s.gigachat_credentials = 'test-cred'
    s.groq_api_key = 'test-groq'
    s.openai_api_key = 'test-openai'
    s.openrouter_api_key = 'test-openrouter'
    return s


@patch('app.ml.llm_factory.get_settings', _fake_settings)
class TestLLMClientFactory:
    """Тесты LLMClientFactory."""

    def test_create_gigachat(self) -> None:
        client = LLMClientFactory.create('gigachat-pro')
        assert isinstance(client, GigaChatClient)

    def test_create_groq(self) -> None:
        client = LLMClientFactory.create('groq')
        assert isinstance(client, GroqClient)

    def test_create_openai(self) -> None:
        client = LLMClientFactory.create('openai')
        assert isinstance(client, OpenAIClient)

    def test_create_gpt4o_mini(self) -> None:
        client = LLMClientFactory.create('gpt-4o-mini')
        assert isinstance(client, OpenAIClient)

    def test_create_llama(self) -> None:
        client = LLMClientFactory.create('llama-3.3-70b')
        assert isinstance(client, GroqClient)

    def test_create_openrouter(self) -> None:
        client = LLMClientFactory.create('openrouter')
        assert isinstance(client, OpenRouterClient)

    def test_create_gpt4o_alias(self) -> None:
        """Frontend alias gpt-4o → OpenAIClient."""
        client = LLMClientFactory.create('gpt-4o')
        assert isinstance(client, OpenAIClient)

    def test_create_llama_short_alias(self) -> None:
        """Frontend alias llama-3-70b → GroqClient."""
        client = LLMClientFactory.create('llama-3-70b')
        assert isinstance(client, GroqClient)

    def test_create_unknown(self) -> None:
        with pytest.raises(LLMProviderUnavailable):
            LLMClientFactory.create('unknown-model')


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
        client = LLMClientFactory.create_with_fallback(preferred='groq')
        assert isinstance(client, GroqClient)

"""Тесты ml/llm_factory.py — фабрика LLM-клиентов."""

from __future__ import annotations

import pytest

from app.core.exceptions import LLMProviderUnavailable
from app.ml.llm_client import GigaChatClient, GroqClient, OpenAIClient, OpenRouterClient
from app.ml.llm_factory import LLMClientFactory


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

    def test_create_unknown(self) -> None:
        with pytest.raises(LLMProviderUnavailable):
            LLMClientFactory.create('unknown-model')

    async def test_create_with_fallback_success(self) -> None:
        """Fallback — первый доступный провайдер."""
        client = await LLMClientFactory.create_with_fallback()
        assert isinstance(client, GigaChatClient)

    async def test_create_with_fallback_all_fail(self) -> None:
        """Все провайдеры недоступны → LLMProviderUnavailable."""
        from unittest.mock import patch

        with patch.object(
            LLMClientFactory, 'create', side_effect=RuntimeError('unavailable'),
        ), pytest.raises(LLMProviderUnavailable):
            await LLMClientFactory.create_with_fallback()

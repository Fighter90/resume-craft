"""Фабрика LLM-клиентов (Strategy Pattern)."""

from __future__ import annotations

import logging

from app.core.exceptions import LLMProviderUnavailable
from app.ml.llm_client import (
    BaseLLMClient,
    GigaChatClient,
    GroqClient,
    OpenAIClient,
    OpenRouterClient,
)

logger = logging.getLogger(__name__)

# Маппинг имён моделей → классы клиентов
_PROVIDERS: dict[str, type[BaseLLMClient]] = {
    'gigachat-pro': GigaChatClient,
    'gigachat-lite': GigaChatClient,
    'groq': GroqClient,
    'llama-3.3-70b': GroqClient,
    'openai': OpenAIClient,
    'gpt-4o-mini': OpenAIClient,
    'openrouter': OpenRouterClient,
}

# Модели по умолчанию для каждого класса
_MODEL_NAMES: dict[str, str] = {
    'gigachat-pro': 'GigaChat-Pro',
    'gigachat-lite': 'GigaChat',
    'groq': 'llama-3.3-70b-versatile',
    'llama-3.3-70b': 'llama-3.3-70b-versatile',
    'openai': 'gpt-4o-mini',
    'gpt-4o-mini': 'gpt-4o-mini',
    'openrouter': 'anthropic/claude-3.5-sonnet',
}

# Порядок fallback
FALLBACK_ORDER: list[str] = ['gigachat-pro', 'groq', 'openrouter', 'openai']


class LLMClientFactory:
    """Фабрика для создания LLM-клиентов.

    Usage:
        client = LLMClientFactory.create('gigachat-pro')
        response = await client.complete(system='...', user='...')
        await client.close()
    """

    @staticmethod
    def create(provider_name: str) -> BaseLLMClient:
        """Создание LLM-клиента по имени провайдера.

        Args:
            provider_name: Имя провайдера ('gigachat-pro', 'groq', 'openai').

        Returns:
            Экземпляр LLM-клиента.

        Raises:
            LLMProviderUnavailable: неизвестный провайдер.
        """
        provider_class = _PROVIDERS.get(provider_name)
        if not provider_class:
            raise LLMProviderUnavailable(provider_name)

        model_name = _MODEL_NAMES.get(provider_name, provider_name)
        logger.info('Creating LLM client: %s (model=%s)', provider_name, model_name)
        return provider_class(model=model_name)  # type: ignore[call-arg]

    @staticmethod
    async def create_with_fallback() -> BaseLLMClient:
        """Создание клиента с автоматическим fallback.

        Порядок: GigaChat Pro → Groq/Llama 3.3 → OpenAI GPT-4o-mini

        Raises:
            LLMProviderUnavailable: все провайдеры недоступны.
        """
        for provider_name in FALLBACK_ORDER:
            try:
                client = LLMClientFactory.create(provider_name)
                logger.info('Using LLM provider: %s', provider_name)
                return client
            except Exception:
                logger.warning('LLM provider %s unavailable, trying next', provider_name)
                continue

        raise LLMProviderUnavailable('all')

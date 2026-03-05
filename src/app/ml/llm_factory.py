"""Фабрика LLM-клиентов (Strategy Pattern)."""

from __future__ import annotations

import logging

from app.core.config import get_settings
from app.core.exceptions import LLMProviderUnavailable
from app.ml.llm_client import (
    AnthropicClient,
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
    'llama-3-70b': GroqClient,
    'openai': OpenAIClient,
    'gpt-4o-mini': OpenAIClient,
    'gpt-4o': OpenAIClient,
    'anthropic': AnthropicClient,
    'claude-sonnet': AnthropicClient,
    'claude-haiku': AnthropicClient,
    'openrouter': OpenRouterClient,
}

# Модели по умолчанию для каждого класса
_MODEL_NAMES: dict[str, str] = {
    'gigachat-pro': 'GigaChat-Pro',
    'gigachat-lite': 'GigaChat',
    'groq': 'llama-3.3-70b-versatile',
    'llama-3.3-70b': 'llama-3.3-70b-versatile',
    'llama-3-70b': 'llama-3.3-70b-versatile',
    'openai': 'gpt-4o-mini',
    'gpt-4o-mini': 'gpt-4o-mini',
    'gpt-4o': 'gpt-4o',
    'anthropic': 'claude-sonnet-4-20250514',
    'claude-sonnet': 'claude-sonnet-4-20250514',
    'claude-haiku': 'claude-3-5-haiku-20241022',
    'openrouter': 'anthropic/claude-3.5-sonnet',
}

# Маппинг провайдера → поле API-ключа в Settings
_PROVIDER_KEY_FIELDS: dict[str, str] = {
    'gigachat-pro': 'gigachat_credentials',
    'gigachat-lite': 'gigachat_credentials',
    'groq': 'groq_api_key',
    'llama-3.3-70b': 'groq_api_key',
    'llama-3-70b': 'groq_api_key',
    'openai': 'openai_api_key',
    'gpt-4o-mini': 'openai_api_key',
    'gpt-4o': 'openai_api_key',
    'anthropic': 'anthropic_api_key',
    'claude-sonnet': 'anthropic_api_key',
    'claude-haiku': 'anthropic_api_key',
    'openrouter': 'openrouter_api_key',
}

# Популярные модели OpenRouter
OPENROUTER_MODELS: list[dict[str, str]] = [
    {'id': 'anthropic/claude-sonnet-4', 'name': 'Claude Sonnet 4', 'provider': 'Anthropic'},
    {'id': 'anthropic/claude-3.5-sonnet', 'name': 'Claude 3.5 Sonnet', 'provider': 'Anthropic'},
    {'id': 'google/gemini-2.5-flash-preview', 'name': 'Gemini 2.5 Flash', 'provider': 'Google'},
    {'id': 'google/gemini-2.0-flash-001', 'name': 'Gemini 2.0 Flash', 'provider': 'Google'},
    {'id': 'deepseek/deepseek-chat-v3-0324', 'name': 'DeepSeek V3', 'provider': 'DeepSeek'},
    {'id': 'deepseek/deepseek-r1', 'name': 'DeepSeek R1', 'provider': 'DeepSeek'},
    {'id': 'mistralai/mistral-large-2411', 'name': 'Mistral Large', 'provider': 'Mistral'},
    {'id': 'qwen/qwen-2.5-72b-instruct', 'name': 'Qwen 2.5 72B', 'provider': 'Qwen'},
    {'id': 'meta-llama/llama-3.3-70b-instruct', 'name': 'Llama 3.3 70B', 'provider': 'Meta'},
]

# Порядок fallback
FALLBACK_ORDER: list[str] = ['gigachat-pro', 'groq', 'anthropic', 'openrouter', 'openai']


class LLMClientFactory:
    """Фабрика для создания LLM-клиентов.

    Usage:
        client = LLMClientFactory.create('gigachat-pro')
        response = await client.complete(system='...', user='...')
        await client.close()
    """

    @staticmethod
    def create(
        provider_name: str,
        *,
        openrouter_model: str | None = None,
    ) -> BaseLLMClient:
        """Создание LLM-клиента по имени провайдера.

        Args:
            provider_name: Имя провайдера ('gigachat-pro', 'groq', 'openai', 'openrouter').
            openrouter_model: Модель OpenRouter (напр. 'anthropic/claude-3.5-sonnet').

        Returns:
            Экземпляр LLM-клиента.

        Raises:
            LLMProviderUnavailable: неизвестный провайдер или не настроен API-ключ.
        """
        provider_class = _PROVIDERS.get(provider_name)
        if not provider_class:
            raise LLMProviderUnavailable(provider_name)

        # Проверка наличия API-ключа
        key_field = _PROVIDER_KEY_FIELDS.get(provider_name)
        if key_field:
            settings = get_settings()
            key_value = getattr(settings, key_field, '')
            if not key_value or not key_value.strip():
                from app.core.exceptions import LLMAuthError

                raise LLMAuthError(provider_name)

        # Подмодель OpenRouter
        if provider_name == 'openrouter' and openrouter_model:
            model_name = openrouter_model
        else:
            model_name = _MODEL_NAMES.get(provider_name, provider_name)

        logger.info('Creating LLM client: %s (model=%s)', provider_name, model_name)
        return provider_class(model=model_name)  # type: ignore[call-arg]

    @staticmethod
    def create_with_fallback(
        *,
        preferred: str | None = None,
        openrouter_model: str | None = None,
    ) -> BaseLLMClient:
        """Создание клиента с автоматическим fallback.

        Порядок: preferred → GigaChat Pro → Groq → OpenRouter → OpenAI.
        Пропускает провайдеров без настроенных ключей.

        Raises:
            LLMProviderUnavailable: все провайдеры недоступны.
        """
        order = list(FALLBACK_ORDER)
        if preferred and preferred in order:
            order.remove(preferred)
            order.insert(0, preferred)
        elif preferred:
            order.insert(0, preferred)

        for provider_name in order:
            try:
                client = LLMClientFactory.create(
                    provider_name,
                    openrouter_model=openrouter_model if provider_name == 'openrouter' else None,
                )
                logger.info('Using LLM provider: %s', provider_name)
                return client
            except Exception:
                logger.warning('LLM provider %s unavailable, trying next', provider_name)
                continue

        raise LLMProviderUnavailable('all')

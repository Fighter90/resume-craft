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
    'openai': OpenAIClient,
    'gpt-4o-mini': OpenAIClient,
    'gpt-4o': OpenAIClient,
    'anthropic': AnthropicClient,
    'claude-sonnet': AnthropicClient,
    'claude-haiku': AnthropicClient,
    'openrouter': OpenRouterClient,
    'groq': GroqClient,
}

# Модели по умолчанию для каждого класса
_MODEL_NAMES: dict[str, str] = {
    'gigachat-pro': 'GigaChat-Pro',
    'gigachat-lite': 'GigaChat',
    'openai': 'gpt-4o-mini',
    'gpt-4o-mini': 'gpt-4o-mini',
    'gpt-4o': 'gpt-4o',
    'anthropic': 'claude-sonnet-4-20250514',
    'claude-sonnet': 'claude-sonnet-4-20250514',
    'claude-haiku': 'claude-3-5-haiku-20241022',
    'openrouter': 'anthropic/claude-3.5-sonnet',
    'groq': 'llama-3.3-70b-versatile',
}

# Маппинг провайдера → поле API-ключа в Settings
_PROVIDER_KEY_FIELDS: dict[str, str] = {
    'gigachat-pro': 'gigachat_credentials',
    'gigachat-lite': 'gigachat_credentials',
    'openai': 'openai_api_key',
    'gpt-4o-mini': 'openai_api_key',
    'gpt-4o': 'openai_api_key',
    'anthropic': 'anthropic_api_key',
    'claude-sonnet': 'anthropic_api_key',
    'claude-haiku': 'anthropic_api_key',
    'openrouter': 'openrouter_api_key',
    'groq': 'groq_api_key',
}

# Провайдеры с поддержкой выбора подмодели (2-шаговый выбор)
SUB_MODEL_PROVIDERS: frozenset[str] = frozenset({'openai', 'anthropic', 'openrouter', 'groq'})

# Порядок fallback
FALLBACK_ORDER: list[str] = ['gigachat-pro', 'anthropic', 'openrouter', 'groq', 'openai']


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
        sub_model: str | None = None,
        api_key: str | None = None,
    ) -> BaseLLMClient:
        """Создание LLM-клиента по имени провайдера.

        Args:
            provider_name: Имя провайдера ('gigachat-pro', 'openai', 'anthropic', 'openrouter').
            sub_model: Конкретная модель провайдера (напр. 'gpt-4o', 'claude-sonnet-4-20250514').
            api_key: Пользовательский API-ключ (из БД).
                Если не передан — используются env-настройки.

        Returns:
            Экземпляр LLM-клиента.

        Raises:
            LLMProviderUnavailable: неизвестный провайдер или не настроен API-ключ.
        """
        provider_class = _PROVIDERS.get(provider_name)
        if not provider_class:
            raise LLMProviderUnavailable(provider_name)

        # Проверка наличия API-ключа: пользовательский → env
        effective_key = api_key
        if not effective_key or not effective_key.strip():
            key_field = _PROVIDER_KEY_FIELDS.get(provider_name)
            if key_field:
                settings = get_settings()
                env_value = getattr(settings, key_field, '')
                if env_value and env_value.strip():
                    effective_key = env_value
                else:
                    from app.core.exceptions import LLMAuthError

                    raise LLMAuthError(provider_name)

        # Подмодель для провайдеров с 2-шаговым выбором
        if provider_name in SUB_MODEL_PROVIDERS and sub_model:
            model_name = sub_model
        else:
            model_name = _MODEL_NAMES.get(provider_name, provider_name)

        logger.info('Creating LLM client: %s (model=%s)', provider_name, model_name)
        return provider_class(model=model_name, api_key=effective_key)  # type: ignore[call-arg]

    @staticmethod
    def create_with_fallback(
        *,
        preferred: str | None = None,
        sub_model: str | None = None,
        user_keys: dict[str, str] | None = None,
    ) -> BaseLLMClient:
        """Создание клиента с автоматическим fallback.

        Порядок: preferred → GigaChat Pro → Anthropic → OpenRouter → OpenAI.
        Пропускает провайдеров без настроенных ключей.

        Args:
            preferred: Предпочтительный провайдер (ставится первым в очереди).
            sub_model: Подмодель для провайдеров с 2-шаговым выбором.
            user_keys: Словарь {provider_name: api_key} — пользовательские ключи из БД.

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
                # Пользовательский ключ из БД (если есть)
                user_key = (user_keys or {}).get(provider_name, '')
                client = LLMClientFactory.create(
                    provider_name,
                    sub_model=sub_model if provider_name in SUB_MODEL_PROVIDERS else None,
                    api_key=user_key or None,
                )
                logger.info('Using LLM provider: %s', provider_name)
                return client
            except Exception:
                logger.warning('LLM provider %s unavailable, trying next', provider_name)
                continue

        raise LLMProviderUnavailable('all')

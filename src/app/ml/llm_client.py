"""Базовый LLM-клиент и реализации для GigaChat, Groq, OpenAI, OpenRouter."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


def _handle_llm_error(exc: Exception, *, provider: str) -> None:
    """Обработка ошибок LLM-провайдеров → понятные исключения."""
    from app.core.exceptions import LLMAuthError, LLMProviderUnavailable

    err_str = str(exc)
    status_code: int | None = getattr(exc, 'status_code', None)

    # 401 — невалидный ключ
    if status_code == 401 or '401' in err_str or 'Unauthorized' in err_str:
        raise LLMAuthError(provider) from exc

    # 429 — rate limit
    if status_code == 429 or '429' in err_str or 'rate' in err_str.lower():
        raise LLMProviderUnavailable(
            f'{provider} — превышен лимит запросов, попробуйте позже'
        ) from exc

    # 5xx — сервер провайдера
    if status_code and status_code >= 500:
        raise LLMProviderUnavailable(
            f'{provider} — сервер провайдера временно недоступен'
        ) from exc

    # Timeout
    if 'timeout' in err_str.lower() or 'timed out' in err_str.lower():
        raise LLMProviderUnavailable(f'{provider} — таймаут запроса, попробуйте позже') from exc

    # Другая ошибка — пробросим с контекстом
    raise LLMProviderUnavailable(f'{provider}: {err_str[:200]}') from exc


class BaseLLMClient(ABC):
    """Абстрактный базовый класс LLM-клиента (Strategy Pattern)."""

    @abstractmethod
    async def complete(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        """Отправка запроса к LLM и получение ответа.

        Args:
            system: Системный промпт.
            user: Пользовательский промпт.
            temperature: Креативность (0.0 - 1.0).
            max_tokens: Максимальное кол-во токенов в ответе.

        Returns:
            Текстовый ответ LLM.
        """

    @abstractmethod
    async def close(self) -> None:
        """Закрытие клиента и освобождение ресурсов."""


class GigaChatClient(BaseLLMClient):
    """Клиент GigaChat (Сбер) — #1 MERA для русского языка."""

    def __init__(self, model: str = 'GigaChat-Pro') -> None:
        self._model = model
        self._client: Any = None

    def _get_client(self) -> Any:
        """Lazy-инициализация клиента GigaChat."""
        if self._client is None:
            from gigachat import GigaChat

            self._client = GigaChat(
                credentials=settings.gigachat_credentials,
                scope=settings.gigachat_scope,
                model=self._model,
                verify_ssl_certs=False,
            )
        return self._client

    async def complete(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        """Запрос к GigaChat API."""
        from gigachat.models import Chat, Messages, MessagesRole

        client = self._get_client()

        messages = [
            Messages(role=MessagesRole.SYSTEM, content=system),
            Messages(role=MessagesRole.USER, content=user),
        ]

        payload = Chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        try:
            response = client.chat(payload)
        except Exception as exc:
            _handle_llm_error(exc, provider='gigachat-pro')

        content = response.choices[0].message.content

        logger.info(
            'GigaChat response: model=%s, tokens=%s',
            self._model,
            response.usage.total_tokens if response.usage else 'N/A',
        )
        return content  # type: ignore[no-any-return]

    async def close(self) -> None:
        """Закрытие GigaChat клиента."""
        self._client = None


class GroqClient(BaseLLMClient):
    """Клиент Groq (Llama 3.3 70B) — быстрый fallback."""

    def __init__(self, model: str = 'llama-3.3-70b-versatile') -> None:
        self._model = model
        self._client: Any = None

    def _get_client(self) -> Any:
        """Lazy-инициализация Groq через openai SDK."""
        if self._client is None:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(
                api_key=settings.groq_api_key,
                base_url='https://api.groq.com/openai/v1',
            )
        return self._client

    async def complete(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        """Запрос к Groq API."""
        client = self._get_client()

        try:
            response = await client.chat.completions.create(
                model=self._model,
                messages=[
                    {'role': 'system', 'content': system},
                    {'role': 'user', 'content': user},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as exc:
            _handle_llm_error(exc, provider='groq')

        content = response.choices[0].message.content or ''
        logger.info(
            'Groq response: model=%s, tokens=%s',
            self._model,
            response.usage.total_tokens if response.usage else 'N/A',
        )
        return content

    async def close(self) -> None:
        """Закрытие Groq клиента."""
        if self._client:
            await self._client.close()
            self._client = None


class OpenAIClient(BaseLLMClient):
    """Клиент OpenAI GPT-4o-mini — резервный."""

    def __init__(self, model: str = 'gpt-4o-mini') -> None:
        self._model = model
        self._client: Any = None

    def _get_client(self) -> Any:
        """Lazy-инициализация OpenAI клиента."""
        if self._client is None:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._client

    async def complete(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        """Запрос к OpenAI API."""
        client = self._get_client()

        try:
            response = await client.chat.completions.create(
                model=self._model,
                messages=[
                    {'role': 'system', 'content': system},
                    {'role': 'user', 'content': user},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as exc:
            _handle_llm_error(exc, provider='openai')

        content = response.choices[0].message.content or ''
        logger.info('OpenAI response: model=%s', self._model)
        return content

    async def close(self) -> None:
        """Закрытие OpenAI клиента."""
        if self._client:
            await self._client.close()
            self._client = None


class OpenRouterClient(BaseLLMClient):
    """Клиент OpenRouter — доступ к 100+ моделям через единый API."""

    def __init__(self, model: str = 'anthropic/claude-3.5-sonnet') -> None:
        self._model = model
        self._client: Any = None

    def _get_client(self) -> Any:
        """Lazy-инициализация OpenRouter через openai SDK."""
        if self._client is None:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(
                api_key=settings.openrouter_api_key,
                base_url='https://openrouter.ai/api/v1',
                default_headers={
                    'HTTP-Referer': 'https://resumecraft.ru',
                    'X-Title': 'ResumeCraft',
                },
            )
        return self._client

    async def complete(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        """Запрос к OpenRouter API."""
        client = self._get_client()

        try:
            response = await client.chat.completions.create(
                model=self._model,
                messages=[
                    {'role': 'system', 'content': system},
                    {'role': 'user', 'content': user},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as exc:
            _handle_llm_error(exc, provider='openrouter')

        content = response.choices[0].message.content or ''
        logger.info(
            'OpenRouter response: model=%s, tokens=%s',
            self._model,
            response.usage.total_tokens if response.usage else 'N/A',
        )
        return content

    async def close(self) -> None:
        """Закрытие OpenRouter клиента."""
        if self._client:
            await self._client.close()
            self._client = None

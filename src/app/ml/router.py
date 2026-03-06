"""Роутер AI-моделей: /api/v1/models."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.core.dependencies import get_optional_user

if TYPE_CHECKING:
    from app.auth.models import User

router = APIRouter(prefix='/models', tags=['models'])

logger = logging.getLogger(__name__)

# Маппинг провайдера → поле с ключом в Settings
_KEY_FIELDS: dict[str, str] = {
    'gigachat': 'gigachat_credentials',
    'openai': 'openai_api_key',
    'anthropic': 'anthropic_api_key',
    'openrouter': 'openrouter_api_key',
}

# Маппинг имени модели → имя провайдера для БД
_MODEL_TO_PROVIDER: dict[str, str] = {
    'gigachat': 'gigachat',
    'openai': 'openai',
    'anthropic': 'anthropic',
    'openrouter': 'openrouter',
}


async def _get_user_keys(
    session: AsyncSession | None,
    user: User | None,
) -> dict[str, bool]:
    """Проверить наличие пользовательских ключей в БД."""
    user_has: dict[str, bool] = dict.fromkeys(_KEY_FIELDS, False)
    if not user or not session:
        return user_has

    from app.settings.service import get_setting

    for provider in _KEY_FIELDS:
        setting = await get_setting(
            session,
            user_id=user.id,
            category='ai_keys',
            key=provider,
        )
        user_has[provider] = bool(setting and setting.value)

    return user_has


@router.get(
    '',
    summary='Список доступных AI-моделей',
)
async def list_models(
    session: AsyncSession = Depends(get_session),
    current_user: User | None = Depends(get_optional_user),
) -> dict[str, object]:
    """Возвращает модели с флагом доступности.

    Доступность определяется: пользовательский ключ в БД ИЛИ ключ в env-настройках.
    """
    settings = get_settings()

    env_available: dict[str, bool] = {}
    for provider, field in _KEY_FIELDS.items():
        val = getattr(settings, field, '')
        env_available[provider] = bool(val and val.strip())

    # Проверка пользовательских ключей в БД
    user_has = await _get_user_keys(session, current_user)

    available: dict[str, bool] = {}
    for provider in _KEY_FIELDS:
        available[provider] = env_available[provider] or user_has[provider]

    models = [
        {
            'id': 'gigachat-pro',
            'name': 'GigaChat Pro',
            'provider': 'gigachat',
            'available': available['gigachat'],
            'description': '#1 русский язык (MERA), данные в РФ',
            'has_sub_models': True,
        },
        {
            'id': 'openai',
            'name': 'OpenAI',
            'provider': 'openai',
            'available': available['openai'],
            'description': 'GPT-4o, GPT-4o-mini и другие модели OpenAI',
            'has_sub_models': True,
        },
        {
            'id': 'anthropic',
            'name': 'Anthropic Claude',
            'provider': 'anthropic',
            'available': available['anthropic'],
            'description': 'Claude Sonnet 4, Claude Haiku — отличный русский, 200K контекст',
            'has_sub_models': True,
        },
        {
            'id': 'openrouter',
            'name': 'OpenRouter',
            'provider': 'openrouter',
            'available': available['openrouter'],
            'description': '100+ моделей через единый API',
            'has_sub_models': True,
        },
    ]

    return {'models': models}


@router.get(
    '/{provider}/sub-models',
    summary='Получить доступные подмодели провайдера',
)
async def get_sub_models(
    provider: str,
    session: AsyncSession = Depends(get_session),
    current_user: User | None = Depends(get_optional_user),
) -> dict[str, object]:
    """Динамически запрашивает список доступных моделей у провайдера через его API.

    Поддерживаемые провайдеры: openai, anthropic, openrouter.
    Требует настроенного API-ключа (в env или в личных настройках).
    """
    # Получаем пользовательский ключ из БД (если авторизован)
    user_key = ''
    if current_user and session:
        from app.settings.service import get_decrypted_value

        user_key = await get_decrypted_value(
            session,
            user_id=current_user.id,
            category='ai_keys',
            key=provider,
        )

    settings = get_settings()

    if provider == 'gigachat':
        key = user_key or settings.gigachat_credentials
        scope = settings.gigachat_scope
        return await _fetch_gigachat_models(key, scope=scope)
    if provider == 'openai':
        key = user_key or settings.openai_api_key
        return await _fetch_openai_models(key)
    if provider == 'anthropic':
        key = user_key or settings.anthropic_api_key
        return await _fetch_anthropic_models(key)
    if provider == 'openrouter':
        key = user_key or settings.openrouter_api_key
        return await _fetch_openrouter_models(key)

    return {'sub_models': [], 'error': f'Провайдер {provider} не поддерживает выбор подмоделей'}


async def _fetch_gigachat_models(
    credentials: str,
    *,
    scope: str = 'GIGACHAT_API_PERS',
) -> dict[str, Any]:
    """Получение списка моделей GigaChat через SDK."""
    if not credentials or not credentials.strip():
        return {'sub_models': [], 'error': 'API-ключ GigaChat не настроен'}

    try:
        from gigachat import GigaChat

        client = GigaChat(
            credentials=credentials,
            scope=scope,
            verify_ssl_certs=False,
        )
        response = client.get_models()

        models = []
        for m in response.data:
            models.append(
                {
                    'id': m.id,
                    'name': m.id,
                    'provider': 'GigaChat',
                }
            )

        models.sort(key=lambda x: x['name'])
        return {'sub_models': models}

    except Exception as exc:
        logger.warning('Failed to fetch GigaChat models: %s', exc)
        return {
            'sub_models': [
                {'id': 'GigaChat-Pro', 'name': 'GigaChat-Pro', 'provider': 'GigaChat'},
                {'id': 'GigaChat', 'name': 'GigaChat', 'provider': 'GigaChat'},
                {'id': 'GigaChat-Max', 'name': 'GigaChat-Max', 'provider': 'GigaChat'},
            ],
            'fallback': True,
        }


async def _fetch_openai_models(api_key: str) -> dict[str, Any]:
    """Получение списка моделей OpenAI через API."""
    if not api_key or not api_key.strip():
        return {'sub_models': [], 'error': 'API-ключ OpenAI не настроен'}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                'https://api.openai.com/v1/models',
                headers={'Authorization': f'Bearer {api_key}'},
            )
            resp.raise_for_status()
            data = resp.json()

        # Фильтруем только chat-модели GPT
        chat_prefixes = ('gpt-4', 'gpt-3.5', 'o1', 'o3', 'o4')
        exclude_keywords = (
            'instruct',
            'realtime',
            'audio',
            'transcribe',
            'tts',
            'dall-e',
            'whisper',
            'embedding',
            'moderation',
            'search',
        )
        models = []
        for m in data.get('data', []):
            mid = m.get('id', '')
            if any(mid.startswith(p) for p in chat_prefixes) and not any(
                kw in mid for kw in exclude_keywords
            ):
                models.append(
                    {
                        'id': mid,
                        'name': mid,
                        'provider': 'OpenAI',
                    }
                )

        # Сортировка: новые модели первыми
        models.sort(key=lambda x: x['id'], reverse=True)
        return {'sub_models': models}

    except Exception as exc:
        logger.warning('Failed to fetch OpenAI models: %s', exc)
        return {
            'sub_models': [
                {'id': 'gpt-4o', 'name': 'gpt-4o', 'provider': 'OpenAI'},
                {'id': 'gpt-4o-mini', 'name': 'gpt-4o-mini', 'provider': 'OpenAI'},
                {'id': 'gpt-4-turbo', 'name': 'gpt-4-turbo', 'provider': 'OpenAI'},
            ],
            'fallback': True,
        }


async def _fetch_anthropic_models(api_key: str) -> dict[str, Any]:
    """Получение списка моделей Anthropic через API."""
    if not api_key or not api_key.strip():
        return {'sub_models': [], 'error': 'API-ключ Anthropic не настроен'}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                'https://api.anthropic.com/v1/models',
                headers={
                    'x-api-key': api_key,
                    'anthropic-version': '2023-06-01',
                },
            )
            resp.raise_for_status()
            data = resp.json()

        models = []
        for m in data.get('data', []):
            mid = m.get('id', '')
            name = m.get('display_name', mid)
            models.append(
                {
                    'id': mid,
                    'name': name,
                    'provider': 'Anthropic',
                }
            )

        # Сортировка по имени (новые первыми)
        models.sort(key=lambda x: x['id'], reverse=True)
        return {'sub_models': models}

    except Exception as exc:
        logger.warning('Failed to fetch Anthropic models: %s', exc)
        return {
            'sub_models': [
                {
                    'id': 'claude-sonnet-4-20250514',
                    'name': 'Claude Sonnet 4',
                    'provider': 'Anthropic',
                },
                {
                    'id': 'claude-3-5-sonnet-20241022',
                    'name': 'Claude 3.5 Sonnet',
                    'provider': 'Anthropic',
                },
                {
                    'id': 'claude-3-5-haiku-20241022',
                    'name': 'Claude 3.5 Haiku',
                    'provider': 'Anthropic',
                },
            ],
            'fallback': True,
        }


async def _fetch_openrouter_models(api_key: str) -> dict[str, Any]:
    """Получение списка всех доступных моделей OpenRouter через API."""
    if not api_key or not api_key.strip():
        return {'sub_models': [], 'error': 'API-ключ OpenRouter не настроен'}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                'https://openrouter.ai/api/v1/models',
                headers={'Authorization': f'Bearer {api_key}'},
            )
            resp.raise_for_status()
            data = resp.json()

        models = []
        for m in data.get('data', []):
            mid = m.get('id', '')
            name = m.get('name', mid)
            # Извлекаем провайдера из id (формат: provider/model)
            provider = mid.split('/')[0] if '/' in mid else 'Unknown'
            models.append(
                {
                    'id': mid,
                    'name': name,
                    'provider': provider.capitalize(),
                }
            )

        # Сортировка по имени
        models.sort(key=lambda x: x['name'])
        return {'sub_models': models}

    except Exception as exc:
        logger.warning('Failed to fetch OpenRouter models: %s', exc)
        return {
            'sub_models': [
                {
                    'id': 'anthropic/claude-sonnet-4',
                    'name': 'Claude Sonnet 4',
                    'provider': 'Anthropic',
                },
                {
                    'id': 'anthropic/claude-3.5-sonnet',
                    'name': 'Claude 3.5 Sonnet',
                    'provider': 'Anthropic',
                },
                {
                    'id': 'google/gemini-2.5-flash-preview',
                    'name': 'Gemini 2.5 Flash',
                    'provider': 'Google',
                },
                {
                    'id': 'deepseek/deepseek-chat-v3-0324',
                    'name': 'DeepSeek V3',
                    'provider': 'DeepSeek',
                },
                {
                    'id': 'mistralai/mistral-large-2411',
                    'name': 'Mistral Large',
                    'provider': 'Mistral',
                },
            ],
            'fallback': True,
        }

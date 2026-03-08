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
    'groq': 'groq_api_key',
}

# Маппинг имени модели → имя провайдера для БД
_MODEL_TO_PROVIDER: dict[str, str] = {
    'gigachat': 'gigachat',
    'openai': 'openai',
    'anthropic': 'anthropic',
    'openrouter': 'openrouter',
    'groq': 'groq',
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
        {
            'id': 'groq',
            'name': 'Groq',
            'provider': 'groq',
            'available': available['groq'],
            'description': 'Быстрый inference — Llama, Mixtral, Gemma',
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
    # Нормализуем имя провайдера (gigachat-pro → gigachat)
    db_key = provider.split('-')[0] if provider.startswith('gigachat') else provider
    user_key = ''
    if current_user and session:
        from app.settings.service import get_decrypted_value

        user_key = await get_decrypted_value(
            session,
            user_id=current_user.id,
            category='ai_keys',
            key=db_key,
        )

    settings = get_settings()

    # Нормализуем имя провайдера (gigachat-pro → gigachat)
    normalized = provider.split('-')[0] if provider.startswith('gigachat') else provider

    if normalized == 'gigachat':
        key = user_key or settings.gigachat_credentials
        scope = settings.gigachat_scope
        return await _fetch_gigachat_models(key, scope=scope)
    if normalized == 'openai':
        key = user_key or settings.openai_api_key
        return await _fetch_openai_models(key)
    if normalized == 'anthropic':
        key = user_key or settings.anthropic_api_key
        return await _fetch_anthropic_models(key)
    if normalized == 'openrouter':
        key = user_key or settings.openrouter_api_key
        return await _fetch_openrouter_models(key)
    if normalized == 'groq':
        key = user_key or settings.groq_api_key
        return await _fetch_groq_models(key)

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
        chat_prefixes = ('gpt-4', 'gpt-3.5', 'chatgpt', 'o1', 'o3', 'o4')
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
                {'id': 'gpt-4o', 'name': 'GPT-4o', 'provider': 'OpenAI'},
                {'id': 'gpt-4o-mini', 'name': 'GPT-4o Mini', 'provider': 'OpenAI'},
                {'id': 'gpt-4.1', 'name': 'GPT-4.1', 'provider': 'OpenAI'},
                {'id': 'gpt-4.1-mini', 'name': 'GPT-4.1 Mini', 'provider': 'OpenAI'},
                {'id': 'gpt-4.1-nano', 'name': 'GPT-4.1 Nano', 'provider': 'OpenAI'},
                {'id': 'gpt-4-turbo', 'name': 'GPT-4 Turbo', 'provider': 'OpenAI'},
                {'id': 'o3', 'name': 'o3', 'provider': 'OpenAI'},
                {'id': 'o3-mini', 'name': 'o3 Mini', 'provider': 'OpenAI'},
                {'id': 'o4-mini', 'name': 'o4 Mini', 'provider': 'OpenAI'},
                {'id': 'gpt-3.5-turbo', 'name': 'GPT-3.5 Turbo', 'provider': 'OpenAI'},
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
                    'id': 'claude-opus-4-20250514',
                    'name': 'Claude Opus 4',
                    'provider': 'Anthropic',
                },
                {
                    'id': 'claude-3-7-sonnet-20250219',
                    'name': 'Claude 3.7 Sonnet',
                    'provider': 'Anthropic',
                },
                {
                    'id': 'claude-3-5-sonnet-20241022',
                    'name': 'Claude 3.5 Sonnet v2',
                    'provider': 'Anthropic',
                },
                {
                    'id': 'claude-3-5-haiku-20241022',
                    'name': 'Claude 3.5 Haiku',
                    'provider': 'Anthropic',
                },
                {
                    'id': 'claude-3-opus-20240229',
                    'name': 'Claude 3 Opus',
                    'provider': 'Anthropic',
                },
                {
                    'id': 'claude-3-haiku-20240307',
                    'name': 'Claude 3 Haiku',
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
                    'id': 'anthropic/claude-opus-4',
                    'name': 'Claude Opus 4',
                    'provider': 'Anthropic',
                },
                {
                    'id': 'anthropic/claude-3.7-sonnet',
                    'name': 'Claude 3.7 Sonnet',
                    'provider': 'Anthropic',
                },
                {
                    'id': 'google/gemini-2.5-pro-preview',
                    'name': 'Gemini 2.5 Pro',
                    'provider': 'Google',
                },
                {
                    'id': 'google/gemini-2.5-flash',
                    'name': 'Gemini 2.5 Flash',
                    'provider': 'Google',
                },
                {
                    'id': 'google/gemini-2.0-flash-001',
                    'name': 'Gemini 2.0 Flash',
                    'provider': 'Google',
                },
                {
                    'id': 'openai/gpt-4o',
                    'name': 'GPT-4o',
                    'provider': 'Openai',
                },
                {
                    'id': 'openai/gpt-4.1',
                    'name': 'GPT-4.1',
                    'provider': 'Openai',
                },
                {
                    'id': 'mistralai/mistral-large',
                    'name': 'Mistral Large',
                    'provider': 'Mistralai',
                },
                {
                    'id': 'mistralai/mistral-medium',
                    'name': 'Mistral Medium',
                    'provider': 'Mistralai',
                },
                {
                    'id': 'meta-llama/llama-4-maverick',
                    'name': 'Llama 4 Maverick',
                    'provider': 'Meta-llama',
                },
                {
                    'id': 'meta-llama/llama-4-scout',
                    'name': 'Llama 4 Scout',
                    'provider': 'Meta-llama',
                },
                {
                    'id': 'deepseek/deepseek-r1',
                    'name': 'DeepSeek R1',
                    'provider': 'Deepseek',
                },
                {
                    'id': 'deepseek/deepseek-chat-v3-0324',
                    'name': 'DeepSeek V3',
                    'provider': 'Deepseek',
                },
                {
                    'id': 'qwen/qwen3-235b-a22b',
                    'name': 'Qwen3 235B',
                    'provider': 'Qwen',
                },
                {
                    'id': 'x-ai/grok-3-mini-beta',
                    'name': 'Grok 3 Mini',
                    'provider': 'X-ai',
                },
            ],
            'fallback': True,
        }


async def _fetch_groq_models(api_key: str) -> dict[str, Any]:
    """Получение списка моделей Groq через OpenAI-совместимый API."""
    if not api_key or not api_key.strip():
        return {'sub_models': [], 'error': 'API-ключ Groq не настроен'}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                'https://api.groq.com/openai/v1/models',
                headers={'Authorization': f'Bearer {api_key}'},
            )
            resp.raise_for_status()
            data = resp.json()

        # Фильтр: только chat-модели (не whisper, не embedding)
        exclude_keywords = ('whisper', 'distil', 'embed', 'tts', 'guard')
        models = []
        for m in data.get('data', []):
            mid = m.get('id', '')
            if any(kw in mid.lower() for kw in exclude_keywords):
                continue
            models.append(
                {
                    'id': mid,
                    'name': mid,
                    'provider': 'Groq',
                }
            )

        models.sort(key=lambda x: x['name'])
        return {'sub_models': models}

    except Exception as exc:
        logger.warning('Failed to fetch Groq models: %s', exc)
        return {
            'sub_models': [
                {'id': 'llama-3.3-70b-versatile', 'name': 'Llama 3.3 70B', 'provider': 'Groq'},
                {'id': 'llama-3.1-8b-instant', 'name': 'Llama 3.1 8B', 'provider': 'Groq'},
                {'id': 'llama3-70b-8192', 'name': 'Llama 3 70B', 'provider': 'Groq'},
                {'id': 'mixtral-8x7b-32768', 'name': 'Mixtral 8x7B', 'provider': 'Groq'},
                {'id': 'gemma2-9b-it', 'name': 'Gemma 2 9B', 'provider': 'Groq'},
            ],
            'fallback': True,
        }


# ============================================================================
# Health-check: GET /models/health
# ============================================================================


@router.get(
    '/health',
    summary='Проверка доступности AI-провайдеров',
)
async def check_providers_health(
    session: AsyncSession = Depends(get_session),
    current_user: User | None = Depends(get_optional_user),
) -> dict[str, object]:
    """Проверяет доступность каждого провайдера (наличие ключа + пинг API)."""
    settings = get_settings()
    user_has = await _get_user_keys(session, current_user)

    results: dict[str, dict[str, Any]] = {}

    for provider, field in _KEY_FIELDS.items():
        env_val = getattr(settings, field, '')
        has_env = bool(env_val and env_val.strip())
        has_user = user_has.get(provider, False)
        has_key = has_env or has_user

        if not has_key:
            results[provider] = {'status': 'no_key', 'message': 'API-ключ не настроен'}
            continue

        # Get the actual key (prefer user key)
        api_key = ''
        if has_user and current_user and session:
            from app.settings.service import get_decrypted_value

            api_key = await get_decrypted_value(
                session,
                user_id=current_user.id,
                category='ai_keys',
                key=provider,
            )
        if not api_key:
            api_key = env_val

        # Ping provider API
        try:
            if provider == 'gigachat':
                results[provider] = await _ping_gigachat(api_key, scope=settings.gigachat_scope)
            elif provider == 'openai':
                results[provider] = await _ping_openai(api_key)
            elif provider == 'anthropic':
                results[provider] = await _ping_anthropic(api_key)
            elif provider == 'openrouter':
                results[provider] = await _ping_openrouter(api_key)
            elif provider == 'groq':
                results[provider] = await _ping_groq(api_key)
            else:
                results[provider] = {'status': 'ok', 'message': 'Ключ настроен'}
        except Exception as exc:
            logger.warning('Health check failed for %s: %s', provider, exc)
            results[provider] = {'status': 'error', 'message': str(exc)}

    return {'providers': results}


async def _ping_gigachat(
    credentials: str,
    *,
    scope: str = 'GIGACHAT_API_PERS',
) -> dict[str, str]:
    """Пинг GigaChat — получить список моделей (минимальный запрос)."""
    try:
        from gigachat import GigaChat

        client = GigaChat(credentials=credentials, scope=scope, verify_ssl_certs=False)
        client.get_models()
        return {'status': 'ok', 'message': 'Доступен'}
    except Exception as exc:
        msg = str(exc)
        if 'balance' in msg.lower() or 'billing' in msg.lower() or 'средств' in msg.lower():
            return {'status': 'billing_error', 'message': 'Недостаточно средств на балансе'}
        if 'auth' in msg.lower() or 'credentials' in msg.lower() or '401' in msg:
            return {'status': 'auth_error', 'message': 'Невалидный API-ключ'}
        return {'status': 'error', 'message': msg[:200]}


async def _ping_openai(api_key: str) -> dict[str, str]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                'https://api.openai.com/v1/models',
                headers={'Authorization': f'Bearer {api_key}'},
            )
            resp.raise_for_status()
        return {'status': 'ok', 'message': 'Доступен'}
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            return {'status': 'auth_error', 'message': 'Невалидный API-ключ'}
        return {'status': 'error', 'message': f'HTTP {exc.response.status_code}'}
    except Exception as exc:
        return {'status': 'error', 'message': str(exc)[:200]}


async def _ping_anthropic(api_key: str) -> dict[str, str]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                'https://api.anthropic.com/v1/models',
                headers={'x-api-key': api_key, 'anthropic-version': '2023-06-01'},
            )
            resp.raise_for_status()
        return {'status': 'ok', 'message': 'Доступен'}
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            return {'status': 'auth_error', 'message': 'Невалидный API-ключ'}
        return {'status': 'error', 'message': f'HTTP {exc.response.status_code}'}
    except Exception as exc:
        return {'status': 'error', 'message': str(exc)[:200]}


async def _ping_openrouter(api_key: str) -> dict[str, str]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                'https://openrouter.ai/api/v1/models',
                headers={'Authorization': f'Bearer {api_key}'},
            )
            resp.raise_for_status()
        return {'status': 'ok', 'message': 'Доступен'}
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            return {'status': 'auth_error', 'message': 'Невалидный API-ключ'}
        return {'status': 'error', 'message': f'HTTP {exc.response.status_code}'}
    except Exception as exc:
        return {'status': 'error', 'message': str(exc)[:200]}


async def _ping_groq(api_key: str) -> dict[str, str]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                'https://api.groq.com/openai/v1/models',
                headers={'Authorization': f'Bearer {api_key}'},
            )
            resp.raise_for_status()
        return {'status': 'ok', 'message': 'Доступен'}
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            return {'status': 'auth_error', 'message': 'Невалидный API-ключ'}
        return {'status': 'error', 'message': f'HTTP {exc.response.status_code}'}
    except Exception as exc:
        return {'status': 'error', 'message': str(exc)[:200]}
    """Получение списка моделей Groq через OpenAI-совместимый API."""
    if not api_key or not api_key.strip():
        return {'sub_models': [], 'error': 'API-ключ Groq не настроен'}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                'https://api.groq.com/openai/v1/models',
                headers={'Authorization': f'Bearer {api_key}'},
            )
            resp.raise_for_status()
            data = resp.json()

        # Фильтр: только chat-модели (не whisper, не embedding)
        exclude_keywords = ('whisper', 'distil', 'embed', 'tts', 'guard')
        models = []
        for m in data.get('data', []):
            mid = m.get('id', '')
            if any(kw in mid.lower() for kw in exclude_keywords):
                continue
            models.append(
                {
                    'id': mid,
                    'name': mid,
                    'provider': 'Groq',
                }
            )

        models.sort(key=lambda x: x['name'])
        return {'sub_models': models}

    except Exception as exc:
        logger.warning('Failed to fetch Groq models: %s', exc)
        return {
            'sub_models': [
                {'id': 'llama-3.3-70b-versatile', 'name': 'Llama 3.3 70B', 'provider': 'Groq'},
                {'id': 'llama-3.1-8b-instant', 'name': 'Llama 3.1 8B', 'provider': 'Groq'},
                {'id': 'llama3-70b-8192', 'name': 'Llama 3 70B', 'provider': 'Groq'},
                {'id': 'mixtral-8x7b-32768', 'name': 'Mixtral 8x7B', 'provider': 'Groq'},
                {'id': 'gemma2-9b-it', 'name': 'Gemma 2 9B', 'provider': 'Groq'},
            ],
            'fallback': True,
        }

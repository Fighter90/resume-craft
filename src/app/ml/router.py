"""Роутер AI-моделей: /api/v1/models."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings
from app.ml.llm_factory import OPENROUTER_MODELS

router = APIRouter(prefix='/models', tags=['models'])

# Маппинг провайдера → поле с ключом в Settings
_KEY_FIELDS: dict[str, str] = {
    'gigachat': 'gigachat_credentials',
    'openai': 'openai_api_key',
    'groq': 'groq_api_key',
    'openrouter': 'openrouter_api_key',
}


@router.get(
    '',
    summary='Список доступных AI-моделей',
)
async def list_models() -> dict[str, object]:
    """Возвращает модели с флагом доступности (настроен ли API-ключ).

    Не требует авторизации — информация публична.
    """
    settings = get_settings()

    available: dict[str, bool] = {}
    for provider, field in _KEY_FIELDS.items():
        val = getattr(settings, field, '')
        available[provider] = bool(val and val.strip())

    models = [
        {
            'id': 'gigachat-pro',
            'name': 'GigaChat Pro',
            'provider': 'gigachat',
            'available': available['gigachat'],
            'description': '#1 русский язык (MERA), данные в РФ',
        },
        {
            'id': 'gpt-4o',
            'name': 'GPT-4o',
            'provider': 'openai',
            'available': available['openai'],
            'description': 'Топ-модель OpenAI, 128K контекст',
        },
        {
            'id': 'llama-3-70b',
            'name': 'Llama 3.3 70B',
            'provider': 'groq',
            'available': available['groq'],
            'description': 'Бесплатно 14 400 запросов/день',
        },
        {
            'id': 'openrouter',
            'name': 'OpenRouter',
            'provider': 'openrouter',
            'available': available['openrouter'],
            'description': '100+ моделей через единый API',
            'sub_models': OPENROUTER_MODELS,
        },
    ]

    return {'models': models}

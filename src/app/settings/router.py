"""Роутер настроек пользователя: /api/v1/settings/*."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.database import get_session
from app.core.dependencies import get_current_user
from app.settings import service as settings_service
from app.settings.schemas import (
    AIKeysResponse,
    AIKeyStatus,
    AIKeyUpdate,
    AITogglesResponse,
    AITogglesUpdate,
    SelectedModelResponse,
    SelectedModelUpdate,
)

router = APIRouter(prefix='/settings', tags=['settings'])


@router.get(
    '/ai-keys',
    response_model=AIKeysResponse,
    summary='Статусы API-ключей (маскированные)',
)
async def get_ai_keys(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AIKeysResponse:
    """Возвращает маскированные ключи всех провайдеров."""
    keys = await settings_service.get_ai_keys_status(session, user_id=current_user.id)
    return AIKeysResponse(keys=keys)


@router.put(
    '/ai-keys/{provider}',
    response_model=AIKeyStatus,
    summary='Сохранить API-ключ провайдера',
)
async def save_ai_key(
    provider: str,
    data: AIKeyUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AIKeyStatus:
    """Зашифровать и сохранить API-ключ в БД."""
    if provider not in settings_service.VALID_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Неизвестный провайдер: {provider}',
        )
    await settings_service.save_ai_key(
        session,
        user_id=current_user.id,
        provider=provider,
        api_key=data.api_key,
    )
    from app.core.encryption import mask_api_key

    return AIKeyStatus(
        provider=provider,
        has_key=True,
        masked_key=mask_api_key(data.api_key),
    )


@router.delete(
    '/ai-keys/{provider}',
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary='Удалить API-ключ провайдера',
)
async def delete_ai_key(
    provider: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Удалить API-ключ из БД."""
    await settings_service.delete_ai_key(
        session,
        user_id=current_user.id,
        provider=provider,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    '/ai-toggles',
    response_model=AITogglesResponse,
    summary='Получить AI-настройки (toggles)',
)
async def get_ai_toggles(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AITogglesResponse:
    """Получить текущие AI-настройки пользователя."""
    toggles: dict[str, bool] = {}
    for key in ('auto_metrics', 'ats', 'upgrade_title', 'keep_language', 'soft_skills'):
        val = await settings_service.get_decrypted_value(
            session,
            user_id=current_user.id,
            category='ai_toggles',
            key=key,
        )
        toggles[key] = val == 'true' if val else key in ('auto_metrics', 'ats', 'keep_language')
    return AITogglesResponse(toggles=toggles)


@router.put(
    '/ai-toggles',
    response_model=AITogglesResponse,
    summary='Обновить AI-настройки (toggles)',
)
async def save_ai_toggles(
    data: AITogglesUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AITogglesResponse:
    """Сохранить AI-настройки в БД."""
    result: dict[str, bool] = {}
    for toggle in data.toggles:
        await settings_service.set_setting(
            session,
            user_id=current_user.id,
            category='ai_toggles',
            key=toggle.key,
            value='true' if toggle.value else 'false',
        )
        result[toggle.key] = toggle.value
    return AITogglesResponse(toggles=result)


@router.get(
    '/ai-model',
    response_model=SelectedModelResponse,
    summary='Получить выбранную модель',
)
async def get_selected_model(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SelectedModelResponse:
    """Получить текущую выбранную AI-модель пользователя."""
    model = await settings_service.get_decrypted_value(
        session,
        user_id=current_user.id,
        category='ai_model',
        key='selected',
    )
    sub_model = await settings_service.get_decrypted_value(
        session,
        user_id=current_user.id,
        category='ai_model',
        key='sub_model',
    )
    return SelectedModelResponse(
        model=model or 'gigachat-pro',
        sub_model=sub_model or None,
    )


@router.put(
    '/ai-model',
    response_model=SelectedModelResponse,
    summary='Сохранить выбранную модель',
)
async def save_selected_model(
    data: SelectedModelUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SelectedModelResponse:
    """Сохранить выбранную AI-модель в БД."""
    await settings_service.set_setting(
        session,
        user_id=current_user.id,
        category='ai_model',
        key='selected',
        value=data.model,
    )
    if data.sub_model:
        await settings_service.set_setting(
            session,
            user_id=current_user.id,
            category='ai_model',
            key='sub_model',
            value=data.sub_model,
        )
    return SelectedModelResponse(model=data.model, sub_model=data.sub_model)

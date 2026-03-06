"""Роутер аутентификации: /api/v1/auth/*."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import service as auth_service
from app.auth.models import User
from app.auth.schemas import (
    DeleteAccountRequest,
    LoginRequest,
    MessageResponse,
    PasswordChangeRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UpdateUserRequest,
    UserResponse,
)
from app.core.database import get_session
from app.core.dependencies import get_current_user

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post(
    '/register',
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary='Регистрация нового пользователя',
)
async def register(
    data: RegisterRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Создание нового аккаунта → JWT-токены."""
    return await auth_service.register(session, data=data)


@router.post(
    '/login',
    response_model=TokenResponse,
    summary='Авторизация по email/password',
)
async def login(
    data: LoginRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Получение JWT-токенов."""
    return await auth_service.authenticate(
        session,
        email=data.email,
        password=data.password,
    )


@router.post(
    '/refresh',
    response_model=TokenResponse,
    summary='Обновление JWT-токенов',
)
async def refresh(
    data: RefreshRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Обновление пары токенов по refresh-токену."""
    return await auth_service.refresh_tokens(session, refresh_token=data.refresh_token)


@router.post(
    '/logout',
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary='Выход из системы',
)
async def logout(
    _current_user: User = Depends(get_current_user),
) -> Response:
    """Выход (клиент должен удалить токены)."""
    # Stateless JWT — инвалидация через jti blacklist планируется в Phase 2
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    '/me',
    response_model=UserResponse,
    summary='Текущий пользователь',
)
async def me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Получение профиля текущего пользователя."""
    return UserResponse.model_validate(current_user)


@router.put(
    '/me',
    response_model=UserResponse,
    summary='Обновление профиля',
)
async def update_me(
    data: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    """Обновление данных профиля (имя, email)."""
    updated = await auth_service.update_user(
        session,
        user=current_user,
        full_name=data.full_name,
        email=str(data.email) if data.email else None,
    )
    return UserResponse.model_validate(updated)


@router.put(
    '/me/password',
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary='Смена пароля',
)
async def change_password(
    data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Смена пароля текущего пользователя."""
    await auth_service.change_password(
        session,
        user=current_user,
        current_password=data.current_password,
        new_password=data.new_password,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    '/me',
    response_model=MessageResponse,
    summary='Удаление аккаунта (soft-delete, 30 дней)',
)
async def delete_me(
    data: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """Soft-delete аккаунта с 30-дневным периодом восстановления (ФЗ-152).

    Требует подтверждение паролем. Данные будут окончательно удалены через 30 дней.
    Для восстановления — войдите в аккаунт до истечения срока.
    """
    result = await auth_service.soft_delete_account(
        session, user=current_user, password=data.password,
    )
    return MessageResponse(message=result)


@router.post(
    '/me/restore',
    response_model=MessageResponse,
    summary='Восстановление аккаунта',
)
async def restore_me(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """Отмена удаления аккаунта в течение 30-дневного периода."""
    result = await auth_service.restore_account(session, user=current_user)
    return MessageResponse(message=result)

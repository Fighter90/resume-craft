"""Роутер аутентификации: /api/v1/auth/*."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import service as auth_service
from app.auth.models import User
from app.auth.schemas import (
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.core.database import get_session
from app.core.dependencies import get_current_user

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post(
    '/register',
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary='Регистрация нового пользователя',
)
async def register(
    data: RegisterRequest,
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    """Создание нового аккаунта."""
    user = await auth_service.register(session, data=data)
    return UserResponse.model_validate(user)


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
        session, email=data.email, password=data.password,
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
    summary='Выход из системы',
)
async def logout(
    _current_user: User = Depends(get_current_user),
) -> None:
    """Выход (клиент должен удалить токены)."""
    # Stateless JWT — инвалидация через jti blacklist планируется в Phase 2
    return None


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

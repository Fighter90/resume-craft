"""Бизнес-логика аутентификации."""

from __future__ import annotations

from uuid import UUID

import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.schemas import RegisterRequest, TokenResponse
from app.core.exceptions import (
    InactiveUser,
    InvalidCredentials,
    TokenExpired,
    TokenInvalid,
    UserAlreadyExists,
    UserNotFound,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


async def get_user_by_email(session: AsyncSession, *, email: str) -> User | None:
    """Поиск пользователя по email."""
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, *, user_id: UUID) -> User | None:
    """Поиск пользователя по ID."""
    return await session.get(User, user_id)


async def register(
    session: AsyncSession,
    *,
    data: RegisterRequest,
) -> TokenResponse:
    """Регистрация нового пользователя → JWT-токены.

    Raises:
        UserAlreadyExists: если email уже занят.
    """
    existing = await get_user_by_email(session, email=data.email)
    if existing:
        raise UserAlreadyExists()

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    session.add(user)
    await session.flush()

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


async def authenticate(
    session: AsyncSession,
    *,
    email: str,
    password: str,
) -> TokenResponse:
    """Аутентификация — возвращает пару access+refresh токенов.

    Raises:
        InvalidCredentials: неверный email или пароль.
        InactiveUser: аккаунт деактивирован.
    """
    user = await get_user_by_email(session, email=email)
    if not user or not verify_password(password, user.hashed_password):
        raise InvalidCredentials()

    if not user.is_active:
        raise InactiveUser()

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


async def refresh_tokens(
    session: AsyncSession,
    *,
    refresh_token: str,
) -> TokenResponse:
    """Обновление пары токенов по refresh-токену.

    Raises:
        TokenExpired: токен истёк.
        TokenInvalid: невалидный токен.
        UserNotFound: пользователь не найден.
        InactiveUser: аккаунт деактивирован.
    """
    try:
        payload = decode_token(refresh_token)
    except jwt.ExpiredSignatureError:
        raise TokenExpired() from None
    except jwt.InvalidTokenError:
        raise TokenInvalid() from None

    if payload.get('type') != 'refresh':
        raise TokenInvalid()

    user_id = UUID(payload['sub'])
    user = await get_user_by_id(session, user_id=user_id)
    if not user:
        raise UserNotFound()
    if not user.is_active:
        raise InactiveUser()

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )

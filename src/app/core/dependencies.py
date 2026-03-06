"""FastAPI Depends() — DI для сервисов, сессий, текущего пользователя."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.core.exceptions import InactiveUser, TokenExpired, TokenInvalid
from app.core.security import decode_token

if TYPE_CHECKING:
    from app.auth.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/v1/auth/login')
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl='/api/v1/auth/login', auto_error=False)


@lru_cache
def get_cached_settings() -> Settings:
    """Кэшированные настройки приложения."""
    return get_settings()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Получение текущего пользователя из JWT-токена.

    Raises:
        TokenExpired: если токен истёк.
        TokenInvalid: если токен невалидный.
        InactiveUser: если пользователь деактивирован.
    """
    from app.auth.models import User

    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise TokenExpired() from None
    except jwt.InvalidTokenError:
        raise TokenInvalid() from None

    if payload.get('type') != 'access':
        raise TokenInvalid()

    user_id_str = payload.get('sub')
    if not user_id_str:
        raise TokenInvalid()

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise TokenInvalid() from None

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Пользователь не найден',
        )

    if not user.is_active:
        raise InactiveUser()

    return user


async def get_optional_user(
    token: str | None = Depends(oauth2_scheme_optional),
    session: AsyncSession = Depends(get_session),
) -> User | None:
    """Получение текущего пользователя из JWT (опционально).

    Если токен не передан или невалиден — возвращает None (без ошибки).
    """
    if not token:
        return None

    from app.auth.models import User

    try:
        payload = decode_token(token)
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

    if payload.get('type') != 'access':
        return None

    user_id_str = payload.get('sub')
    if not user_id_str:
        return None

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        return None

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        return None

    return user

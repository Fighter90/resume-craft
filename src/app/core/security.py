"""Безопасность: bcrypt, JWT, OAuth2."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import bcrypt
import jwt

from app.core.config import get_settings

settings = get_settings()

# --- Password Hashing (direct bcrypt, cost=12) ---
_BCRYPT_ROUNDS = 12


def hash_password(password: str) -> str:
    """Хэширование пароля bcrypt (cost=12)."""
    salt = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля по хэшу."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8'),
    )


# --- JWT Tokens ---
def create_access_token(user_id: UUID) -> str:
    """Создание access-токена (30 мин по умолчанию)."""
    payload: dict[str, Any] = {
        'sub': str(user_id),
        'exp': datetime.now(tz=UTC) + timedelta(minutes=settings.access_token_expire_minutes),
        'type': 'access',
        'jti': str(uuid4()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: UUID) -> str:
    """Создание refresh-токена (30 дней по умолчанию)."""
    payload: dict[str, Any] = {
        'sub': str(user_id),
        'exp': datetime.now(tz=UTC) + timedelta(days=settings.refresh_token_expire_days),
        'type': 'refresh',
        'jti': str(uuid4()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """Декодирование и валидация JWT-токена.

    Raises:
        jwt.ExpiredSignatureError: токен истёк.
        jwt.InvalidTokenError: невалидный токен.
    """
    return jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.jwt_algorithm],
    )

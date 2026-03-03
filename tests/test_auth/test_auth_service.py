"""Тесты auth/service.py — бизнес-логика."""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User, UserPlan
from app.auth.schemas import RegisterRequest
from app.auth.service import authenticate, get_user_by_email, get_user_by_id, refresh_tokens, register
from app.core.exceptions import (
    InactiveUser,
    InvalidCredentials,
    TokenExpired,
    TokenInvalid,
    UserAlreadyExists,
    UserNotFound,
)
from app.core.security import create_refresh_token, hash_password


class TestRegisterService:
    """Тесты register()."""

    async def test_register_success(self, session: AsyncSession) -> None:
        """Успешная регистрация."""
        data = RegisterRequest(
            email='newuser@example.com',
            password='StrongPass1',
            full_name='Новый Пользователь',
        )
        user = await register(session, data=data)
        assert user.email == 'newuser@example.com'
        assert user.full_name == 'Новый Пользователь'
        assert user.plan == UserPlan.FREE
        assert user.optimizations_used == 0
        assert user.is_active is True

    async def test_register_duplicate_email(self, session: AsyncSession, test_user: User) -> None:
        """Дубликат email → UserAlreadyExists."""
        data = RegisterRequest(email=test_user.email, password='TestPass123')
        with pytest.raises(UserAlreadyExists):
            await register(session, data=data)


class TestAuthenticateService:
    """Тесты authenticate()."""

    async def test_authenticate_success(self, session: AsyncSession, test_user: User) -> None:
        """Правильные credentials → TokenResponse."""
        result = await authenticate(session, email=test_user.email, password='TestPass123')
        assert result.access_token
        assert result.refresh_token
        assert result.token_type == 'bearer'

    async def test_wrong_password(self, session: AsyncSession, test_user: User) -> None:
        """Неверный пароль → InvalidCredentials."""
        with pytest.raises(InvalidCredentials):
            await authenticate(session, email=test_user.email, password='WrongPass1')

    async def test_nonexistent_email(self, session: AsyncSession) -> None:
        """Несуществующий email → InvalidCredentials."""
        with pytest.raises(InvalidCredentials):
            await authenticate(session, email='nobody@x.com', password='Pass123')

    async def test_inactive_user(self, session: AsyncSession) -> None:
        """Деактивированный пользователь → InactiveUser."""
        user = User(
            id=uuid4(),
            email=f'inactive-{uuid4().hex[:8]}@test.com',
            hashed_password=hash_password('InactivePass1'),
            is_active=False,
        )
        session.add(user)
        await session.flush()
        with pytest.raises(InactiveUser):
            await authenticate(session, email=user.email, password='InactivePass1')


class TestRefreshTokensService:
    """Тесты refresh_tokens()."""

    async def test_refresh_success(self, session: AsyncSession, test_user: User) -> None:
        """Валидный refresh-токен → новая пара."""
        token = create_refresh_token(test_user.id)
        result = await refresh_tokens(session, refresh_token=token)
        assert result.access_token
        assert result.refresh_token

    async def test_refresh_with_access_token(self, session: AsyncSession, test_user: User) -> None:
        """Access-токен вместо refresh → TokenInvalid."""
        from app.core.security import create_access_token

        token = create_access_token(test_user.id)
        with pytest.raises(TokenInvalid):
            await refresh_tokens(session, refresh_token=token)

    async def test_refresh_invalid_token(self, session: AsyncSession) -> None:
        """Невалидный токен → TokenInvalid."""
        with pytest.raises(TokenInvalid):
            await refresh_tokens(session, refresh_token='invalid.token')

    async def test_refresh_nonexistent_user(self, session: AsyncSession) -> None:
        """Refresh для несуществующего пользователя → UserNotFound."""
        token = create_refresh_token(uuid4())
        with pytest.raises(UserNotFound):
            await refresh_tokens(session, refresh_token=token)


class TestGetUserFunctions:
    """Тесты get_user_by_email / get_user_by_id."""

    async def test_get_by_email_exists(self, session: AsyncSession, test_user: User) -> None:
        user = await get_user_by_email(session, email=test_user.email)
        assert user is not None
        assert user.id == test_user.id

    async def test_get_by_email_not_exists(self, session: AsyncSession) -> None:
        user = await get_user_by_email(session, email='nobody@x.com')
        assert user is None

    async def test_get_by_id_exists(self, session: AsyncSession, test_user: User) -> None:
        user = await get_user_by_id(session, user_id=test_user.id)
        assert user is not None
        assert user.email == test_user.email

    async def test_get_by_id_not_exists(self, session: AsyncSession) -> None:
        user = await get_user_by_id(session, user_id=uuid4())
        assert user is None

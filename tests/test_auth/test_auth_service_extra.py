"""Дополнительные тесты auth/service.py — покрытие update_user, change_password, delete."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.service import (
    change_password,
    delete_user_account,
    refresh_tokens,
    restore_account,
    soft_delete_account,
    update_user,
)
from app.core.config import get_settings
from app.core.exceptions import (
    InactiveUser,
    InvalidCredentials,
    TokenExpired,
    UserAlreadyExists,
)
from app.core.security import hash_password, verify_password


class TestRefreshTokensEdgeCases:
    """Дополнительные edge-cases для refresh_tokens()."""

    async def test_refresh_expired_token(self, session: AsyncSession, test_user: User) -> None:
        """Истёкший refresh-токен → TokenExpired."""
        settings = get_settings()
        payload = {
            'sub': str(test_user.id),
            'type': 'refresh',
            'exp': datetime.now(tz=UTC) - timedelta(seconds=10),
        }
        expired_token = jwt.encode(payload, settings.secret_key, algorithm='HS256')
        with pytest.raises(TokenExpired):
            await refresh_tokens(session, refresh_token=expired_token)

    async def test_refresh_inactive_user(self, session: AsyncSession) -> None:
        """Refresh для деактивированного пользователя → InactiveUser."""
        from app.core.security import create_refresh_token

        user = User(
            id=uuid4(),
            email=f'inactive-ref-{uuid4().hex[:8]}@test.com',
            hashed_password=hash_password('InactiveRefresh1'),
            is_active=False,
        )
        session.add(user)
        await session.flush()

        token = create_refresh_token(user.id)
        with pytest.raises(InactiveUser):
            await refresh_tokens(session, refresh_token=token)


class TestUpdateUser:
    """Тесты update_user()."""

    async def test_update_full_name(self, session: AsyncSession, test_user: User) -> None:
        """Обновление имени."""
        result = await update_user(session, user=test_user, full_name='Новое Имя')
        assert result.full_name == 'Новое Имя'

    async def test_update_email(self, session: AsyncSession, test_user: User) -> None:
        """Обновление email на свободный."""
        new_email = f'new-{uuid4().hex[:8]}@example.com'
        result = await update_user(session, user=test_user, email=new_email)
        assert result.email == new_email

    async def test_update_same_email(self, session: AsyncSession, test_user: User) -> None:
        """Обновление на тот же email — без ошибки."""
        result = await update_user(session, user=test_user, email=test_user.email)
        assert result.email == test_user.email

    async def test_update_email_conflict(self, session: AsyncSession) -> None:
        """Обновление email на занятый → UserAlreadyExists."""
        user1 = User(
            id=uuid4(),
            email=f'user1-{uuid4().hex[:8]}@test.com',
            hashed_password=hash_password('Pass1234'),
        )
        user2 = User(
            id=uuid4(),
            email=f'user2-{uuid4().hex[:8]}@test.com',
            hashed_password=hash_password('Pass1234'),
        )
        session.add_all([user1, user2])
        await session.flush()

        with pytest.raises(UserAlreadyExists):
            await update_user(session, user=user2, email=user1.email)

    async def test_update_both(self, session: AsyncSession, test_user: User) -> None:
        """Обновление имени и email одновременно."""
        new_email = f'both-{uuid4().hex[:8]}@example.com'
        result = await update_user(
            session,
            user=test_user,
            full_name='Оба Поля',
            email=new_email,
        )
        assert result.full_name == 'Оба Поля'
        assert result.email == new_email


class TestChangePassword:
    """Тесты change_password()."""

    async def test_change_password_success(
        self,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        """Смена пароля с правильным текущим."""
        await change_password(
            session,
            user=test_user,
            current_password='TestPass123',
            new_password='NewPass456',
        )
        assert verify_password('NewPass456', test_user.hashed_password)

    async def test_change_password_wrong_current(
        self,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        """Неверный текущий пароль → InvalidCredentials."""
        with pytest.raises(InvalidCredentials):
            await change_password(
                session,
                user=test_user,
                current_password='WrongPass999',
                new_password='NewPass456',
            )


class TestDeleteUserAccount:
    """Тесты delete_user_account()."""

    async def test_delete_account(self, session: AsyncSession) -> None:
        """Удаление аккаунта → пользователь удалён из БД."""
        user = User(
            id=uuid4(),
            email=f'delete-{uuid4().hex[:8]}@test.com',
            hashed_password=hash_password('DeleteMe1'),
        )
        session.add(user)
        await session.flush()

        user_id = user.id
        await delete_user_account(session, user=user)
        await session.flush()

        deleted = await session.get(User, user_id)
        assert deleted is None


class TestSoftDeleteAccount:
    """Тесты soft_delete_account() и restore_account()."""

    async def test_soft_delete_success(self, session: AsyncSession) -> None:
        """Soft-delete с правильным паролем → deleted_at устанавливается."""
        user = User(
            id=uuid4(),
            email=f'sd-{uuid4().hex[:8]}@test.com',
            hashed_password=hash_password('SoftDel123'),
        )
        session.add(user)
        await session.flush()

        result = await soft_delete_account(session, user=user, password='SoftDel123')
        assert 'удалён через 30 дней' in result
        assert user.deleted_at is not None
        assert user.scheduled_deletion is not None

    async def test_soft_delete_wrong_password(self, session: AsyncSession) -> None:
        """Soft-delete с неверным паролем → InvalidCredentials."""
        user = User(
            id=uuid4(),
            email=f'sd-wp-{uuid4().hex[:8]}@test.com',
            hashed_password=hash_password('SoftDel123'),
        )
        session.add(user)
        await session.flush()

        with pytest.raises(InvalidCredentials):
            await soft_delete_account(session, user=user, password='WrongPass')

    async def test_restore_account(self, session: AsyncSession) -> None:
        """Восстановление soft-deleted аккаунта."""
        user = User(
            id=uuid4(),
            email=f'restore-{uuid4().hex[:8]}@test.com',
            hashed_password=hash_password('Restore123'),
        )
        session.add(user)
        await session.flush()

        await soft_delete_account(session, user=user, password='Restore123')
        assert user.deleted_at is not None

        result = await restore_account(session, user=user)
        assert 'восстановлен' in result
        assert user.deleted_at is None
        assert user.scheduled_deletion is None

    async def test_restore_not_deleted(self, session: AsyncSession) -> None:
        """Восстановление не-deleted аккаунта → сообщение."""
        user = User(
            id=uuid4(),
            email=f'notdel-{uuid4().hex[:8]}@test.com',
            hashed_password=hash_password('NotDel123'),
        )
        session.add(user)
        await session.flush()

        result = await restore_account(session, user=user)
        assert 'не был помечен' in result

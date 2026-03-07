"""Бизнес-логика аутентификации."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
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
    create_verification_token,
    decode_token,
    hash_password,
    verify_email_token,
    verify_password,
)

logger = logging.getLogger(__name__)


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
        is_verified=False,
    )
    session.add(user)
    await session.flush()

    _token = create_verification_token(data.email)  # TODO: отправить по email
    logger.info('Verification token created for %s (length=%d)', data.email, len(_token))

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


async def verify_email(
    session: AsyncSession,
    *,
    token: str,
) -> str:
    """Подтверждение email по токену.

    Raises:
        TokenExpired: токен истёк.
        TokenInvalid: невалидный токен.
        UserNotFound: пользователь не найден.
    """
    try:
        email = verify_email_token(token)
    except jwt.ExpiredSignatureError:
        raise TokenExpired() from None
    except jwt.InvalidTokenError:
        raise TokenInvalid() from None

    user = await get_user_by_email(session, email=email)
    if not user:
        raise UserNotFound()

    user.is_verified = True
    await session.flush()
    logger.info('Email verified for %s', email)
    return 'Email подтверждён'


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

    # Если аккаунт помечен для удаления — автоматически восстанавливаем при входе
    if user.deleted_at is not None:
        user.deleted_at = None
        user.scheduled_deletion = None
        await session.flush()

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


async def update_user(
    session: AsyncSession,
    *,
    user: User,
    full_name: str | None = None,
    email: str | None = None,
) -> User:
    """Обновление профиля пользователя.

    Raises:
        UserAlreadyExists: если новый email уже занят.
    """
    if email is not None and email != user.email:
        existing = await get_user_by_email(session, email=email)
        if existing:
            raise UserAlreadyExists(email)
        user.email = email

    if full_name is not None:
        user.full_name = full_name

    await session.flush()
    await session.refresh(user)
    return user


async def change_password(
    session: AsyncSession,
    *,
    user: User,
    current_password: str,
    new_password: str,
) -> None:
    """Смена пароля пользователя.

    Raises:
        InvalidCredentials: текущий пароль неверен.
    """
    if not verify_password(current_password, user.hashed_password):
        raise InvalidCredentials()

    user.hashed_password = hash_password(new_password)
    await session.flush()


async def delete_user_account(
    session: AsyncSession,
    *,
    user: User,
) -> None:
    """Полное удаление аккаунта пользователя и всех связанных данных (ФЗ-152).

    AUTH-001: Удаляет файлы пользователя с диска перед удалением из БД.
    Используется Celery-задачей для окончательной очистки после soft-delete.
    """
    from app.core.storage import file_storage

    try:
        await file_storage.delete_user_files(user.id)
    except Exception:
        logger.warning('Failed to delete user files for %s', user.id, exc_info=True)

    await session.delete(user)
    await session.flush()


async def soft_delete_account(
    session: AsyncSession,
    *,
    user: User,
    password: str,
) -> str:
    """Soft-delete аккаунта с 30-дневным периодом восстановления.

    Raises:
        InvalidCredentials: неверный пароль.
        AppError: ошибка базы данных.
    """
    if not verify_password(password, user.hashed_password):
        raise InvalidCredentials()

    try:
        user.deleted_at = datetime.now(tz=UTC)
        user.scheduled_deletion = datetime.now(tz=UTC) + timedelta(days=30)
        await session.flush()
    except Exception as exc:
        logger.exception('Failed to soft-delete user %s: %s', user.id, exc)
        from app.core.exceptions import AppError

        raise AppError(
            message='Не удалось удалить аккаунт. Попробуйте позже.',
            status_code=500,
            error_code='DELETE_ACCOUNT_FAILED',
        ) from exc

    return 'Аккаунт будет удалён через 30 дней. Вы можете отменить удаление, войдя в аккаунт.'


async def restore_account(
    session: AsyncSession,
    *,
    user: User,
) -> str:
    """Отмена soft-delete аккаунта."""
    if user.deleted_at is None:
        return 'Аккаунт не был помечен для удаления'

    user.deleted_at = None
    user.scheduled_deletion = None
    await session.flush()

    return 'Аккаунт успешно восстановлен'

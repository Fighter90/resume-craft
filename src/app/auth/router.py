"""Роутер аутентификации: /api/v1/auth/*."""

import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, Request, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import service as auth_service
from app.auth.models import User
from app.auth.schemas import (
    DeleteAccountRequest,
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
from app.core.exceptions import UserAlreadyExists
from app.core.limiter import limiter

router = APIRouter(prefix='/auth', tags=['auth'])


async def _parse_login_data(request: Request) -> tuple[str, str]:
    """Извлечение email/password из JSON или form-data (P1-4).

    Поддерживает:
    - application/json: {"email": "...", "password": "..."}
    - application/x-www-form-urlencoded: email/username + password
    - multipart/form-data: email/username + password
    """
    from fastapi import HTTPException

    content_type = request.headers.get('content-type', '')

    if 'application/json' in content_type:
        try:
            data = await request.json()
        except Exception:
            raise HTTPException(status_code=422, detail='Некорректный JSON') from None
        email = data.get('email', '')
        password = data.get('password', '')
    elif (
        'application/x-www-form-urlencoded' in content_type
        or 'multipart/form-data' in content_type
    ):
        form = await request.form()
        email = str(form.get('email') or form.get('username') or '')
        password = str(form.get('password') or '')
    else:
        # Default: try JSON parsing (backwards compatible)
        try:
            data = await request.json()
            email = data.get('email', '')
            password = data.get('password', '')
        except Exception:
            raise HTTPException(
                status_code=415,
                detail='Unsupported Content-Type',
            ) from None

    if not email or not password:
        raise HTTPException(status_code=422, detail='Email и пароль обязательны')

    return email, password


@router.post(
    '/register',
    response_model=TokenResponse | MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary='Регистрация нового пользователя',
)
@limiter.limit('3/minute')
async def register(
    request: Request,
    data: RegisterRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse | MessageResponse:
    """Создание нового аккаунта → JWT-токены.

    LIVE-013: Единый формат ответа для защиты от email enumeration.
    """
    try:
        return await auth_service.register(session, data=data)
    except UserAlreadyExists:
        # Не раскрываем, что email уже зарегистрирован
        return MessageResponse(message='Проверьте почту для подтверждения аккаунта')


@router.get(
    '/verify/{token}',
    response_model=MessageResponse,
    summary='Подтверждение email',
)
async def verify_email(
    token: str,
    session: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """Подтверждение email по верификационному токену."""
    result = await auth_service.verify_email(session, token=token)
    return MessageResponse(message=result)


@router.post(
    '/resend-verification',
    response_model=MessageResponse,
    summary='Повторная отправка верификации email',
)
async def resend_verification(
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    """Повторная отправка письма подтверждения email (mock для MVP)."""
    if current_user.is_verified:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail='Email уже подтверждён')

    logger.info('Resend verification requested for %s', current_user.email)
    return MessageResponse(message='Письмо подтверждения отправлено')


@router.post(
    '/login',
    response_model=TokenResponse,
    summary='Авторизация по email/password',
)
@limiter.limit('5/minute')
async def login(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Получение JWT-токенов. Принимает JSON и form-data (P1-4)."""
    email, password = await _parse_login_data(request)
    return await auth_service.authenticate(
        session,
        email=email,
        password=password,
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
        phone=data.phone,
        city=data.city,
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
    summary='Soft-delete аккаунта (30 дней на восстановление)',
)
async def delete_me(
    data: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """Soft-delete аккаунта: помечает для удаления через 30 дней.

    Восстановить аккаунт можно просто войдя в систему.
    """
    if data.confirmation != 'УДАЛИТЬ':
        from app.core.exceptions import AppError

        raise AppError(
            message='Введите УДАЛИТЬ для подтверждения удаления аккаунта',
            status_code=400,
            error_code='DELETE_CONFIRMATION_INVALID',
        )

    result = await auth_service.soft_delete_account(
        session,
        user=current_user,
        password=data.password,
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


logger = logging.getLogger(__name__)

AVATAR_MAX_SIZE: int = 2 * 1024 * 1024  # 2 MB
AVATAR_ALLOWED_TYPES: frozenset[str] = frozenset({'image/jpeg', 'image/png', 'image/webp'})


def _extract_storage_path(avatar_url: str) -> str:
    """Преобразование avatar_url в относительный путь для storage backend."""
    if '/uploads/' in avatar_url:
        return avatar_url.split('/uploads/', 1)[-1]
    return avatar_url.lstrip('/')


@router.post(
    '/me/avatar',
    response_model=MessageResponse,
    summary='Загрузка аватара пользователя',
)
async def upload_avatar(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """Загрузка аватара (JPEG/PNG/WebP, ≤ 2 MB)."""
    from app.core.config import get_settings
    from app.core.storage import file_storage

    if not file.content_type or file.content_type not in AVATAR_ALLOWED_TYPES:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail='Допустимые форматы: JPEG, PNG, WebP')

    content = await file.read()
    if len(content) > AVATAR_MAX_SIZE:
        from fastapi import HTTPException

        raise HTTPException(status_code=413, detail='Максимальный размер аватара — 2 MB')

    # Определяем расширение из content-type
    ext_map = {'image/jpeg': 'jpg', 'image/png': 'png', 'image/webp': 'webp'}
    ext = ext_map.get(file.content_type, 'jpg')
    filename = f'avatar_{uuid4().hex[:8]}.{ext}'

    # Удаляем старый аватар
    if current_user.avatar_url:
        try:
            old_path = current_user.avatar_url.split('/uploads/', 1)[-1]
            await file_storage.delete(old_path)
        except Exception:
            logger.warning(
                'Failed to delete old avatar for user %s',
                current_user.id,
                exc_info=True,
            )

    relative_path = await file_storage.save(current_user.id, filename, content)
    settings = get_settings()
    avatar_url = f'{settings.api_v1_prefix}/uploads/{relative_path}'

    current_user.avatar_url = avatar_url
    await session.flush()

    return MessageResponse(message=avatar_url)


@router.delete(
    '/me/avatar',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Удаление аватара',
)
async def delete_avatar(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Удаление аватара пользователя."""
    if current_user.avatar_url:
        file_storage = None
        try:
            from app.core.storage import file_storage as storage_backend

            file_storage = storage_backend
        except Exception:
            logger.warning(
                'Storage backend unavailable while deleting avatar for user %s',
                current_user.id,
                exc_info=True,
            )

        if file_storage is not None:
            try:
                old_path = _extract_storage_path(current_user.avatar_url)
                if old_path:
                    await file_storage.delete(old_path)
            except Exception:
                logger.warning(
                    'Failed to delete avatar file for user %s',
                    current_user.id,
                    exc_info=True,
                )

    current_user.avatar_url = None
    await session.flush()

    return Response(status_code=status.HTTP_204_NO_CONTENT)

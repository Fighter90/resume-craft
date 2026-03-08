"""Бизнес-логика пользовательских настроек."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import decrypt_value, encrypt_value, mask_api_key
from app.settings.models import UserSetting
from app.settings.schemas import AIKeyStatus

# Допустимые провайдеры для API-ключей
VALID_PROVIDERS: frozenset[str] = frozenset(
    {
        'gigachat',
        'openai',
        'anthropic',
        'openrouter',
        'groq',
    }
)


async def get_setting(
    session: AsyncSession,
    *,
    user_id: UUID,
    category: str,
    key: str,
) -> UserSetting | None:
    """Получить настройку пользователя."""
    stmt = select(UserSetting).where(
        UserSetting.user_id == user_id,
        UserSetting.category == category,
        UserSetting.key == key,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def set_setting(
    session: AsyncSession,
    *,
    user_id: UUID,
    category: str,
    key: str,
    value: str,
    is_encrypted: bool = False,
) -> UserSetting:
    """Создать или обновить настройку пользователя."""
    existing = await get_setting(session, user_id=user_id, category=category, key=key)

    stored_value = encrypt_value(value) if is_encrypted else value

    if existing:
        existing.value = stored_value
        existing.is_encrypted = is_encrypted
        await session.flush()
        return existing

    setting = UserSetting(
        user_id=user_id,
        category=category,
        key=key,
        value=stored_value,
        is_encrypted=is_encrypted,
    )
    session.add(setting)
    await session.flush()
    return setting


async def get_decrypted_value(
    session: AsyncSession,
    *,
    user_id: UUID,
    category: str,
    key: str,
) -> str:
    """Получить расшифрованное значение настройки."""
    setting = await get_setting(session, user_id=user_id, category=category, key=key)
    if not setting:
        return ''
    if setting.is_encrypted:
        return decrypt_value(setting.value)
    return setting.value


async def get_ai_keys_status(
    session: AsyncSession,
    *,
    user_id: UUID,
) -> list[AIKeyStatus]:
    """Получить статусы всех AI-ключей (маскированные)."""
    result: list[AIKeyStatus] = []
    for provider in sorted(VALID_PROVIDERS):
        setting = await get_setting(
            session,
            user_id=user_id,
            category='ai_keys',
            key=provider,
        )
        if setting and setting.value:
            decrypted = decrypt_value(setting.value) if setting.is_encrypted else setting.value
            result.append(
                AIKeyStatus(
                    provider=provider,
                    has_key=bool(decrypted),
                    masked_key=mask_api_key(decrypted),
                )
            )
        else:
            result.append(AIKeyStatus(provider=provider, has_key=False))
    return result


async def save_ai_key(
    session: AsyncSession,
    *,
    user_id: UUID,
    provider: str,
    api_key: str,
) -> None:
    """Сохранить API-ключ провайдера (зашифрованный)."""
    if provider not in VALID_PROVIDERS:
        msg = f'Неизвестный провайдер: {provider}'
        raise ValueError(msg)
    await set_setting(
        session,
        user_id=user_id,
        category='ai_keys',
        key=provider,
        value=api_key,
        is_encrypted=True,
    )


async def delete_ai_key(
    session: AsyncSession,
    *,
    user_id: UUID,
    provider: str,
) -> None:
    """Удалить API-ключ провайдера."""
    setting = await get_setting(
        session,
        user_id=user_id,
        category='ai_keys',
        key=provider,
    )
    if setting:
        await session.delete(setting)
        await session.flush()


async def get_user_setting(
    session: AsyncSession,
    *,
    user_id: UUID,
    provider: str,
) -> str:
    """Получить расшифрованный API-ключ пользователя для провайдера.

    Используется rewriter-сервисом для проверки доступности модели.
    """
    return await get_decrypted_value(
        session,
        user_id=user_id,
        category='ai_keys',
        key=provider,
    )

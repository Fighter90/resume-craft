"""Сидирование БД: создание тестового пользователя при первом развёртывании."""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from app.auth.models import User, UserPlan
from app.core.database import get_session_factory
from app.core.security import hash_password

logger = logging.getLogger(__name__)

# Данные тестового пользователя
_SEED_EMAIL = 'test@example.com'
_SEED_PASSWORD = 'TestPass123'  # noqa: S105 — seed-данные для development
_SEED_FULL_NAME = 'Тестовый Пользователь'


async def seed_test_user() -> None:
    """Создать тестового пользователя, если его ещё нет.

    Вызывается при первом развёртывании или в lifespan FastAPI.
    Идемпотентна — повторный вызов безопасен.
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        stmt = select(User).where(User.email == _SEED_EMAIL)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            logger.info('Тестовый пользователь %s уже существует', _SEED_EMAIL)
            return

        user = User(
            email=_SEED_EMAIL,
            hashed_password=hash_password(_SEED_PASSWORD),
            full_name=_SEED_FULL_NAME,
            plan=UserPlan.FREE,
        )
        session.add(user)
        await session.commit()
        logger.info(
            'Тестовый пользователь создан: %s / %s',
            _SEED_EMAIL,
            _SEED_PASSWORD,
        )


def run_seed() -> None:
    """Точка входа для запуска из CLI: python -m app.core.seed."""
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed_test_user())


if __name__ == '__main__':
    run_seed()

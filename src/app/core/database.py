"""Async SQLAlchemy engine, session и базовая модель."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import MetaData, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.config import get_settings

# Соглашения для имён constraints (Alembic autogenerate)
convention = {
    'ix': 'ix_%(column_0_label)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'ck': 'ck_%(table_name)s_%(constraint_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s',
}

# Ленивая инициализация engine/session (для совместимости с тестами SQLite)
_engine = None
_session_factory = None


def _get_engine_kwargs() -> dict[str, Any]:
    """Параметры engine в зависимости от драйвера."""
    settings = get_settings()
    kwargs: dict[str, Any] = {'echo': settings.database_echo}
    # pool_size / max_overflow не поддерживаются SQLite
    if 'sqlite' not in settings.database_url:
        kwargs.update(pool_size=20, max_overflow=10, pool_pre_ping=True)
    return kwargs


def get_engine():  # type: ignore[no-untyped-def]
    """Получение (или создание) глобального async engine."""
    global _engine  # noqa: PLW0603
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(settings.database_url, **_get_engine_kwargs())
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Получение (или создание) глобальной фабрики сессий."""
    global _session_factory  # noqa: PLW0603
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(), class_=AsyncSession, expire_on_commit=False,
        )
    return _session_factory

class Base(DeclarativeBase):
    """Базовый класс для всех SQLAlchemy-моделей."""

    metadata = MetaData(naming_convention=convention)


class TimestampMixin:
    """Миксин для полей created_at / updated_at."""

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDMixin:
    """Миксин для UUID primary key."""

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )


async def get_session() -> AsyncSession:  # type: ignore[misc]
    """Генератор async-сессий для FastAPI Depends()."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

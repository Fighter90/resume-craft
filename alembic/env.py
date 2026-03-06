"""Alembic environment configuration для async SQLAlchemy."""

from __future__ import annotations

import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

# Добавление src/ в sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from app.auth.models import User  # noqa: F401
from app.core.config import get_settings
from app.core.database import Base
from app.resumes.models import Resume  # noqa: F401
from app.rewriter.models import RewriteHistory  # noqa: F401
from app.settings.models import UserSetting  # noqa: F401
from app.vacancies.models import Vacancy  # noqa: F401

# Alembic Config
config = context.config

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata для autogenerate
target_metadata = Base.metadata

# Database URL из settings
settings = get_settings()
config.set_main_option('sqlalchemy.url', settings.database_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):  # type: ignore[no-untyped-def]
    """Выполнение миграций с connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Async migrations runner."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (async)."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

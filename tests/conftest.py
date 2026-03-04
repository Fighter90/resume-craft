"""Общие фикстуры для тестов.

ВАЖНО: os.environ задаётся ДО любых импортов app.*, чтобы get_settings()
использовала тестовые значения при module-level инициализации.
"""

from __future__ import annotations

import os

# ── Тестовые env-переменные (до импортов!) ──────────────────────────────────
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-ci-only-do-not-use-in-production')
os.environ.setdefault('DATABASE_URL', 'sqlite+aiosqlite://')
os.environ.setdefault('DATABASE_ECHO', 'false')
os.environ.setdefault('ENVIRONMENT', 'testing')
os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/15')
os.environ.setdefault('CELERY_BROKER_URL', 'memory://')
os.environ.setdefault('CELERY_RESULT_BACKEND', 'cache+memory://')

from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import JSON, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.auth.models import User, UserPlan
from app.core.database import Base, get_session
from app.core.security import hash_password
from app.main import create_app

# ── Тестовая БД (in-memory SQLite) ──────────────────────────────────────────
TEST_DATABASE_URL = 'sqlite+aiosqlite://'


# Маппинг JSONB → JSON для SQLite (JSONB не поддерживается)
@event.listens_for(Base.metadata, 'before_create')
def _remap_jsonb_to_json(target, connection, **kw):  # type: ignore[no-untyped-def]
    """Замена JSONB на JSON при создании таблиц в SQLite."""
    for table in target.sorted_tables:
        for column in table.columns:
            if isinstance(column.type, JSONB):
                column.type = JSON()


@pytest.fixture(scope='session')
async def test_engine():
    """Тестовый async engine (in-memory SQLite)."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def session(test_engine) -> AsyncIterator[AsyncSession]:  # type: ignore[no-untyped-def]
    """Тестовая async-сессия с rollback после каждого теста."""
    factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with factory() as sess:
        yield sess
        await sess.rollback()


@pytest.fixture
async def client(session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """HTTP-клиент для тестирования API через ASGI."""
    app = create_app()

    async def _override_session() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = _override_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as ac:
        yield ac


@pytest.fixture
async def test_user(session: AsyncSession) -> User:
    """Тестовый пользователь (plan=FREE, 0 оптимизаций)."""
    user = User(
        id=uuid4(),
        email=f'test-{uuid4().hex[:8]}@example.com',
        hashed_password=hash_password('TestPass123'),
        full_name='Тест Тестович',
        plan=UserPlan.FREE,
    )
    session.add(user)
    await session.flush()
    return user


@pytest.fixture
async def pro_user(session: AsyncSession) -> User:
    """Тестовый PRO-пользователь (безлимит)."""
    user = User(
        id=uuid4(),
        email=f'pro-{uuid4().hex[:8]}@example.com',
        hashed_password=hash_password('ProPass123'),
        full_name='Про Пользователь',
        plan=UserPlan.PRO,
    )
    session.add(user)
    await session.flush()
    return user


@pytest.fixture
async def exhausted_user(session: AsyncSession) -> User:
    """Пользователь FREE с исчерпанным лимитом."""
    user = User(
        id=uuid4(),
        email=f'exhausted-{uuid4().hex[:8]}@example.com',
        hashed_password=hash_password('ExhPass123'),
        full_name='Исчерпан Лимит',
        plan=UserPlan.FREE,
        optimizations_used=5,
    )
    session.add(user)
    await session.flush()
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    """JWT-заголовки для авторизованных запросов."""
    from app.core.security import create_access_token

    token = create_access_token(test_user.id)
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def pro_auth_headers(pro_user: User) -> dict[str, str]:
    """JWT-заголовки для PRO-пользователя."""
    from app.core.security import create_access_token

    token = create_access_token(pro_user.id)
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
async def auth_client(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> AsyncClient:
    """HTTP-клиент с JWT-авторизацией."""
    client.headers.update(auth_headers)
    return client

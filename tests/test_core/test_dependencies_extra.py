"""Тесты core/dependencies.py — get_cached_settings и InactiveUser."""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import uuid4

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User, UserPlan
from app.core.database import get_session
from app.core.dependencies import get_cached_settings
from app.core.security import create_access_token, hash_password
from app.main import create_app


class TestGetCachedSettings:
    """Тесты get_cached_settings() с @lru_cache."""

    def test_returns_settings(self) -> None:
        """Вызов get_cached_settings() возвращает Settings."""
        get_cached_settings.cache_clear()
        settings = get_cached_settings()
        assert settings.secret_key is not None
        assert hasattr(settings, 'database_url')

    def test_cached_returns_same(self) -> None:
        """Повторный вызов возвращает тот же объект (кэш)."""
        get_cached_settings.cache_clear()
        s1 = get_cached_settings()
        s2 = get_cached_settings()
        assert s1 is s2


class TestInactiveUserDependency:
    """Тест: деактивированный пользователь → 403 InactiveUser."""

    async def test_inactive_user_rejected(
        self,
        session: AsyncSession,
        test_engine: object,
    ) -> None:
        """Запрос от is_active=False → HTTPException 403."""
        # Создаём неактивного пользователя
        inactive_user = User(
            id=uuid4(),
            email=f'inactive-{uuid4().hex[:8]}@example.com',
            hashed_password=hash_password('TestPass123'),
            full_name='Inactive User',
            plan=UserPlan.FREE,
            is_active=False,
        )
        session.add(inactive_user)
        await session.flush()

        token = create_access_token(inactive_user.id)

        app = create_app()

        async def _override_session() -> AsyncIterator[AsyncSession]:
            yield session

        app.dependency_overrides[get_session] = _override_session

        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url='http://test',
        ) as ac:
            response = await ac.get(
                '/api/v1/resumes',
                headers={'Authorization': f'Bearer {token}'},
            )

        assert response.status_code == 403
        data = response.json()
        assert data['error'] == 'INACTIVE_USER'

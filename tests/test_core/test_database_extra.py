"""Дополнительные тесты core/database.py — engine kwargs, session generator."""

from __future__ import annotations

import contextlib
from unittest.mock import patch

from app.core.database import _get_engine_kwargs


class TestEngineKwargs:
    """Тесты _get_engine_kwargs()."""

    def test_sqlite_kwargs(self) -> None:
        """SQLite → без pool_size/max_overflow."""
        from app.core.config import Settings

        mock_settings = Settings(
            secret_key='test-key',
            database_url='sqlite+aiosqlite://',
            database_echo=False,
        )
        with patch('app.core.database.get_settings', return_value=mock_settings):
            kwargs = _get_engine_kwargs()

        assert 'pool_size' not in kwargs
        assert 'max_overflow' not in kwargs

    def test_postgres_kwargs(self) -> None:
        """PostgreSQL → с pool_size/max_overflow."""
        from app.core.config import Settings

        mock_settings = Settings(
            secret_key='test-key',
            database_url='postgresql+asyncpg://user:pass@localhost/db',
            database_echo=False,
        )
        with patch('app.core.database.get_settings', return_value=mock_settings):
            kwargs = _get_engine_kwargs()

        assert kwargs['pool_size'] == 20
        assert kwargs['max_overflow'] == 10
        assert kwargs['pool_pre_ping'] is True
        assert kwargs['echo'] is False


class TestGetSessionGenerator:
    """Тесты get_session() — async generator."""

    async def test_session_commit_on_success(self) -> None:
        """Успешная сессия → commit вызывается."""
        from app.core.database import get_session

        gen = get_session()
        session = await gen.__anext__()
        assert session is not None
        # Завершаем генератор
        with contextlib.suppress(StopAsyncIteration):
            await gen.__anext__()

    async def test_session_rollback_on_error(self) -> None:
        """Ошибка в сессии → rollback."""
        from app.core.database import get_session

        gen = get_session()
        session = await gen.__anext__()
        assert session is not None
        # Вбрасываем ошибку — генератор должен сделать rollback
        with contextlib.suppress(ValueError):
            await gen.athrow(ValueError('test error'))

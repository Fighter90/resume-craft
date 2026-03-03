"""Тесты для app.core.seed — сидирование тестового пользователя."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.seed import _SEED_EMAIL, _SEED_FULL_NAME, seed_test_user


class TestSeedTestUser:
    """Тесты seed_test_user()."""

    @pytest.mark.asyncio
    async def test_creates_user_when_not_exists(self, session) -> None:  # type: ignore[no-untyped-def]
        """Создаёт пользователя, если его нет в БД."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch('app.core.seed.get_session_factory', return_value=mock_factory):
            await seed_test_user()

        mock_session.add.assert_called_once()
        added_user = mock_session.add.call_args[0][0]
        assert added_user.email == _SEED_EMAIL
        assert added_user.full_name == _SEED_FULL_NAME
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_skips_when_user_exists(self, session) -> None:  # type: ignore[no-untyped-def]
        """Не создаёт дубликат, если пользователь уже есть."""
        existing_user = MagicMock()
        existing_user.email = _SEED_EMAIL

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_user
        mock_session.execute.return_value = mock_result

        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch('app.core.seed.get_session_factory', return_value=mock_factory):
            await seed_test_user()

        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_awaited()


class TestRunSeed:
    """Тесты run_seed() — CLI entry point."""

    def test_run_seed_calls_seed_test_user(self) -> None:
        """run_seed() вызывает asyncio.run(seed_test_user())."""
        with (
            patch('app.core.seed.asyncio.run') as mock_run,
            patch('app.core.seed.logging.basicConfig'),
        ):
            from app.core.seed import run_seed

            run_seed()
            mock_run.assert_called_once()

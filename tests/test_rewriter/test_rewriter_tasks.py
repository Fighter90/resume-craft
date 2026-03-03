"""Тесты rewriter/tasks.py — Celery задачи."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.rewriter.tasks import _run_rewrite, execute_rewrite_task


class TestRunRewrite:
    """Тесты _run_rewrite() (async helper for Celery)."""

    @patch('app.rewriter.tasks.rewrite_service')
    @patch('app.rewriter.tasks.get_session_factory')
    async def test_success(self, mock_factory: MagicMock, mock_service: MagicMock) -> None:
        """Успешная оптимизация в async-контексте."""
        task_id = uuid4()

        mock_task = MagicMock()
        mock_task.status.value = 'completed'

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        mock_factory_instance = MagicMock()
        mock_factory_instance.return_value = mock_session
        mock_factory.return_value = mock_factory_instance

        mock_service.execute_rewrite = AsyncMock(return_value=mock_task)

        result = await _run_rewrite(task_id)
        assert result == 'completed'

    @patch('app.rewriter.tasks.rewrite_service')
    @patch('app.rewriter.tasks.get_session_factory')
    async def test_failure_rollback(
        self, mock_factory: MagicMock, mock_service: MagicMock,
    ) -> None:
        """Ошибка → rollback."""
        task_id = uuid4()

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        mock_factory_instance = MagicMock()
        mock_factory_instance.return_value = mock_session
        mock_factory.return_value = mock_factory_instance

        mock_service.execute_rewrite = AsyncMock(side_effect=RuntimeError('boom'))

        with pytest.raises(RuntimeError, match='boom'):
            await _run_rewrite(task_id)

        mock_session.rollback.assert_called_once()


class TestExecuteRewriteTask:
    """Тесты execute_rewrite_task() — синхронная Celery обёртка."""

    @patch('app.rewriter.tasks._run_rewrite')
    def test_success(self, mock_run: MagicMock) -> None:
        """Успешное выполнение Celery-задачи."""
        task_id = str(uuid4())

        # _run_rewrite is async, so we need to make it return a coroutine
        async def _mock_run(tid):  # type: ignore[no-untyped-def]
            return 'completed'

        mock_run.side_effect = _mock_run

        # execute_rewrite_task is a Celery task, call its inner function
        result = execute_rewrite_task(task_id)
        assert result['task_id'] == task_id
        assert result['status'] == 'completed'

    @patch('app.rewriter.tasks._run_rewrite')
    def test_failure_retries(self, mock_run: MagicMock) -> None:
        """Ошибка → Celery retry."""
        task_id = str(uuid4())

        async def _mock_run(tid):  # type: ignore[no-untyped-def]
            raise RuntimeError('LLM timeout')

        mock_run.side_effect = _mock_run

        # The task calls self.retry() which raises Retry exception
        # Since we're not in a real Celery context, self is the task obj
        # Just test that when _run_rewrite fails, the exception propagates
        with pytest.raises(RuntimeError, match='LLM timeout'):
            execute_rewrite_task(task_id)

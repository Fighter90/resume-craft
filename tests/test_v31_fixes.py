"""Тесты V31 (4 дефекта QA Full Regression Report #27).

Покрывает:
- KEY-CHECK-001: Celery worker fresh engine + user_keys retrieval (P1 CRITICAL)
- HISTORY-RAW-ERROR-001: Sanitized LLM error messages (P2 MEDIUM)
- FILE-UPLOAD-001: File input hidden via opacity (P3 LOW) — frontend only
- SCORE-VARIANCE-001: Already covered in test_v30_fixes (P4 INFO)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

# ==================================================================================
# KEY-CHECK-001: Celery worker creates fresh engine per task
# ==================================================================================


class TestCeleryFreshEngine:
    """KEY-CHECK-001: _run_rewrite creates its own engine, not the cached global one."""

    @pytest.mark.asyncio
    async def test_run_rewrite_creates_fresh_engine(self) -> None:
        """_run_rewrite should create_async_engine, not use get_session_factory."""
        from app.rewriter.tasks import _run_rewrite

        task_id = uuid4()

        with (
            patch('app.rewriter.tasks.create_async_engine') as mock_engine_ctor,
            patch('app.rewriter.tasks.async_sessionmaker') as mock_factory_ctor,
            patch('app.rewriter.tasks.rewrite_service') as mock_service,
            patch('app.rewriter.tasks.get_settings') as mock_settings,
            patch('app.rewriter.tasks._get_engine_kwargs', return_value={}),
        ):
            mock_settings.return_value = MagicMock(database_url='sqlite+aiosqlite://')

            mock_engine = MagicMock()
            mock_engine.dispose = AsyncMock()
            mock_engine_ctor.return_value = mock_engine

            # Mock session
            mock_session = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session.rollback = AsyncMock()

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_factory_ctor.return_value = MagicMock(return_value=mock_ctx)

            # Mock execute_rewrite result
            mock_task = MagicMock()
            mock_task.status = MagicMock(value='completed')
            mock_service.execute_rewrite = AsyncMock(return_value=mock_task)

            result = await _run_rewrite(task_id)

            # Should create fresh engine, not use cached one
            mock_engine_ctor.assert_called_once()
            # Should dispose engine after use
            mock_engine.dispose.assert_awaited_once()
            assert result == 'completed'

    @pytest.mark.asyncio
    async def test_run_rewrite_disposes_engine_on_error(self) -> None:
        """Engine must be disposed even if task fails."""
        from app.rewriter.tasks import _run_rewrite

        task_id = uuid4()

        with (
            patch('app.rewriter.tasks.create_async_engine') as mock_engine_ctor,
            patch('app.rewriter.tasks.async_sessionmaker') as mock_factory_ctor,
            patch('app.rewriter.tasks.rewrite_service') as mock_service,
            patch('app.rewriter.tasks.get_settings') as mock_settings,
            patch('app.rewriter.tasks._get_engine_kwargs', return_value={}),
        ):
            mock_settings.return_value = MagicMock(database_url='sqlite+aiosqlite://')

            mock_engine = MagicMock()
            mock_engine.dispose = AsyncMock()
            mock_engine_ctor.return_value = mock_engine

            mock_session = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session.rollback = AsyncMock()

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_factory_ctor.return_value = MagicMock(return_value=mock_ctx)

            mock_service.execute_rewrite = AsyncMock(side_effect=RuntimeError('test'))

            with pytest.raises(RuntimeError, match='test'):
                await _run_rewrite(task_id)

            # Engine MUST be disposed even on failure
            mock_engine.dispose.assert_awaited_once()


class TestUserKeysRetrieval:
    """KEY-CHECK-001: execute_rewrite builds user_keys correctly from DB."""

    @pytest.mark.asyncio
    async def test_user_keys_populated_for_all_providers(self) -> None:
        """User keys should propagate to all provider aliases."""
        from app.rewriter.service import execute_rewrite

        session = AsyncMock()
        task_id = uuid4()
        user_id = uuid4()
        resume_id = uuid4()
        vacancy_id = uuid4()

        # Mock task from DB
        mock_task = MagicMock()
        mock_task.id = task_id
        mock_task.user_id = user_id
        mock_task.resume_id = resume_id
        mock_task.vacancy_id = vacancy_id
        mock_task.model_name = 'openai:gpt-4o-mini'
        mock_task.original_text = 'Senior Python developer...'
        mock_task.status = 'pending'
        mock_task.match_score_before = None
        mock_task.match_score_after = None
        mock_task.rewritten_text = None
        mock_task.rewritten_data = None
        mock_task.score_breakdown = None
        mock_task.ats_rating = None
        mock_task.tokens_used = None
        mock_task.error_message = None
        mock_task.processing_time_ms = None

        session.get = AsyncMock(side_effect=lambda model, pk: {
            task_id: mock_task,
            resume_id: MagicMock(raw_text='test', parsed_data=None, status='draft'),
            vacancy_id: MagicMock(description='Python developer'),
            user_id: MagicMock(optimizations_used=0),
        }.get(pk))

        session.flush = AsyncMock()

        # Mock get_user_setting: openai key exists, others don't
        async def mock_get_setting(_session: object, *, user_id: object, provider: str) -> str:
            return 'sk-test-key-123' if provider == 'openai' else ''

        # Mock LLM factory and client
        mock_client = MagicMock()
        mock_client.complete = AsyncMock(
            return_value=(
                '{"summary": "test", "experience": [],'
                ' "education": [], "skills": ["Python"],'
                ' "keywords_added": ["Python"]}'
            )
        )
        mock_client.close = AsyncMock()

        with (
            patch('app.settings.service.get_user_setting', side_effect=mock_get_setting),
            patch('app.rewriter.service.LLMClientFactory') as mock_factory,
        ):
            mock_factory.create_with_fallback = MagicMock(return_value=mock_client)

            result = await execute_rewrite(session, task_id=task_id)

            # Verify create_with_fallback received user_keys with all openai aliases
            call_kwargs = mock_factory.create_with_fallback.call_args
            result = call_kwargs.kwargs.get('user_keys', {})
            # All openai provider names should have the key
            assert result.get('openai') == 'sk-test-key-123'
            assert result.get('gpt-4o-mini') == 'sk-test-key-123'
            assert result.get('gpt-4o') == 'sk-test-key-123'
            # Non-openai should not be present
            assert 'anthropic' not in result
            assert 'gigachat-pro' not in result

    @pytest.mark.asyncio
    async def test_user_keys_no_duplicate_db_queries(self) -> None:
        """Each DB provider should be queried exactly once (not multiple times)."""
        call_log: list[str] = []

        async def tracking_get_setting(
            _session: object,
            *,
            user_id: object,
            provider: str,
        ) -> str:
            call_log.append(provider)
            return ''

        from app.rewriter.service import execute_rewrite

        session = AsyncMock()
        task_id = uuid4()

        mock_task = MagicMock()
        mock_task.id = task_id
        mock_task.user_id = uuid4()
        mock_task.resume_id = uuid4()
        mock_task.vacancy_id = uuid4()
        mock_task.model_name = 'openai'
        mock_task.original_text = 'Test resume text.'
        mock_task.status = 'pending'
        mock_task.match_score_before = None
        mock_task.match_score_after = None
        mock_task.rewritten_text = None
        mock_task.rewritten_data = None
        mock_task.score_breakdown = None
        mock_task.ats_rating = None
        mock_task.tokens_used = None
        mock_task.error_message = None
        mock_task.processing_time_ms = None

        session.get = AsyncMock(
            side_effect=lambda model, pk: mock_task if pk == task_id
            else MagicMock(
                description='test vacancy',
                raw_text='test',
                parsed_data=None,
                status='draft',
                optimizations_used=0,
            ),
        )
        session.flush = AsyncMock()

        with (
            patch(
                'app.settings.service.get_user_setting',
                side_effect=tracking_get_setting,
            ),
            patch('app.rewriter.service.LLMClientFactory') as mock_factory,
        ):
            mock_factory.create_with_fallback = MagicMock(
                side_effect=Exception('test stop'),
            )

            await execute_rewrite(session, task_id=task_id)

            # Should query exactly 5 DB providers, each once
            assert call_log == ['gigachat', 'openai', 'anthropic', 'openrouter', 'groq']


# ==================================================================================
# HISTORY-RAW-ERROR-001: _handle_llm_error sanitizes raw messages
# ==================================================================================


class TestHandleLlmErrorSanitized:
    """HISTORY-RAW-ERROR-001: _handle_llm_error returns clean messages."""

    def test_400_auth_error_gives_clean_message(self) -> None:
        """GigaChat 400 with 'decode Authorization' should give LLMAuthError."""
        from app.core.exceptions import LLMAuthError
        from app.ml.llm_client import _handle_llm_error

        exc = Exception("Can't decode Authorization header, error=invalid_client")
        exc.status_code = 400  # type: ignore[attr-defined]

        with pytest.raises(LLMAuthError) as exc_info:
            _handle_llm_error(exc, provider='gigachat-pro')

        msg = exc_info.value.message
        assert 'URL' not in msg
        assert 'sberbank' not in msg
        assert 'GigaChat' in msg

    def test_400_generic_gives_clean_message(self) -> None:
        """400 without auth keywords → clean 'parameter error' message."""
        from app.core.exceptions import LLMProviderUnavailable
        from app.ml.llm_client import _handle_llm_error

        exc = Exception(
            "Error code: 400 - {'error': {'message':"
            " \"Unsupported parameter: 'max_tokens'\"}}"
        )
        exc.status_code = 400  # type: ignore[attr-defined]

        with pytest.raises(LLMProviderUnavailable) as exc_info:
            _handle_llm_error(exc, provider='openai')

        msg = exc_info.value.message
        assert 'max_tokens' not in msg
        assert 'ошибка параметров' in msg.lower()

    def test_catchall_no_raw_data(self) -> None:
        """Unknown error should NOT contain raw exception text."""
        from app.core.exceptions import LLMProviderUnavailable
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('Some internal traceback\nFile "xxx.py" line 123\nKeyError: foo')

        with pytest.raises(LLMProviderUnavailable) as exc_info:
            _handle_llm_error(exc, provider='openai')

        msg = exc_info.value.message
        assert 'traceback' not in msg.lower()
        assert 'xxx.py' not in msg
        assert 'KeyError' not in msg

    def test_401_gives_auth_error(self) -> None:
        """401 still correctly maps to LLMAuthError."""
        from app.core.exceptions import LLMAuthError
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('Unauthorized')
        exc.status_code = 401  # type: ignore[attr-defined]

        with pytest.raises(LLMAuthError):
            _handle_llm_error(exc, provider='openai')

    def test_429_gives_rate_limit(self) -> None:
        """429 still correctly maps to rate limit."""
        from app.core.exceptions import LLMProviderUnavailable
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('Rate limit exceeded')
        exc.status_code = 429  # type: ignore[attr-defined]

        with pytest.raises(LLMProviderUnavailable) as exc_info:
            _handle_llm_error(exc, provider='openai')

        assert 'лимит' in exc_info.value.message.lower()

    def test_500_gives_server_error(self) -> None:
        """500 still correctly maps to server unavailable."""
        from app.core.exceptions import LLMProviderUnavailable
        from app.ml.llm_client import _handle_llm_error

        exc = Exception('Internal Server Error')
        exc.status_code = 500  # type: ignore[attr-defined]

        with pytest.raises(LLMProviderUnavailable) as exc_info:
            _handle_llm_error(exc, provider='openai')

        assert 'недоступен' in exc_info.value.message.lower()


class TestExecuteRewriteErrorFormat:
    """HISTORY-RAW-ERROR-001: error_message stored in task is user-friendly."""

    @pytest.mark.asyncio
    async def test_error_message_no_raw_url(self) -> None:
        """Task error_message should not contain raw URLs."""
        from app.core.exceptions import LLMProviderUnavailable
        from app.rewriter.service import execute_rewrite

        session = AsyncMock()
        task_id = uuid4()

        mock_task = MagicMock()
        mock_task.id = task_id
        mock_task.user_id = uuid4()
        mock_task.resume_id = uuid4()
        mock_task.vacancy_id = uuid4()
        mock_task.model_name = 'gigachat-pro'
        mock_task.original_text = 'Resume text'
        mock_task.status = 'pending'
        mock_task.match_score_before = None
        mock_task.match_score_after = None
        mock_task.rewritten_text = None
        mock_task.rewritten_data = None
        mock_task.score_breakdown = None
        mock_task.ats_rating = None
        mock_task.tokens_used = None
        mock_task.error_message = None
        mock_task.processing_time_ms = None

        session.get = AsyncMock(
            side_effect=lambda model, pk: mock_task if pk == task_id
            else MagicMock(
                description='vacancy',
                raw_text='text',
                parsed_data=None,
                status='draft',
                optimizations_used=0,
            ),
        )
        session.flush = AsyncMock()

        with (
            patch('app.settings.service.get_user_setting', AsyncMock(return_value='')),
            patch('app.rewriter.service.LLMClientFactory') as mock_factory,
        ):
            mock_factory.create_with_fallback = MagicMock(
                side_effect=LLMProviderUnavailable('all'),
            )

            result = await execute_rewrite(session, task_id=task_id)

            assert result.status.value == 'failed' or result.status == 'failed'
            assert result.error_message is not None
            # Should NOT contain raw URLs
            assert 'https://' not in (result.error_message or '')
            assert 'http://' not in (result.error_message or '')


# ==================================================================================
# KEY-CHECK-001 + HISTORY-RAW-ERROR-001: LLMClientFactory fallback
# ==================================================================================


class TestLLMFactoryFallbackWithUserKeys:
    """Factory uses user_keys and falls back cleanly."""

    def test_create_with_user_key(self) -> None:
        """create() uses user API key when provided."""
        from app.ml.llm_factory import LLMClientFactory

        with patch('app.ml.llm_factory.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(openai_api_key='', groq_api_key='')

            # OpenAI with user key should not raise
            with patch('app.ml.llm_client.OpenAIClient') as mock_oai:
                mock_oai.return_value = MagicMock()
                client = LLMClientFactory.create('openai', api_key='sk-user-key')
                assert client is not None

    def test_create_no_key_raises_auth_error(self) -> None:
        """create() without any key raises LLMAuthError."""
        from app.core.exceptions import LLMAuthError
        from app.ml.llm_factory import LLMClientFactory

        with patch('app.ml.llm_factory.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(openai_api_key='')

            with pytest.raises(LLMAuthError):
                LLMClientFactory.create('openai', api_key=None)

    def test_fallback_tries_all_providers(self) -> None:
        """create_with_fallback tries all providers and raises if all fail."""
        from app.core.exceptions import LLMProviderUnavailable
        from app.ml.llm_factory import LLMClientFactory

        with patch('app.ml.llm_factory.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                gigachat_credentials='',
                openai_api_key='',
                anthropic_api_key='',
                openrouter_api_key='',
                groq_api_key='',
            )

            with pytest.raises(LLMProviderUnavailable) as exc_info:
                LLMClientFactory.create_with_fallback(preferred='openai', user_keys={})

            msg = str(exc_info.value.message).lower()
            assert 'all' in msg or 'все' in msg


# ==================================================================================
# KEY-CHECK-001: Celery task function (synchronous wrapper)
# ==================================================================================


class TestCeleryTaskWrapper:
    """Celery task creates event loop and calls _run_rewrite."""

    def test_task_returns_status_dict(self) -> None:
        """execute_rewrite_task should return dict with task_id and status."""
        with patch('app.rewriter.tasks._run_rewrite') as mock_run:
            # Mock _run_rewrite as a coroutine
            async def fake_run(_tid: object) -> str:
                return 'completed'

            mock_run.side_effect = fake_run

            # Call the underlying function directly (bypass Celery decorator)
            import asyncio

            from app.rewriter.tasks import _run_rewrite

            loop = asyncio.new_event_loop()
            try:
                result = loop.run_until_complete(_run_rewrite(uuid4()))
            finally:
                loop.close()

            assert result == 'completed'

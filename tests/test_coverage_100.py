"""Дополнительные тесты для достижения 100% покрытия.

Покрытие gap-ов:
- ml/llm_client.py: AnthropicClient, _handle_llm_error (все ветви),
  GigaChat/OpenAI/OpenRouter error paths
- ml/llm_factory.py: create_with_fallback (preferred not in order,
  all fail)
- core/celery_app.py: _load_all_models
- resumes/router.py: create_from_text endpoint
- resumes/service.py: create_from_text (ветви с hh.ru URL, _try_generate_embedding)
- rewriter/service.py: edge-cases (sub_model, AppError handling, JSON regex fallback)
"""

from __future__ import annotations

import sys
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import LLMAuthError, LLMProviderUnavailable
from app.ml.llm_client import AnthropicClient, _handle_llm_error

# ── _handle_llm_error() — все ветви ─────────────────────────────────────────


class TestHandleLLMError:
    """Тесты всех ветвей _handle_llm_error."""

    def test_401_status_code(self) -> None:
        """status_code=401 → LLMAuthError."""
        exc = Exception('Unauthorized')
        exc.status_code = 401  # type: ignore[attr-defined]
        with pytest.raises(LLMAuthError):
            _handle_llm_error(exc, provider='test')

    def test_401_in_message(self) -> None:
        """'401' в тексте ошибки → LLMAuthError."""
        with pytest.raises(LLMAuthError):
            _handle_llm_error(Exception('Error 401 Unauthorized'), provider='test')

    def test_unauthorized_in_message(self) -> None:
        """'Unauthorized' в тексте → LLMAuthError."""
        with pytest.raises(LLMAuthError):
            _handle_llm_error(Exception('Unauthorized access'), provider='test')

    def test_429_rate_limit(self) -> None:
        """status_code=429 → LLMProviderUnavailable (rate limit)."""
        exc = Exception('Too many requests')
        exc.status_code = 429  # type: ignore[attr-defined]
        with pytest.raises(LLMProviderUnavailable, match='лимит запросов'):
            _handle_llm_error(exc, provider='test')

    def test_429_in_message(self) -> None:
        """'429' в тексте → rate limit."""
        with pytest.raises(LLMProviderUnavailable, match='лимит запросов'):
            _handle_llm_error(Exception('Error 429'), provider='test')

    def test_rate_in_message(self) -> None:
        """'rate' в тексте → rate limit."""
        with pytest.raises(LLMProviderUnavailable, match='лимит запросов'):
            _handle_llm_error(Exception('Rate limit exceeded'), provider='test')

    def test_5xx_server_error(self) -> None:
        """status_code=500 → сервер недоступен."""
        exc = Exception('Internal server error')
        exc.status_code = 500  # type: ignore[attr-defined]
        with pytest.raises(LLMProviderUnavailable, match='временно недоступен'):
            _handle_llm_error(exc, provider='test')

    def test_502_server_error(self) -> None:
        """status_code=502 → сервер недоступен."""
        exc = Exception('Bad gateway')
        exc.status_code = 502  # type: ignore[attr-defined]
        with pytest.raises(LLMProviderUnavailable, match='временно недоступен'):
            _handle_llm_error(exc, provider='test')

    def test_timeout_error(self) -> None:
        """'timeout' в тексте → таймаут."""
        with pytest.raises(LLMProviderUnavailable, match='таймаут'):
            _handle_llm_error(Exception('Connection timeout'), provider='test')

    def test_timed_out_error(self) -> None:
        """'timed out' в тексте → таймаут."""
        with pytest.raises(LLMProviderUnavailable, match='таймаут'):
            _handle_llm_error(Exception('Request timed out'), provider='test')

    def test_generic_error(self) -> None:
        """Другая ошибка → LLMProviderUnavailable с текстом."""
        with pytest.raises(LLMProviderUnavailable, match='test: Some weird error'):
            _handle_llm_error(Exception('Some weird error'), provider='test')


# ── AnthropicClient ─────────────────────────────────────────────────────────


class TestAnthropicClient:
    """Тесты AnthropicClient."""

    def test_init_default(self) -> None:
        client = AnthropicClient()
        assert client._model == 'claude-sonnet-4-20250514'

    def test_init_custom_model(self) -> None:
        client = AnthropicClient(model='claude-3-5-haiku-20241022')
        assert client._model == 'claude-3-5-haiku-20241022'

    def test_get_client_lazy_init(self) -> None:
        """Lazy-инициализация Anthropic клиента."""
        mock_anthropic_cls = MagicMock()
        mock_anthropic_mod = MagicMock()
        mock_anthropic_mod.AsyncAnthropic = mock_anthropic_cls

        sys.modules['anthropic'] = mock_anthropic_mod
        try:
            client = AnthropicClient()
            assert client._client is None
            result = client._get_client()
            assert result is not None
            mock_anthropic_cls.assert_called_once()
        finally:
            sys.modules.pop('anthropic', None)

    @patch('app.ml.llm_client.AnthropicClient._get_client')
    async def test_complete(self, mock_get: MagicMock) -> None:
        """Успешный запрос к Anthropic."""
        mock_content = MagicMock()
        mock_content.text = 'Claude response'

        mock_response = MagicMock()
        mock_response.content = [mock_content]
        mock_response.usage = MagicMock(output_tokens=50)

        mock_sdk = AsyncMock()
        mock_sdk.messages.create = AsyncMock(return_value=mock_response)
        mock_get.return_value = mock_sdk

        client = AnthropicClient()
        result = await client.complete(system='sys', user='usr')
        assert result == 'Claude response'

    @patch('app.ml.llm_client.AnthropicClient._get_client')
    async def test_complete_empty_content(self, mock_get: MagicMock) -> None:
        """Пустой content → пустая строка."""
        mock_response = MagicMock()
        mock_response.content = []
        mock_response.usage = None

        mock_sdk = AsyncMock()
        mock_sdk.messages.create = AsyncMock(return_value=mock_response)
        mock_get.return_value = mock_sdk

        client = AnthropicClient()
        result = await client.complete(system='sys', user='usr')
        assert result == ''

    @patch('app.ml.llm_client.AnthropicClient._get_client')
    async def test_complete_error(self, mock_get: MagicMock) -> None:
        """Ошибка API → _handle_llm_error → исключение."""
        mock_sdk = AsyncMock()
        mock_sdk.messages.create = AsyncMock(side_effect=Exception('API error'))
        mock_get.return_value = mock_sdk

        client = AnthropicClient()
        with pytest.raises(LLMProviderUnavailable):
            await client.complete(system='sys', user='usr')

    async def test_close_with_client(self) -> None:
        client = AnthropicClient()
        mock_sdk = AsyncMock()
        client._client = mock_sdk
        await client.close()
        mock_sdk.close.assert_called_once()
        assert client._client is None

    async def test_close_without_client(self) -> None:
        client = AnthropicClient()
        await client.close()  # no error


# ── LLMClientFactory — дополнительные ветви ──────────────────────────────────


class TestLLMClientFactoryExtraFallback:
    """Дополнительные тесты fallback-стратегии."""

    def test_fallback_preferred_not_in_default_order(self) -> None:
        """preferred='claude-sonnet' (не в FALLBACK_ORDER) → добавляется в начало."""
        s = MagicMock()
        s.gigachat_credentials = 'test'
        s.openai_api_key = 'test'
        s.anthropic_api_key = 'test'
        s.openrouter_api_key = 'test'

        from app.ml.llm_factory import LLMClientFactory

        with patch('app.ml.llm_factory.get_settings', return_value=s):
            client = LLMClientFactory.create_with_fallback(preferred='claude-sonnet')
        assert isinstance(client, AnthropicClient)

    def test_fallback_all_providers_fail(self) -> None:
        """Все провайдеры без ключей → LLMProviderUnavailable('all')."""
        s = MagicMock()
        s.gigachat_credentials = ''
        s.openai_api_key = ''
        s.anthropic_api_key = ''
        s.openrouter_api_key = ''

        from app.ml.llm_factory import LLMClientFactory

        with (
            patch('app.ml.llm_factory.get_settings', return_value=s),
            pytest.raises(LLMProviderUnavailable),
        ):
            LLMClientFactory.create_with_fallback()

    def test_fallback_with_sub_model_non_sub_provider(self) -> None:
        """sub_model при non-sub_model провайдере → игнорируется."""
        s = MagicMock()
        s.gigachat_credentials = 'test'
        s.openai_api_key = 'test'
        s.anthropic_api_key = 'test'
        s.openrouter_api_key = 'test'

        from app.ml.llm_client import GigaChatClient
        from app.ml.llm_factory import LLMClientFactory

        with patch('app.ml.llm_factory.get_settings', return_value=s):
            # gigachat-pro не в SUB_MODEL_PROVIDERS → sub_model игнорируется
            client = LLMClientFactory.create_with_fallback(
                preferred='gigachat-pro', sub_model='some-model'
            )
        assert isinstance(client, GigaChatClient)


# ── Celery _preload_models ──────────────────────────────────────────────────


class TestCeleryPreload:
    """Тесты _load_all_models из celery_app.py."""

    def test_load_all_models(self) -> None:
        """_load_all_models импортирует все доменные модели."""
        from app.core.celery_app import _load_all_models

        _load_all_models()

        # Проверяем что модули доступны после preload
        import app.auth.models
        import app.resumes.models
        import app.rewriter.models
        import app.vacancies.models

        assert hasattr(app.auth.models, 'User')
        assert hasattr(app.resumes.models, 'Resume')
        assert hasattr(app.rewriter.models, 'RewriteHistory')
        assert hasattr(app.vacancies.models, 'Vacancy')


# ── Resumes: create_from_text endpoint и service ─────────────────────────────


class TestResumeFromTextService:
    """Тесты resumes/service.py — create_from_text."""

    async def test_create_from_text_default_title(self) -> None:
        """Без title → 'Резюме из текста'."""
        from app.resumes.models import Resume
        from app.resumes.service import create_from_text

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        with patch('app.resumes.service._try_generate_embedding'):
            resume = await create_from_text(
                mock_session,
                user_id=uuid4(),
                text='Python разработчик с опытом 5 лет',
            )

        assert isinstance(resume, Resume)
        assert resume.title == 'Резюме из текста'
        assert resume.file_format == 'txt'
        assert resume.raw_text == 'Python разработчик с опытом 5 лет'

    async def test_create_from_text_hh_url(self) -> None:
        """С hh.ru URL и без title → 'Резюме с hh.ru'."""
        from app.resumes.service import create_from_text

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        with patch('app.resumes.service._try_generate_embedding'):
            resume = await create_from_text(
                mock_session,
                user_id=uuid4(),
                text='Текст резюме',
                source_url='https://hh.ru/resume/12345',
            )

        assert resume.title == 'Резюме с hh.ru'

    async def test_create_from_text_custom_title(self) -> None:
        """С custom title → используется custom title."""
        from app.resumes.service import create_from_text

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        with patch('app.resumes.service._try_generate_embedding'):
            resume = await create_from_text(
                mock_session,
                user_id=uuid4(),
                text='Текст',
                title='Моё резюме',
                source_url='https://hh.ru/resume/12345',
            )

        assert resume.title == 'Моё резюме'

    async def test_create_from_text_file_size(self) -> None:
        """file_size_bytes = длина текста в UTF-8 байтах."""
        from app.resumes.service import create_from_text

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        text = 'Кириллический текст для проверки размера'

        with patch('app.resumes.service._try_generate_embedding'):
            resume = await create_from_text(
                mock_session,
                user_id=uuid4(),
                text=text,
            )

        assert resume.file_size_bytes == len(text.encode('utf-8'))


# ── Rewriter — edge-cases ───────────────────────────────────────────────────


class TestRewriterServiceEdgeCases:
    """Тесты edge-cases rewriter/service.py."""

    def test_parse_llm_response_plain_text(self) -> None:
        """Не-JSON ответ → False, rewritten_data=None."""
        from app.rewriter.models import RewriteHistory
        from app.rewriter.service import _parse_llm_response

        task = MagicMock(spec=RewriteHistory)
        task.rewritten_data = None
        task.keywords_added = None

        result = _parse_llm_response('Просто текстовый ответ без JSON', task=task)
        assert result is False

    def test_parse_llm_response_valid_json(self) -> None:
        """Валидный JSON → True, данные сохранены."""
        import json

        from app.rewriter.models import RewriteHistory
        from app.rewriter.service import _parse_llm_response

        task = MagicMock(spec=RewriteHistory)
        task.rewritten_data = None
        task.keywords_added = None

        response = json.dumps(
            {
                'summary': 'Опытный разработчик',
                'experience': [],
                'skills': ['Python', 'FastAPI'],
                'keywords_added': ['Docker', 'CI/CD'],
            }
        )

        result = _parse_llm_response(response, task=task)
        assert result is True
        assert task.rewritten_data == {
            'summary': 'Опытный разработчик',
            'experience': [],
            'skills': ['Python', 'FastAPI'],
            'keywords_added': ['Docker', 'CI/CD'],
        }
        assert task.keywords_added == ['Docker', 'CI/CD']

    def test_parse_llm_response_markdown_code_block(self) -> None:
        """JSON в markdown code block → True."""
        from app.rewriter.service import _parse_llm_response

        task = MagicMock()
        task.rewritten_data = None
        task.keywords_added = None

        response = '```json\n{"summary": "Test", "keywords_added": ["A"]}\n```'

        result = _parse_llm_response(response, task=task)
        assert result is True
        assert task.rewritten_data['summary'] == 'Test'

    def test_parse_llm_response_trailing_comma(self) -> None:
        """JSON с trailing comma → авто-исправление."""
        from app.rewriter.service import _parse_llm_response

        task = MagicMock()
        task.rewritten_data = None
        task.keywords_added = None

        response = '{"summary": "Test", "keywords_added": ["A",]}'

        result = _parse_llm_response(response, task=task)
        assert result is True

    def test_calculate_ats_rating(self) -> None:
        """Тест _calculate_ats_rating для разных score."""
        from app.rewriter.service import _calculate_ats_rating

        assert _calculate_ats_rating(0.9) in ('A+', 'A')
        assert _calculate_ats_rating(0.7) in ('B+', 'B', 'A')
        assert _calculate_ats_rating(0.5) in ('C+', 'C', 'B')
        assert _calculate_ats_rating(0.3) in ('D', 'C', 'C+')
        assert _calculate_ats_rating(0.1) in ('D', 'F')

    def test_parse_llm_response_regex_fallback(self) -> None:
        """JSON внутри текста, извлечение через regex → True."""
        from app.rewriter.service import _parse_llm_response

        task = MagicMock()
        task.rewritten_data = None
        task.keywords_added = None

        # JSON внутри текстового мусора — regex fallback
        response = 'Вот результат:\n  {"summary": "OK", "keywords_added": ["X"]}\nконец'

        result = _parse_llm_response(response, task=task)
        assert result is True
        assert task.rewritten_data['summary'] == 'OK'


# ── LLM-клиенты: error paths (except blocks) ────────────────────────────────


class TestGigaChatClientError:
    """Тесты GigaChatClient — путь с ошибкой (except block)."""

    @patch('app.ml.llm_client.GigaChatClient._get_client')
    async def test_complete_api_error(self, mock_get: MagicMock) -> None:
        """GigaChat API ошибка → _handle_llm_error → LLMProviderUnavailable."""
        import sys

        mock_gigachat_models = MagicMock()
        mock_gigachat_models.Chat = MagicMock()
        mock_gigachat_models.Messages = MagicMock()
        mock_gigachat_models.MessagesRole = MagicMock()
        mock_gigachat_models.MessagesRole.SYSTEM = 'system'
        mock_gigachat_models.MessagesRole.USER = 'user'
        sys.modules['gigachat'] = MagicMock()
        sys.modules['gigachat.models'] = mock_gigachat_models

        try:
            from app.ml.llm_client import GigaChatClient

            mock_sdk_client = MagicMock()
            mock_sdk_client.chat.side_effect = Exception('Service unavailable')
            mock_get.return_value = mock_sdk_client

            client = GigaChatClient()
            with pytest.raises(LLMProviderUnavailable):
                await client.complete(system='sys', user='usr')
        finally:
            sys.modules.pop('gigachat.models', None)
            sys.modules.pop('gigachat', None)


class TestOpenAIClientError:
    """Тесты OpenAIClient — путь с ошибкой (except block)."""

    @patch('app.ml.llm_client.OpenAIClient._get_client')
    async def test_complete_api_error(self, mock_get: MagicMock) -> None:
        """OpenAI API ошибка → _handle_llm_error → LLMProviderUnavailable."""
        from app.ml.llm_client import OpenAIClient

        mock_sdk = AsyncMock()
        mock_sdk.chat.completions.create = AsyncMock(
            side_effect=Exception('OpenAI connection failed')
        )
        mock_get.return_value = mock_sdk

        client = OpenAIClient()
        with pytest.raises(LLMProviderUnavailable):
            await client.complete(system='sys', user='usr')


class TestOpenRouterClientError:
    """Тесты OpenRouterClient — путь с ошибкой (except block)."""

    @patch('app.ml.llm_client.OpenRouterClient._get_client')
    async def test_complete_api_error(self, mock_get: MagicMock) -> None:
        """OpenRouter API ошибка → _handle_llm_error → LLMProviderUnavailable."""
        from app.ml.llm_client import OpenRouterClient

        mock_sdk = AsyncMock()
        mock_sdk.chat.completions.create = AsyncMock(side_effect=Exception('OpenRouter timeout'))
        mock_get.return_value = mock_sdk

        client = OpenRouterClient()
        with pytest.raises(LLMProviderUnavailable):
            await client.complete(system='sys', user='usr')


# ── Resumes router: create_from_text endpoint ────────────────────────────────


class TestResumeFromTextEndpoint:
    """Тесты POST /api/v1/resumes/from-text endpoint."""

    async def test_create_from_text_endpoint(self) -> None:
        """Успешное создание резюме из текста через endpoint."""
        from datetime import UTC, datetime

        from httpx import ASGITransport, AsyncClient

        from app.auth.models import User, UserPlan
        from app.core.database import get_session
        from app.core.dependencies import get_current_user
        from app.main import create_app
        from app.resumes.models import Resume, ResumeStatus

        user_id = uuid4()
        mock_user = User(
            id=user_id,
            email='test@test.com',
            hashed_password='hashed',
            plan=UserPlan.FREE,
            optimizations_used=0,
            is_active=True,
        )

        now = datetime.now(tz=UTC)
        mock_resume = Resume(
            id=uuid4(),
            user_id=user_id,
            title='Резюме из текста',
            file_path='',
            file_format='txt',
            file_size_bytes=100,
            raw_text='Python разработчик',
            status=ResumeStatus.DRAFT,
            created_at=now,
            updated_at=now,
        )

        app = create_app()

        async def _fake_user() -> User:
            return mock_user

        async def _fake_session() -> AsyncMock:
            return AsyncMock()

        app.dependency_overrides[get_current_user] = _fake_user
        app.dependency_overrides[get_session] = _fake_session

        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url='http://test') as client:
            with patch(
                'app.resumes.router.resume_service.create_from_text',
                new=AsyncMock(return_value=mock_resume),
            ):
                long_text = 'Python разработчик с опытом работы более пяти лет в крупных проектах'
                resp = await client.post(
                    '/api/v1/resumes/from-text',
                    json={'text': long_text},
                )

        app.dependency_overrides.clear()

        assert resp.status_code == 201
        data = resp.json()
        assert data['title'] == 'Резюме из текста'
        assert data['file_format'] == 'txt'


# ── Rewriter service: sub_model combination and error handling ───────────────


class TestRewriterServiceSubModel:
    """Тесты rewriter/service.py — сохранение sub_model в model_name."""

    async def test_create_task_with_sub_model(self) -> None:
        """Создание задачи с sub_model → model_name='openai:gpt-4o'."""
        from app.rewriter.service import create_rewrite_task

        resume_id = uuid4()
        vacancy_id = uuid4()
        user_id = uuid4()

        mock_resume = MagicMock()
        mock_resume.raw_text = 'Python разработчик'

        mock_vacancy = MagicMock()

        mock_session = AsyncMock()

        # Настроим execute чтобы вернуть resume и vacancy
        mock_result_resume = MagicMock()
        mock_result_resume.scalar_one_or_none.return_value = mock_resume

        mock_result_vacancy = MagicMock()
        mock_result_vacancy.scalar_one_or_none.return_value = mock_vacancy

        mock_session.execute = AsyncMock(side_effect=[mock_result_resume, mock_result_vacancy])
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        task = await create_rewrite_task(
            mock_session,
            user_id=user_id,
            resume_id=resume_id,
            vacancy_id=vacancy_id,
            model_name='openai',
            sub_model='gpt-4o',
        )

        assert task.model_name == 'openai:gpt-4o'


class TestExecuteRewriteEdgeCases:
    """Тесты execute_rewrite — покрытие sub-model split и AppError с detail."""

    async def test_execute_rewrite_sub_model_split(self) -> None:
        """execute_rewrite парсит 'openai:gpt-4o' → provider='openai', sub_model='gpt-4o'."""
        from app.rewriter.models import RewriteHistory, RewriteStatus
        from app.rewriter.service import execute_rewrite

        task_id = uuid4()
        mock_task = MagicMock(spec=RewriteHistory)
        mock_task.id = task_id
        mock_task.user_id = uuid4()
        mock_task.model_name = 'openai:gpt-4o'
        mock_task.original_text = 'Python разработчик с опытом работы'
        mock_task.vacancy_id = uuid4()
        mock_task.resume_id = uuid4()
        mock_task.match_score_before = None
        mock_task.match_score_after = None
        mock_task.rewritten_text = None
        mock_task.rewritten_data = None
        mock_task.tokens_used = None
        mock_task.ats_rating = None
        mock_task.error_message = None
        mock_task.processing_time_ms = None
        mock_task.status = RewriteStatus.PENDING

        mock_vacancy = MagicMock()
        mock_vacancy.description = 'Python developer needed'

        mock_resume = MagicMock()
        mock_resume.parsed_data = None

        mock_user = MagicMock()
        mock_user.optimizations_used = 0

        mock_llm_client = AsyncMock()
        mock_llm_client.complete = AsyncMock(
            return_value='{"summary": "Test", "keywords_added": ["Python"]}'
        )
        mock_llm_client.close = AsyncMock()

        mock_session = AsyncMock()
        mock_session.get = AsyncMock(side_effect=[mock_task, mock_vacancy, mock_resume, mock_user])
        mock_session.flush = AsyncMock()

        with patch(
            'app.rewriter.service.LLMClientFactory.create_with_fallback',
            return_value=mock_llm_client,
        ) as mock_factory:
            result = await execute_rewrite(mock_session, task_id=task_id)

        # Проверяем что factory вызван с правильными аргументами (sub_model split)
        mock_factory.assert_called_once_with(preferred='openai', sub_model='gpt-4o')
        assert result.status == RewriteStatus.COMPLETED

    async def test_execute_rewrite_app_error_with_detail(self) -> None:
        """AppError с detail → error_message = 'message. detail'."""
        from app.core.exceptions import AppError
        from app.rewriter.models import RewriteHistory, RewriteStatus
        from app.rewriter.service import execute_rewrite

        task_id = uuid4()
        mock_task = MagicMock(spec=RewriteHistory)
        mock_task.id = task_id
        mock_task.model_name = 'gigachat-pro'
        mock_task.original_text = 'Python разработчик'
        mock_task.vacancy_id = uuid4()
        mock_task.resume_id = uuid4()
        mock_task.match_score_before = None
        mock_task.match_score_after = None
        mock_task.rewritten_text = None
        mock_task.rewritten_data = None
        mock_task.tokens_used = None
        mock_task.ats_rating = None
        mock_task.error_message = None
        mock_task.processing_time_ms = None
        mock_task.status = RewriteStatus.PENDING

        mock_vacancy = MagicMock()
        mock_vacancy.description = 'Python developer'

        mock_session = AsyncMock()
        mock_session.get = AsyncMock(side_effect=[mock_task, mock_vacancy])
        mock_session.flush = AsyncMock()

        # LLM factory бросает AppError с detail
        app_error = AppError(
            message='LLM недоступен',
            status_code=503,
            error_code='LLM_UNAVAILABLE',
        )
        app_error.detail = 'Все провайдеры временно недоступны'

        with patch(
            'app.rewriter.service.LLMClientFactory.create_with_fallback',
            side_effect=app_error,
        ):
            result = await execute_rewrite(mock_session, task_id=task_id)

        assert result.status == RewriteStatus.FAILED
        assert result.error_message == 'LLM недоступен. Все провайдеры временно недоступны'

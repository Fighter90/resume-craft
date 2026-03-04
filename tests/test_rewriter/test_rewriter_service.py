"""Тесты rewriter/service.py — 8-шаговый pipeline."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.exceptions import ResumeNotFound, RewriteTaskNotFound, VacancyNotFound
from app.resumes.models import Resume
from app.rewriter.models import RewriteHistory, RewriteStatus
from app.rewriter.service import (
    _calculate_ats_rating,
    _parse_llm_response,
    create_rewrite_task,
    execute_rewrite,
    get_task,
    list_history,
)
from app.vacancies.models import Vacancy


class TestCalculateAtsRating:
    """Тесты _calculate_ats_rating()."""

    def test_a_plus(self) -> None:
        assert _calculate_ats_rating(0.95) == 'A+'

    def test_a(self) -> None:
        assert _calculate_ats_rating(0.85) == 'A'

    def test_b_plus(self) -> None:
        assert _calculate_ats_rating(0.75) == 'B+'

    def test_b(self) -> None:
        assert _calculate_ats_rating(0.65) == 'B'

    def test_c(self) -> None:
        assert _calculate_ats_rating(0.55) == 'C'

    def test_d(self) -> None:
        assert _calculate_ats_rating(0.3) == 'D'

    def test_boundary_090(self) -> None:
        assert _calculate_ats_rating(0.9) == 'A+'

    def test_boundary_080(self) -> None:
        assert _calculate_ats_rating(0.8) == 'A'


class TestParseLlmResponse:
    """Тесты _parse_llm_response()."""

    def test_valid_json(self) -> None:
        task = RewriteHistory(original_text='', model_name='test')
        data = {'summary': 'Test', 'keywords_added': ['python', 'fastapi']}
        _parse_llm_response(json.dumps(data), task=task)
        assert task.rewritten_data == data
        assert task.keywords_added == ['python', 'fastapi']

    def test_json_in_markdown_block(self) -> None:
        task = RewriteHistory(original_text='', model_name='test')
        data = {'summary': 'Test', 'keywords_added': []}
        md = f'```json\n{json.dumps(data)}\n```'
        _parse_llm_response(md, task=task)
        assert task.rewritten_data == data

    def test_invalid_json(self) -> None:
        task = RewriteHistory(original_text='', model_name='test')
        _parse_llm_response('This is not JSON', task=task)
        assert task.rewritten_data is None

    def test_empty_keywords(self) -> None:
        task = RewriteHistory(original_text='', model_name='test')
        data = {'summary': 'Test'}
        _parse_llm_response(json.dumps(data), task=task)
        assert task.keywords_added == []


class TestCreateRewriteTask:
    """Тесты create_rewrite_task()."""

    async def test_success(self, session: AsyncSession, test_user: User) -> None:
        """Успешное создание задачи."""
        resume = Resume(
            user_id=test_user.id,
            title='CV',
            file_path='p.pdf',
            file_format='pdf',
            file_size_bytes=100,
            raw_text='My resume text',
        )
        vacancy = Vacancy(
            user_id=test_user.id,
            title='Dev',
            description='Python developer',
        )
        session.add_all([resume, vacancy])
        await session.flush()

        task = await create_rewrite_task(
            session,
            user_id=test_user.id,
            resume_id=resume.id,
            vacancy_id=vacancy.id,
        )
        assert task.status == RewriteStatus.PENDING
        assert task.resume_id == resume.id
        assert task.vacancy_id == vacancy.id
        assert task.model_name == 'gigachat-pro'

    async def test_resume_not_found(self, session: AsyncSession, test_user: User) -> None:
        """Нет резюме → ResumeNotFound."""
        vacancy = Vacancy(user_id=test_user.id, title='V', description='D')
        session.add(vacancy)
        await session.flush()

        with pytest.raises(ResumeNotFound):
            await create_rewrite_task(
                session,
                user_id=test_user.id,
                resume_id=uuid4(),
                vacancy_id=vacancy.id,
            )

    async def test_vacancy_not_found(self, session: AsyncSession, test_user: User) -> None:
        """Нет вакансии → VacancyNotFound."""
        resume = Resume(
            user_id=test_user.id,
            title='CV',
            file_path='p.pdf',
            file_format='pdf',
            file_size_bytes=100,
        )
        session.add(resume)
        await session.flush()

        with pytest.raises(VacancyNotFound):
            await create_rewrite_task(
                session,
                user_id=test_user.id,
                resume_id=resume.id,
                vacancy_id=uuid4(),
            )

    async def test_raw_text_none_uses_empty_string(
        self,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        """raw_text=None → original_text='' (не должен падать на NOT NULL)."""
        resume = Resume(
            user_id=test_user.id,
            title='CV',
            file_path='p.pdf',
            file_format='pdf',
            file_size_bytes=100,
            raw_text=None,
        )
        vacancy = Vacancy(
            user_id=test_user.id,
            title='Dev',
            description='Python developer',
        )
        session.add_all([resume, vacancy])
        await session.flush()

        task = await create_rewrite_task(
            session,
            user_id=test_user.id,
            resume_id=resume.id,
            vacancy_id=vacancy.id,
        )
        assert task.original_text == ''
        assert task.status == RewriteStatus.PENDING


class TestExecuteRewrite:
    """Тесты execute_rewrite()."""

    @patch('app.rewriter.service.LLMClientFactory')
    async def test_success(
        self,
        mock_factory: MagicMock,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        """Успешная оптимизация."""
        # Подготовка данных
        resume = Resume(
            user_id=test_user.id,
            title='CV',
            file_path='p.pdf',
            file_format='pdf',
            file_size_bytes=100,
            raw_text='Опыт работы Python разработчик, управлял командой из 5 человек',
        )
        vacancy = Vacancy(
            user_id=test_user.id,
            title='Senior Python',
            description='Требуется senior Python developer с опытом FastAPI',
        )
        session.add_all([resume, vacancy])
        await session.flush()

        task = RewriteHistory(
            user_id=test_user.id,
            resume_id=resume.id,
            vacancy_id=vacancy.id,
            original_text=resume.raw_text,
            model_name='gigachat-pro',
            status=RewriteStatus.PENDING,
        )
        session.add(task)
        await session.flush()

        # Mock LLM
        llm_response = json.dumps(
            {
                'summary': 'Senior Python разработчик',
                'experience': [],
                'skills': ['Python', 'FastAPI'],
                'keywords_added': ['FastAPI'],
            }
        )
        mock_client = AsyncMock()
        mock_client.complete.return_value = llm_response
        mock_client.close = AsyncMock()
        mock_factory.create.return_value = mock_client

        result = await execute_rewrite(session, task_id=task.id)
        assert result.status == RewriteStatus.COMPLETED
        assert result.rewritten_text == llm_response
        assert result.processing_time_ms is not None
        assert result.match_score_before is not None
        assert result.match_score_after is not None

    async def test_task_not_found(self, session: AsyncSession) -> None:
        """Задача не найдена → RewriteTaskNotFound."""
        with pytest.raises(RewriteTaskNotFound):
            await execute_rewrite(session, task_id=uuid4())

    @patch('app.rewriter.service.LLMClientFactory')
    async def test_llm_failure(
        self,
        mock_factory: MagicMock,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        """Ошибка LLM → статус FAILED."""
        resume = Resume(
            user_id=test_user.id,
            title='CV',
            file_path='p.pdf',
            file_format='pdf',
            file_size_bytes=100,
            raw_text='text',
        )
        vacancy = Vacancy(
            user_id=test_user.id,
            title='Dev',
            description='desc',
        )
        session.add_all([resume, vacancy])
        await session.flush()

        task = RewriteHistory(
            user_id=test_user.id,
            resume_id=resume.id,
            vacancy_id=vacancy.id,
            original_text='text',
            model_name='gigachat-pro',
            status=RewriteStatus.PENDING,
        )
        session.add(task)
        await session.flush()

        mock_client = AsyncMock()
        mock_client.complete.side_effect = RuntimeError('LLM exploded')
        mock_client.close = AsyncMock()
        mock_factory.create.return_value = mock_client

        result = await execute_rewrite(session, task_id=task.id)
        assert result.status == RewriteStatus.FAILED
        assert 'LLM exploded' in (result.error_message or '')

    @patch('app.rewriter.service.LLMClientFactory')
    async def test_llm_retry_on_invalid_json(
        self,
        mock_factory: MagicMock,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        """Невалидный JSON на 1-й попытке → retry → валидный на 2-й."""
        resume = Resume(
            user_id=test_user.id,
            title='CV',
            file_path='p.pdf',
            file_format='pdf',
            file_size_bytes=100,
            raw_text='Python разработчик, опыт 5 лет',
        )
        vacancy = Vacancy(
            user_id=test_user.id,
            title='Senior Python',
            description='Python developer',
        )
        session.add_all([resume, vacancy])
        await session.flush()

        task = RewriteHistory(
            user_id=test_user.id,
            resume_id=resume.id,
            vacancy_id=vacancy.id,
            original_text=resume.raw_text,
            model_name='gigachat-pro',
            status=RewriteStatus.PENDING,
        )
        session.add(task)
        await session.flush()

        valid_json = json.dumps(
            {
                'summary': 'Senior Python dev',
                'skills': ['Python'],
                'keywords_added': ['Python'],
            }
        )

        mock_client = AsyncMock()
        # Первая попытка — невалидный JSON, вторая — валидный
        mock_client.complete = AsyncMock(
            side_effect=['This is not valid JSON at all', valid_json],
        )
        mock_client.close = AsyncMock()
        mock_factory.create.return_value = mock_client

        result = await execute_rewrite(session, task_id=task.id)
        assert result.status == RewriteStatus.COMPLETED
        assert result.rewritten_data is not None
        assert mock_client.complete.call_count == 2


class TestGetTask:
    """Тесты get_task()."""

    async def test_existing(self, session: AsyncSession, test_user: User) -> None:
        task = RewriteHistory(
            user_id=test_user.id,
            resume_id=uuid4(),
            vacancy_id=uuid4(),
            original_text='Original text',
            model_name='gigachat-pro',
            status=RewriteStatus.PENDING,
        )
        session.add(task)
        await session.flush()

        result = await get_task(session, task_id=task.id, user_id=test_user.id)
        assert result.id == task.id

    async def test_nonexistent(self, session: AsyncSession, test_user: User) -> None:
        with pytest.raises(RewriteTaskNotFound):
            await get_task(session, task_id=uuid4(), user_id=test_user.id)


class TestListHistory:
    """Тесты list_history()."""

    async def test_empty(self, session: AsyncSession, test_user: User) -> None:
        items, total = await list_history(session, user_id=test_user.id)
        assert total >= 0
        assert isinstance(items, (list, tuple))

    async def test_with_items(self, session: AsyncSession, test_user: User) -> None:
        for i in range(3):
            t = RewriteHistory(
                user_id=test_user.id,
                resume_id=uuid4(),
                vacancy_id=uuid4(),
                original_text=f'Original text {i}',
                model_name='gigachat-pro',
                status=RewriteStatus.COMPLETED,
            )
            session.add(t)
        await session.flush()

        items, total = await list_history(session, user_id=test_user.id, limit=2)
        assert len(items) == 2
        assert total >= 3

"""Тесты rewriter/router.py — API оптимизации через HTTP."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.resumes.models import Resume
from app.rewriter.models import RewriteHistory, RewriteStatus
from app.vacancies.models import Vacancy


class TestCreateRewrite:
    """POST /api/v1/rewrite."""

    async def test_no_auth(self, client: AsyncClient) -> None:
        """Без JWT → 401."""
        resp = await client.post(
            '/api/v1/rewrite',
            json={
                'resume_id': str(uuid4()),
                'vacancy_id': str(uuid4()),
            },
        )
        assert resp.status_code == 401

    @patch(
        'app.settings.service.get_user_setting',
        new_callable=AsyncMock,
        return_value='fake-api-key',
    )
    @patch('app.rewriter.router.execute_rewrite_task')
    async def test_success(
        self,
        mock_celery: AsyncMock,
        mock_get_key: AsyncMock,
        auth_client: AsyncClient,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        """Успешный запуск оптимизации."""
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

        mock_celery.delay = lambda *a: None

        resp = await auth_client.post(
            '/api/v1/rewrite',
            json={
                'resume_id': str(resume.id),
                'vacancy_id': str(vacancy.id),
            },
        )
        assert resp.status_code == 202
        data = resp.json()
        assert 'task_id' in data

    @patch('app.rewriter.router.execute_rewrite_task')
    async def test_exhausted_user(
        self,
        mock_celery: AsyncMock,
        client: AsyncClient,
        session: AsyncSession,
        exhausted_user: User,
    ) -> None:
        """Исчерпанный лимит → 429."""
        from app.core.security import create_access_token

        token = create_access_token(exhausted_user.id)
        headers = {'Authorization': f'Bearer {token}'}

        resp = await client.post(
            '/api/v1/rewrite',
            json={
                'resume_id': str(uuid4()),
                'vacancy_id': str(uuid4()),
            },
            headers=headers,
        )
        assert resp.status_code == 429


class TestGetRewriteStatus:
    """GET /api/v1/rewrite/{task_id}/status."""

    async def test_no_auth(self, client: AsyncClient) -> None:
        resp = await client.get(f'/api/v1/rewrite/{uuid4()}/status')
        assert resp.status_code == 401

    async def test_not_found(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.get(f'/api/v1/rewrite/{uuid4()}/status')
        assert resp.status_code == 404

    async def test_completed_status(
        self,
        auth_client: AsyncClient,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        task = RewriteHistory(
            user_id=test_user.id,
            resume_id=uuid4(),
            vacancy_id=uuid4(),
            original_text='Original resume text',
            model_name='gigachat-pro',
            status=RewriteStatus.COMPLETED,
        )
        session.add(task)
        await session.flush()

        resp = await auth_client.get(f'/api/v1/rewrite/{task.id}/status')
        assert resp.status_code == 200
        data = resp.json()
        assert data['progress'] == 100
        assert data['step'] == 'completed'

    async def test_processing_status(
        self,
        auth_client: AsyncClient,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        """Статус processing → progress=50, step='rewriting'."""
        task = RewriteHistory(
            user_id=test_user.id,
            resume_id=uuid4(),
            vacancy_id=uuid4(),
            original_text='Original resume text',
            model_name='gigachat-pro',
            status=RewriteStatus.PROCESSING,
        )
        session.add(task)
        await session.flush()

        resp = await auth_client.get(f'/api/v1/rewrite/{task.id}/status')
        assert resp.status_code == 200
        data = resp.json()
        assert data['progress'] == 50
        assert data['step'] == 'rewriting'

    async def test_failed_status(
        self,
        auth_client: AsyncClient,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        """Статус failed → progress=0, step='failed'."""
        task = RewriteHistory(
            user_id=test_user.id,
            resume_id=uuid4(),
            vacancy_id=uuid4(),
            original_text='Original resume text',
            model_name='gigachat-pro',
            status=RewriteStatus.FAILED,
        )
        session.add(task)
        await session.flush()

        resp = await auth_client.get(f'/api/v1/rewrite/{task.id}/status')
        assert resp.status_code == 200
        data = resp.json()
        assert data['progress'] == 0
        assert data['step'] == 'failed'

    async def test_pending_status(
        self,
        auth_client: AsyncClient,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        """Статус pending → progress=0, step='pending'."""
        task = RewriteHistory(
            user_id=test_user.id,
            resume_id=uuid4(),
            vacancy_id=uuid4(),
            original_text='Original resume text',
            model_name='gigachat-pro',
            status=RewriteStatus.PENDING,
        )
        session.add(task)
        await session.flush()

        resp = await auth_client.get(f'/api/v1/rewrite/{task.id}/status')
        assert resp.status_code == 200
        data = resp.json()
        assert data['progress'] == 0
        assert data['step'] == 'pending'


class TestGetRewriteResult:
    """GET /api/v1/rewrite/{task_id}/result."""

    async def test_not_found(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.get(f'/api/v1/rewrite/{uuid4()}/result')
        assert resp.status_code == 404

    async def test_success(
        self,
        auth_client: AsyncClient,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        """Получение результата оптимизации."""
        task = RewriteHistory(
            user_id=test_user.id,
            resume_id=uuid4(),
            vacancy_id=uuid4(),
            original_text='Original resume text',
            model_name='gigachat-pro',
            status=RewriteStatus.COMPLETED,
            rewritten_text='Optimized text',
            match_score_before=0.4,
            match_score_after=0.85,
        )
        session.add(task)
        await session.flush()

        resp = await auth_client.get(f'/api/v1/rewrite/{task.id}/result')
        assert resp.status_code == 200


class TestListHistory:
    """GET /api/v1/rewrite/history."""

    async def test_empty(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.get('/api/v1/rewrite/history')
        assert resp.status_code == 200
        data = resp.json()
        assert 'items' in data
        assert 'total' in data

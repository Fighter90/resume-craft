"""Тесты export/router.py — API экспорта."""

from __future__ import annotations

from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.rewriter.models import RewriteHistory, RewriteStatus


class TestExportDocx:
    """GET /api/v1/export/{task_id}/docx."""

    async def test_no_auth(self, client: AsyncClient) -> None:
        resp = await client.get(f'/api/v1/export/{uuid4()}/docx')
        assert resp.status_code == 401

    async def test_not_found(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.get(f'/api/v1/export/{uuid4()}/docx')
        assert resp.status_code == 404

    async def test_success(
        self,
        auth_client: AsyncClient,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        """Экспорт с текстом → DOCX."""
        task = RewriteHistory(
            user_id=test_user.id,
            resume_id=uuid4(),
            vacancy_id=uuid4(),
            original_text='Original resume text',
            model_name='gigachat-pro',
            status=RewriteStatus.COMPLETED,
            rewritten_text='Optimized resume text here',
        )
        session.add(task)
        await session.flush()

        resp = await auth_client.get(f'/api/v1/export/{task.id}/docx')
        assert resp.status_code == 200
        assert 'application/vnd.openxmlformats' in resp.headers['content-type']
        assert resp.content[:2] == b'PK'

    async def test_no_data(
        self,
        auth_client: AsyncClient,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        """Нет данных для экспорта → 404."""
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

        resp = await auth_client.get(f'/api/v1/export/{task.id}/docx')
        assert resp.status_code == 404

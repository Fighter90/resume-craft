"""Тесты для исправлений v5 — модуль resumes."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.resumes.service import delete_resume


class TestDeleteResumeV5:
    """Исправление v5: delete_resume корректно обрабатывает пустой file_path."""

    @pytest.mark.asyncio
    async def test_no_file_deletion_for_text_resume(self) -> None:
        """Текстовое резюме (file_path='') — storage.delete не вызывается."""
        session = AsyncMock(spec=AsyncSession)
        resume = MagicMock()
        resume.id = uuid4()
        resume.user_id = uuid4()
        resume.file_path = ''

        with (
            patch('app.resumes.service.get_resume', return_value=resume),
            patch('app.resumes.service.file_storage') as fs,
        ):
            await delete_resume(session, resume_id=resume.id, user_id=resume.user_id)
            fs.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_file_deletion_for_none_file_path(self) -> None:
        """file_path=None — storage.delete не вызывается."""
        session = AsyncMock(spec=AsyncSession)
        resume = MagicMock()
        resume.id = uuid4()
        resume.user_id = uuid4()
        resume.file_path = None

        with (
            patch('app.resumes.service.get_resume', return_value=resume),
            patch('app.resumes.service.file_storage') as fs,
        ):
            await delete_resume(session, resume_id=resume.id, user_id=resume.user_id)
            fs.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_file_not_found_suppressed(self) -> None:
        """FileNotFoundError не роняет удаление."""
        session = AsyncMock(spec=AsyncSession)
        resume = MagicMock()
        resume.id = uuid4()
        resume.user_id = uuid4()
        resume.file_path = 'uploads/missing.pdf'

        with (
            patch('app.resumes.service.get_resume', return_value=resume),
            patch('app.resumes.service.file_storage') as fs,
        ):
            fs.delete = AsyncMock(side_effect=FileNotFoundError)
            await delete_resume(session, resume_id=resume.id, user_id=resume.user_id)
            session.delete.assert_awaited_once_with(resume)

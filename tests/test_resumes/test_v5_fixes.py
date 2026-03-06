"""Тесты для исправлений v5 — модуль resumes (soft-delete)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.resumes.service import delete_resume


class TestDeleteResumeV5:
    """Soft-delete: delete_resume устанавливает deleted_at вместо удаления."""

    @pytest.mark.asyncio
    async def test_soft_delete_sets_deleted_at(self) -> None:
        """Soft-delete устанавливает deleted_at на резюме."""
        session = AsyncMock(spec=AsyncSession)
        resume = MagicMock()
        resume.id = uuid4()
        resume.user_id = uuid4()
        resume.deleted_at = None

        with patch('app.resumes.service.get_resume', return_value=resume):
            await delete_resume(session, resume_id=resume.id, user_id=resume.user_id)
            assert resume.deleted_at is not None

    @pytest.mark.asyncio
    async def test_soft_delete_does_not_call_session_delete(self) -> None:
        """Soft-delete не вызывает session.delete()."""
        session = AsyncMock(spec=AsyncSession)
        resume = MagicMock()
        resume.id = uuid4()
        resume.user_id = uuid4()
        resume.deleted_at = None

        with patch('app.resumes.service.get_resume', return_value=resume):
            await delete_resume(session, resume_id=resume.id, user_id=resume.user_id)
            session.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_soft_delete_does_not_touch_file_storage(self) -> None:
        """Soft-delete не обращается к файловому хранилищу."""
        session = AsyncMock(spec=AsyncSession)
        resume = MagicMock()
        resume.id = uuid4()
        resume.user_id = uuid4()
        resume.file_path = 'uploads/file.pdf'
        resume.deleted_at = None

        with (
            patch('app.resumes.service.get_resume', return_value=resume),
            patch('app.resumes.service.file_storage') as fs,
        ):
            await delete_resume(session, resume_id=resume.id, user_id=resume.user_id)
            fs.delete.assert_not_called()

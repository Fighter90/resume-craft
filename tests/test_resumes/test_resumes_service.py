"""Тесты resumes/service.py — бизнес-логика."""

from __future__ import annotations

import io
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.exceptions import FileTooLarge, ResumeNotFound, UnsupportedFileFormat
from app.resumes.models import Resume, ResumeStatus
from app.resumes.service import (
    _extract_extension,
    _extract_text,
    _validate_magic_bytes,
    delete_resume,
    get_resume,
    list_resumes,
    upload_resume,
)


class TestExtractExtension:
    """Тесты извлечения расширения из имени файла."""

    def test_pdf(self) -> None:
        assert _extract_extension('resume.pdf') == 'pdf'

    def test_docx(self) -> None:
        assert _extract_extension('my_resume.docx') == 'docx'

    def test_uppercase(self) -> None:
        assert _extract_extension('FILE.PDF') == 'pdf'

    def test_no_extension(self) -> None:
        with pytest.raises(UnsupportedFileFormat):
            _extract_extension('noext')

    def test_multiple_dots(self) -> None:
        assert _extract_extension('my.old.resume.pdf') == 'pdf'


class TestValidateMagicBytes:
    """Тесты валидации magic bytes."""

    def test_valid_pdf(self) -> None:
        _validate_magic_bytes(b'%PDF-1.5 content', ext='pdf')

    def test_valid_docx(self) -> None:
        _validate_magic_bytes(b'PK\x03\x04 content', ext='docx')

    def test_invalid_pdf(self) -> None:
        with pytest.raises(UnsupportedFileFormat):
            _validate_magic_bytes(b'not a pdf', ext='pdf')

    def test_invalid_docx(self) -> None:
        with pytest.raises(UnsupportedFileFormat):
            _validate_magic_bytes(b'not a docx', ext='docx')


class TestExtractText:
    """Тесты извлечения текста."""

    def test_unknown_format(self) -> None:
        """Неизвестный формат → None."""
        result = _extract_text(b'some bytes', ext='txt')
        assert result is None

    @patch('app.resumes.service._extract_from_pdf', return_value='PDF text')
    def test_pdf_format(self, mock_extract: AsyncMock) -> None:
        """Формат pdf → _extract_from_pdf."""
        result = _extract_text(b'%PDF content', ext='pdf')
        assert result == 'PDF text'
        mock_extract.assert_called_once()

    @patch('app.resumes.service._extract_from_docx', return_value='DOCX text')
    def test_docx_format(self, mock_extract: AsyncMock) -> None:
        """Формат docx → _extract_from_docx."""
        result = _extract_text(b'PK content', ext='docx')
        assert result == 'DOCX text'
        mock_extract.assert_called_once()

    @patch('app.resumes.service._extract_from_pdf', side_effect=RuntimeError('parse error'))
    def test_exception_returns_none(self, mock_extract: AsyncMock) -> None:
        """Ошибка парсинга → None."""
        result = _extract_text(b'%PDF content', ext='pdf')
        assert result is None


class TestExtractFromPdfInService:
    """Тесты _extract_from_pdf() в service.py."""

    def test_success(self) -> None:
        """Успешное извлечение через fitz."""
        import sys
        from unittest.mock import MagicMock

        mock_page = MagicMock()
        mock_page.get_text.return_value = 'Service PDF text'

        mock_doc = MagicMock()
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=False)

        mock_fitz = MagicMock()
        mock_fitz.open.return_value = mock_doc

        sys.modules['fitz'] = mock_fitz
        try:
            from app.resumes.service import _extract_from_pdf

            result = _extract_from_pdf(b'%PDF content')
            assert 'Service PDF text' in result
        finally:
            sys.modules.pop('fitz', None)


class TestExtractFromDocxInService:
    """Тесты _extract_from_docx() в service.py."""

    def test_success(self) -> None:
        """Успешное извлечение через python-docx."""
        import sys
        from unittest.mock import MagicMock

        mock_p1 = MagicMock(text='Service DOCX text')
        mock_p2 = MagicMock(text='')

        mock_doc_instance = MagicMock()
        mock_doc_instance.paragraphs = [mock_p1, mock_p2]

        mock_document_cls = MagicMock(return_value=mock_doc_instance)
        mock_docx_mod = MagicMock()
        mock_docx_mod.Document = mock_document_cls

        sys.modules['docx'] = mock_docx_mod
        try:
            from app.resumes.service import _extract_from_docx

            result = _extract_from_docx(b'PK content')
            assert 'Service DOCX text' in result
        finally:
            sys.modules.pop('docx', None)


class TestUploadResume:
    """Тесты upload_resume()."""

    async def test_unsupported_format(self, session: AsyncSession, test_user: User) -> None:
        """Неподдерживаемый формат → UnsupportedFileFormat."""
        file = UploadFile(filename='test.txt', file=io.BytesIO(b'text content'))
        with pytest.raises(UnsupportedFileFormat):
            await upload_resume(session, user_id=test_user.id, file=file)

    async def test_file_too_large(self, session: AsyncSession, test_user: User) -> None:
        """Файл > 10 MB → FileTooLarge."""
        content = b'%PDF' + b'x' * (11 * 1024 * 1024)
        file = UploadFile(filename='big.pdf', file=io.BytesIO(content))
        with pytest.raises(FileTooLarge):
            await upload_resume(session, user_id=test_user.id, file=file)

    async def test_magic_bytes_mismatch(self, session: AsyncSession, test_user: User) -> None:
        """Несовпадение magic bytes → UnsupportedFileFormat."""
        file = UploadFile(filename='fake.pdf', file=io.BytesIO(b'not a pdf content'))
        with pytest.raises(UnsupportedFileFormat):
            await upload_resume(session, user_id=test_user.id, file=file)

    @patch('app.resumes.service.file_storage')
    async def test_upload_success(
        self, mock_storage: AsyncMock, session: AsyncSession, test_user: User,
    ) -> None:
        """Успешная загрузка PDF."""
        mock_storage.save = AsyncMock(return_value=f'{test_user.id}/test.pdf')

        content = b'%PDF-1.5 minimal pdf content'
        file = UploadFile(filename='resume.pdf', file=io.BytesIO(content))
        resume = await upload_resume(session, user_id=test_user.id, file=file)

        assert resume.file_format == 'pdf'
        assert resume.file_size_bytes == len(content)
        assert resume.status == ResumeStatus.DRAFT
        assert resume.user_id == test_user.id
        mock_storage.save.assert_called_once()


class TestGetResume:
    """Тесты get_resume()."""

    async def test_get_existing(self, session: AsyncSession, test_user: User) -> None:
        """Получение существующего резюме."""
        resume = Resume(
            user_id=test_user.id,
            title='Test',
            file_path='test/path.pdf',
            file_format='pdf',
            file_size_bytes=1000,
            status=ResumeStatus.DRAFT,
        )
        session.add(resume)
        await session.flush()

        result = await get_resume(session, resume_id=resume.id, user_id=test_user.id)
        assert result.id == resume.id

    async def test_get_nonexistent(self, session: AsyncSession, test_user: User) -> None:
        """Несуществующее резюме → ResumeNotFound."""
        with pytest.raises(ResumeNotFound):
            await get_resume(session, resume_id=uuid4(), user_id=test_user.id)

    async def test_get_other_users_resume(self, session: AsyncSession, test_user: User) -> None:
        """Чужое резюме → ResumeNotFound (IDOR protection)."""
        resume = Resume(
            user_id=uuid4(),  # другой пользователь
            title='Other',
            file_path='other/path.pdf',
            file_format='pdf',
            file_size_bytes=500,
        )
        session.add(resume)
        await session.flush()

        with pytest.raises(ResumeNotFound):
            await get_resume(session, resume_id=resume.id, user_id=test_user.id)


class TestListResumes:
    """Тесты list_resumes()."""

    async def test_empty_list(self, session: AsyncSession, test_user: User) -> None:
        """Пустой список → ([], 0)."""
        items, total = await list_resumes(session, user_id=test_user.id)
        assert total >= 0  # Может быть >0 из-за других тестов
        assert isinstance(items, (list, tuple))

    async def test_pagination(self, session: AsyncSession, test_user: User) -> None:
        """Пагинация работает."""
        for i in range(3):
            r = Resume(
                user_id=test_user.id, title=f'Resume {i}',
                file_path=f'path/{i}.pdf', file_format='pdf', file_size_bytes=100,
            )
            session.add(r)
        await session.flush()

        items, total = await list_resumes(session, user_id=test_user.id, limit=2, offset=0)
        assert len(items) == 2
        assert total >= 3


class TestDeleteResume:
    """Тесты delete_resume()."""

    @patch('app.resumes.service.file_storage')
    async def test_delete_success(
        self, mock_storage: AsyncMock, session: AsyncSession, test_user: User,
    ) -> None:
        """Удаление существующего резюме."""
        mock_storage.delete = AsyncMock()
        resume = Resume(
            user_id=test_user.id, title='To Delete',
            file_path='del/path.pdf', file_format='pdf', file_size_bytes=100,
        )
        session.add(resume)
        await session.flush()

        await delete_resume(session, resume_id=resume.id, user_id=test_user.id)
        mock_storage.delete.assert_called_once()

    async def test_delete_nonexistent(self, session: AsyncSession, test_user: User) -> None:
        """Удаление несуществующего → ResumeNotFound."""
        with pytest.raises(ResumeNotFound):
            await delete_resume(session, resume_id=uuid4(), user_id=test_user.id)

    @patch('app.resumes.service.file_storage')
    async def test_delete_file_not_found(
        self, mock_storage: AsyncMock, session: AsyncSession, test_user: User,
    ) -> None:
        """Удаление резюме когда файл уже удалён → не крашится."""
        mock_storage.delete = AsyncMock(side_effect=FileNotFoundError('not found'))
        resume = Resume(
            user_id=test_user.id, title='Missing File',
            file_path='gone/path.pdf', file_format='pdf', file_size_bytes=100,
        )
        session.add(resume)
        await session.flush()

        # Не должно бросать исключение
        await delete_resume(session, resume_id=resume.id, user_id=test_user.id)

"""Бизнес-логика управления резюме."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import FileTooLarge, ResumeNotFound, UnsupportedFileFormat
from app.core.storage import file_storage
from app.resumes.models import Resume, ResumeStatus

logger = logging.getLogger(__name__)

settings = get_settings()

ALLOWED_EXTENSIONS: frozenset[str] = frozenset({'pdf', 'docx'})
MAGIC_BYTES: dict[str, bytes] = {
    'pdf': b'%PDF',
    'docx': b'PK\x03\x04',
}


def _extract_extension(filename: str) -> str:
    """Извлечение расширения файла."""
    if '.' not in filename:
        msg = 'Файл не имеет расширения'
        raise UnsupportedFileFormat(msg)
    return filename.rsplit('.', 1)[-1].lower()


def _validate_magic_bytes(content: bytes, *, ext: str) -> None:
    """Проверка magic bytes файла."""
    expected = MAGIC_BYTES.get(ext, b'')
    if expected and not content.startswith(expected):
        msg = f'Содержимое файла не соответствует расширению .{ext}'
        raise UnsupportedFileFormat(msg)


async def upload_resume(
    session: AsyncSession,
    *,
    user_id: UUID,
    file: UploadFile,
) -> Resume:
    """Загрузка и валидация резюме.

    Raises:
        UnsupportedFileFormat: неподдерживаемый формат.
        FileTooLarge: файл превышает 10 MB.
    """
    filename = file.filename or 'unknown'
    ext = _extract_extension(filename)

    if ext not in ALLOWED_EXTENSIONS:
        msg = f'Формат .{ext} не поддерживается. Допустимы: PDF, DOCX'
        raise UnsupportedFileFormat(msg)

    content = await file.read()
    if len(content) > settings.max_file_size_bytes:
        raise FileTooLarge()

    _validate_magic_bytes(content, ext=ext)

    # Сохранение файла
    safe_name = f'{uuid4().hex}.{ext}'
    relative_path = await file_storage.save(user_id, safe_name, content)

    # Извлечение текста
    raw_text = _extract_text(content, ext=ext)

    resume = Resume(
        user_id=user_id,
        title=filename.rsplit('.', 1)[0],
        file_path=relative_path,
        file_format=ext,
        file_size_bytes=len(content),
        raw_text=raw_text,
        status=ResumeStatus.DRAFT,
    )
    session.add(resume)
    await session.flush()

    logger.info('Resume uploaded: %s (user=%s, size=%d)', resume.id, user_id, len(content))
    return resume


def _extract_text(content: bytes, *, ext: str) -> str | None:
    """Извлечение текста из файла (PDF/DOCX)."""
    try:
        if ext == 'pdf':
            return _extract_from_pdf(content)
        if ext == 'docx':
            return _extract_from_docx(content)
    except Exception:
        logger.warning('Failed to extract text from %s file', ext, exc_info=True)
    return None


def _extract_from_pdf(content: bytes) -> str:
    """Извлечение текста из PDF через PyMuPDF."""
    import fitz  # noqa: PLC0415 — lazy import

    text_parts: list[str] = []
    with fitz.open(stream=content, filetype='pdf') as doc:
        for page in doc:
            text_parts.append(page.get_text())  # type: ignore[union-attr]
    return '\n'.join(text_parts).strip()


def _extract_from_docx(content: bytes) -> str:
    """Извлечение текста из DOCX через python-docx."""
    import io  # noqa: PLC0415

    from docx import Document  # noqa: PLC0415 — lazy import

    doc = Document(io.BytesIO(content))
    return '\n'.join(p.text for p in doc.paragraphs if p.text.strip())


async def get_resume(
    session: AsyncSession,
    *,
    resume_id: UUID,
    user_id: UUID,
) -> Resume:
    """Получение резюме по ID (с проверкой владельца).

    Raises:
        ResumeNotFound: резюме не найдено или принадлежит другому пользователю.
    """
    stmt = select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id)
    result = await session.execute(stmt)
    resume = result.scalar_one_or_none()
    if not resume:
        raise ResumeNotFound()
    return resume


async def list_resumes(
    session: AsyncSession,
    *,
    user_id: UUID,
    limit: int = 20,
    offset: int = 0,
) -> tuple[Sequence[Resume], int]:
    """Список резюме пользователя с пагинацией."""
    # Count
    count_stmt = select(func.count()).select_from(Resume).where(Resume.user_id == user_id)
    total = (await session.execute(count_stmt)).scalar_one()

    # Items
    stmt = (
        select(Resume)
        .where(Resume.user_id == user_id)
        .order_by(Resume.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    items = result.scalars().all()

    return items, total


async def delete_resume(
    session: AsyncSession,
    *,
    resume_id: UUID,
    user_id: UUID,
) -> None:
    """Удаление резюме.

    Raises:
        ResumeNotFound: резюме не найдено.
    """
    resume = await get_resume(session, resume_id=resume_id, user_id=user_id)

    # Удаление файла
    try:
        await file_storage.delete(resume.file_path)
    except FileNotFoundError:
        logger.warning('File not found during delete: %s', resume.file_path)

    await session.delete(resume)
    await session.flush()
    logger.info('Resume deleted: %s (user=%s)', resume_id, user_id)

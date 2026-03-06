"""Роутер экспорта: /api/v1/export/*."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.database import get_session
from app.core.dependencies import get_current_user
from app.core.exceptions import RewriteTaskNotFound
from app.export.service import generate_docx, generate_pdf, generate_txt
from app.rewriter import service as rewrite_service

router = APIRouter(prefix='/export', tags=['export'])


# ---- helpers ----

async def _get_task_data(
    task_id: UUID,
    *,
    user_id: UUID,
    session: AsyncSession,
) -> tuple[dict | None, str | None]:
    """Извлечь rewritten_data / rewritten_text из задачи или поднять 404."""
    task = await rewrite_service.get_task(session, task_id=task_id, user_id=user_id)
    if not task.rewritten_text and not task.rewritten_data:
        raise RewriteTaskNotFound()
    return task.rewritten_data, task.rewritten_text


@router.get(
    '/{task_id}/docx',
    summary='Экспорт оптимизированного резюме в DOCX',
    responses={200: {
        'content': {'application/vnd.openxmlformats-officedocument.wordprocessingml.document': {}},
        'description': 'DOCX-файл',
    }},
)
async def export_docx(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Экспорт результата оптимизации в формате DOCX."""
    data, raw = await _get_task_data(task_id, user_id=current_user.id, session=session)
    content = generate_docx(data, raw_text=raw)
    return Response(
        content=content,
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        headers={
            'Content-Disposition': f'attachment; filename="resume_{task_id}.docx"',
            'Content-Length': str(len(content)),
        },
    )


@router.get(
    '/{task_id}/pdf',
    summary='Экспорт оптимизированного резюме в PDF',
    responses={200: {
        'content': {'application/pdf': {}},
        'description': 'PDF-файл',
    }},
)
async def export_pdf(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Экспорт результата оптимизации в формате PDF."""
    data, raw = await _get_task_data(task_id, user_id=current_user.id, session=session)
    content = generate_pdf(data, raw_text=raw)
    return Response(
        content=content,
        media_type='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename="resume_{task_id}.pdf"',
            'Content-Length': str(len(content)),
        },
    )


@router.get(
    '/{task_id}/txt',
    summary='Экспорт оптимизированного резюме в TXT',
    responses={200: {
        'content': {'text/plain': {}},
        'description': 'TXT-файл',
    }},
)
async def export_txt(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Экспорт результата оптимизации в формате TXT."""
    data, raw = await _get_task_data(task_id, user_id=current_user.id, session=session)
    content = generate_txt(data, raw_text=raw)
    return Response(
        content=content,
        media_type='text/plain; charset=utf-8',
        headers={
            'Content-Disposition': f'attachment; filename="resume_{task_id}.txt"',
            'Content-Length': str(len(content)),
        },
    )

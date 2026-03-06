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
from app.export.service import generate_docx
from app.rewriter import service as rewrite_service

router = APIRouter(prefix='/export', tags=['export'])


@router.get(
    '/{task_id}/docx',
    summary='Экспорт оптимизированного резюме в DOCX',
    responses={
        200: {
            'content': {
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document': {},
            },
            'description': 'DOCX-файл',
        },
    },
)
async def export_docx(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Экспорт результата оптимизации в формате DOCX."""
    task = await rewrite_service.get_task(session, task_id=task_id, user_id=current_user.id)

    if not task.rewritten_text and not task.rewritten_data:
        raise RewriteTaskNotFound()

    docx_bytes = generate_docx(
        rewritten_data=task.rewritten_data,
        raw_text=task.rewritten_text,
    )

    return Response(
        content=docx_bytes,
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        headers={
            'Content-Disposition': f'attachment; filename="resume_{task_id}.docx"',
            'Content-Length': str(len(docx_bytes)),
        },
    )

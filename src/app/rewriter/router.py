"""Роутер оптимизации: /api/v1/rewrite/*."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.database import get_session
from app.core.dependencies import get_current_user
from app.core.exceptions import TariffLimitExceeded
from app.rewriter import service as rewrite_service
from app.rewriter.schemas import (
    RewriteHistoryResponse,
    RewriteRequest,
    RewriteResultResponse,
    RewriteStatusResponse,
    RewriteTaskResponse,
)
from app.rewriter.tasks import execute_rewrite_task

router = APIRouter(prefix='/rewrite', tags=['rewrite'])


@router.post(
    '',
    response_model=RewriteTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary='Запуск оптимизации резюме',
)
async def create_rewrite(
    data: RewriteRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> RewriteTaskResponse:
    """Создание задачи оптимизации → Celery queue."""
    # Проверка тарифного лимита
    if not current_user.can_optimize:
        raise TariffLimitExceeded()

    task = await rewrite_service.create_rewrite_task(
        session,
        user_id=current_user.id,
        resume_id=data.resume_id,
        vacancy_id=data.vacancy_id,
        model_name=data.model,
        openrouter_model=data.openrouter_model,
    )

    # Обновление счётчика оптимизаций
    current_user.optimizations_used += 1
    await session.flush()

    # Отправка в Celery (async)
    execute_rewrite_task.delay(str(task.id))

    return RewriteTaskResponse(task_id=task.id, status=task.status)


@router.get(
    '/{task_id}/status',
    response_model=RewriteStatusResponse,
    summary='Статус задачи оптимизации',
)
async def get_rewrite_status(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> RewriteStatusResponse:
    """Получение текущего статуса и прогресса задачи."""
    task = await rewrite_service.get_task(session, task_id=task_id, user_id=current_user.id)

    progress = 0
    step = 'pending'
    if task.status.value == 'processing':
        progress = 50
        step = 'rewriting'
    elif task.status.value == 'completed':
        progress = 100
        step = 'completed'
    elif task.status.value == 'failed':
        progress = 0
        step = 'failed'

    return RewriteStatusResponse(
        task_id=task.id,
        status=task.status,
        step=step,
        progress=progress,
        error_message=task.error_message if task.status.value == 'failed' else None,
    )


@router.get(
    '/{task_id}/result',
    response_model=RewriteResultResponse,
    summary='Результат оптимизации',
)
async def get_rewrite_result(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> RewriteResultResponse:
    """Получение полного результата оптимизации."""
    task = await rewrite_service.get_task(session, task_id=task_id, user_id=current_user.id)
    return RewriteResultResponse.model_validate(task)


@router.get(
    '/history',
    response_model=RewriteHistoryResponse,
    summary='История оптимизаций',
)
async def list_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> RewriteHistoryResponse:
    """Список всех оптимизаций пользователя."""
    items, total = await rewrite_service.list_history(
        session,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )
    return RewriteHistoryResponse(
        items=[RewriteResultResponse.model_validate(i) for i in items],
        total=total,
    )

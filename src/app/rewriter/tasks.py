"""Celery-задачи для асинхронной AI-оптимизации."""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.celery_app import celery_app
from app.core.config import get_settings
from app.core.database import _get_engine_kwargs
from app.rewriter import service as rewrite_service

logger = logging.getLogger(__name__)


@celery_app.task(  # type: ignore[untyped-decorator]
    bind=True,
    name='rewriter.execute_rewrite',
    max_retries=2,
    default_retry_delay=30,
    acks_late=True,
    reject_on_worker_lost=True,
    time_limit=120,
    soft_time_limit=90,
)
def execute_rewrite_task(self: celery_app.Task, task_id: str) -> dict[str, str]:
    """Celery-задача оптимизации резюме.

    Args:
        task_id: UUID задачи оптимизации.

    Returns:
        Словарь с ID задачи и статусом.
    """
    logger.info('Starting rewrite task: %s', task_id)

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_run_rewrite(UUID(task_id)))
        finally:
            loop.close()
        return {'task_id': task_id, 'status': result}
    except Exception as exc:
        logger.exception('Rewrite task failed: %s', task_id)
        # Retry on transient errors
        raise self.retry(exc=exc) from exc


async def _run_rewrite(task_id: UUID) -> str:
    """Запуск оптимизации в async-контексте.

    KEY-CHECK-001: Creates a fresh engine per task invocation to avoid
    stale asyncpg connection pool bound to a previous (closed) event loop.
    """
    settings = get_settings()
    engine = create_async_engine(settings.database_url, **_get_engine_kwargs())
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with factory() as session:
            try:
                task = await rewrite_service.execute_rewrite(session, task_id=task_id)
                await session.commit()
                return task.status.value
            except Exception:
                await session.rollback()
                raise
    finally:
        await engine.dispose()

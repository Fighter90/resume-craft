"""Роутер оптимизации: /api/v1/rewrite/*."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.database import get_session
from app.core.dependencies import get_current_user
from app.core.exceptions import TariffLimitExceeded
from app.core.limiter import limiter
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
@limiter.limit('10/hour')
async def create_rewrite(
    request: Request,
    data: RewriteRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> RewriteTaskResponse:
    """Создание задачи оптимизации → Celery queue."""
    # Проверка тарифного лимита
    if not current_user.can_optimize:
        raise TariffLimitExceeded(
            used=current_user.optimizations_used,
            limit=current_user.optimization_limit or 0,
        )

    # Проверка наличия API-ключа для выбранного провайдера ДО начала оптимизации
    from app.core.config import get_settings
    from app.settings.service import get_user_setting

    # Маппинг модели → имя провайдера в БД и поле в env
    _model_to_db_provider: dict[str, str] = {
        'gigachat-pro': 'gigachat',
        'gigachat-lite': 'gigachat',
        'openai': 'openai',
        'gpt-4o-mini': 'openai',
        'gpt-4o': 'openai',
        'anthropic': 'anthropic',
        'claude-sonnet': 'anthropic',
        'claude-haiku': 'anthropic',
        'openrouter': 'openrouter',
        'groq': 'groq',
    }
    _model_to_env_field: dict[str, str] = {
        'gigachat-pro': 'gigachat_credentials',
        'gigachat-lite': 'gigachat_credentials',
        'openai': 'openai_api_key',
        'gpt-4o-mini': 'openai_api_key',
        'gpt-4o': 'openai_api_key',
        'anthropic': 'anthropic_api_key',
        'claude-sonnet': 'anthropic_api_key',
        'claude-haiku': 'anthropic_api_key',
        'openrouter': 'openrouter_api_key',
        'groq': 'groq_api_key',
    }
    _model_to_display_name: dict[str, str] = {
        'gigachat-pro': 'GigaChat',
        'gigachat-lite': 'GigaChat',
        'openai': 'OpenAI',
        'gpt-4o-mini': 'OpenAI',
        'gpt-4o': 'OpenAI',
        'anthropic': 'Anthropic Claude',
        'claude-sonnet': 'Anthropic Claude',
        'claude-haiku': 'Anthropic Claude',
        'openrouter': 'OpenRouter',
        'groq': 'Groq',
    }

    db_provider = _model_to_db_provider.get(data.model, data.model)
    user_key = await get_user_setting(
        session,
        user_id=current_user.id,
        provider=db_provider,
    )
    env_field = _model_to_env_field.get(data.model, '')
    settings = get_settings()
    env_key = getattr(settings, env_field, '') if env_field else ''

    if not user_key and not (env_key and env_key.strip()):
        from fastapi import HTTPException

        display_name = _model_to_display_name.get(data.model, data.model)

        raise HTTPException(
            status_code=400,
            detail=f'API-ключ для {display_name} не настроен. '
            f'Перейдите в Настройки → AI-модели для настройки.',
        )

    task = await rewrite_service.create_rewrite_task(
        session,
        user_id=current_user.id,
        resume_id=data.resume_id,
        vacancy_id=data.vacancy_id,
        model_name=data.model,
        sub_model=data.sub_model,
    )

    # API-001/LIVE-003: НЕ инкрементируем счётчик здесь.
    # Счётчик обновляется в Celery-задаче ТОЛЬКО при status=COMPLETED.

    # KEY-CHECK-001: Коммитим сессию ДО отправки в Celery,
    # чтобы worker гарантированно видел данные задачи и ключи пользователя.
    await session.commit()

    # Отправка в Celery (async)
    execute_rewrite_task.delay(str(task.id))

    return RewriteTaskResponse(task_id=task.id, status=task.status)


# API-009: Статический маршрут /history ПЕРЕД динамическим /{task_id}
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

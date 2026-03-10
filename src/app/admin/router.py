"""Роутер админ-операций: /api/v1/admin/*.

Внимание: endpoint предназначен для QA-окружения.
Доступ защищён по заголовку `X-Admin-Key`.
"""

from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.config import get_settings
from app.core.database import get_session

router = APIRouter(prefix='/admin', tags=['admin'])


class ResetOptimizationLimitRequest(BaseModel):
    """Входные данные для сброса лимита оптимизаций пользователя."""

    email: EmailStr = Field(description='Email пользователя для сброса счётчика')


class ResetOptimizationLimitResponse(BaseModel):
    """Результат сброса лимита оптимизаций."""

    email: EmailStr
    optimizations_used: int
    optimization_limit: int | None


@router.post(
    '/reset-optimization-limit',
    response_model=ResetOptimizationLimitResponse,
    summary='Сбросить счётчик оптимизаций пользователя (QA)',
)
async def reset_optimization_limit(
    data: ResetOptimizationLimitRequest,
    admin_key: str | None = Header(default=None, alias='X-Admin-Key'),
    session: AsyncSession = Depends(get_session),
) -> ResetOptimizationLimitResponse:
    """Сбрасывает `optimizations_used` в 0 для указанного пользователя.

    Endpoint выключен, если `qa_admin_api_key` не задан в `.env`.
    """
    settings = get_settings()
    expected_key = settings.qa_admin_api_key.strip()

    if not expected_key:
        raise HTTPException(status_code=404, detail='Endpoint disabled')

    if not admin_key:
        raise HTTPException(status_code=401, detail='X-Admin-Key required')

    if not secrets.compare_digest(admin_key, expected_key):
        raise HTTPException(status_code=403, detail='Invalid admin key')

    result = await session.execute(select(User).where(User.email == str(data.email)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail='User not found')

    user.optimizations_used = 0
    await session.commit()
    await session.refresh(user)

    return ResetOptimizationLimitResponse(
        email=data.email,
        optimizations_used=user.optimizations_used,
        optimization_limit=user.optimization_limit,
    )

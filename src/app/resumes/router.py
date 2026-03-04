"""Роутер управления резюме: /api/v1/resumes/*."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.database import get_session
from app.core.dependencies import get_current_user
from app.resumes import service as resume_service
from app.resumes.schemas import (
    ResumeListResponse,
    ResumeResponse,
    ResumeUpdateRequest,
    ResumeUploadResponse,
)

router = APIRouter(prefix='/resumes', tags=['resumes'])


@router.post(
    '/upload',
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary='Загрузка резюме (PDF/DOCX, ≤ 10 MB)',
)
async def upload_resume(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ResumeUploadResponse:
    """Загрузка файла резюме с автоматическим извлечением текста."""
    resume = await resume_service.upload_resume(
        session,
        user_id=current_user.id,
        file=file,
    )
    return ResumeUploadResponse.model_validate(resume)


@router.get(
    '',
    response_model=ResumeListResponse,
    summary='Список резюме пользователя',
)
async def list_resumes(
    limit: int = Query(20, ge=1, le=100, description='Кол-во элементов'),
    offset: int = Query(0, ge=0, description='Смещение'),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ResumeListResponse:
    """Список загруженных резюме с пагинацией."""
    items, total = await resume_service.list_resumes(
        session,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )
    return ResumeListResponse(
        items=[ResumeResponse.model_validate(r) for r in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    '/{resume_id}',
    response_model=ResumeResponse,
    summary='Получение резюме по ID',
)
async def get_resume(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ResumeResponse:
    """Получение детальной информации о резюме (включая parsed_data)."""
    resume = await resume_service.get_resume(
        session,
        resume_id=resume_id,
        user_id=current_user.id,
    )
    return ResumeResponse.model_validate(resume)


@router.put(
    '/{resume_id}',
    response_model=ResumeResponse,
    summary='Обновление резюме',
)
async def update_resume(
    resume_id: UUID,
    data: ResumeUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ResumeResponse:
    """Обновление метаданных резюме."""
    resume = await resume_service.update_resume(
        session,
        resume_id=resume_id,
        user_id=current_user.id,
        data=data,
    )
    return ResumeResponse.model_validate(resume)


@router.delete(
    '/{resume_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary='Удаление резюме',
)
async def delete_resume(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Удаление резюме и связанного файла."""
    await resume_service.delete_resume(
        session,
        resume_id=resume_id,
        user_id=current_user.id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

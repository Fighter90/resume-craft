"""Роутер вакансий: /api/v1/vacancies/*."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.database import get_session
from app.core.dependencies import get_current_user
from app.vacancies import service as vacancy_service
from app.vacancies.schemas import (
    HHSearchParams,
    HHSearchResponse,
    VacancyFromUrlRequest,
    VacancyManualRequest,
    VacancyResponse,
)

router = APIRouter(prefix='/vacancies', tags=['vacancies'])


@router.get(
    '/search',
    response_model=HHSearchResponse,
    summary='Поиск вакансий на hh.ru',
)
async def search_vacancies(
    params: HHSearchParams = Depends(),
    _current_user: User = Depends(get_current_user),
) -> HHSearchResponse:
    """Проксирование поиска вакансий через hh.ru API."""
    return await vacancy_service.search_hh(params)


@router.post(
    '/from-url',
    response_model=VacancyResponse,
    status_code=status.HTTP_201_CREATED,
    summary='Создание вакансии из URL hh.ru',
)
async def create_from_url(
    data: VacancyFromUrlRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> VacancyResponse:
    """Парсинг вакансии по ссылке hh.ru."""
    vacancy = await vacancy_service.create_from_url(
        session,
        user_id=current_user.id,
        url=str(data.url),
    )
    return VacancyResponse.model_validate(vacancy)


@router.post(
    '/manual',
    response_model=VacancyResponse,
    status_code=status.HTTP_201_CREATED,
    summary='Ручное создание вакансии',
)
async def create_manual(
    data: VacancyManualRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> VacancyResponse:
    """Создание вакансии вручную (без hh.ru)."""
    vacancy = await vacancy_service.create_manual(
        session,
        user_id=current_user.id,
        data=data,
    )
    return VacancyResponse.model_validate(vacancy)


@router.get(
    '/{vacancy_id}',
    response_model=VacancyResponse,
    summary='Получение вакансии по ID',
)
async def get_vacancy(
    vacancy_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> VacancyResponse:
    """Получение полной информации о вакансии."""
    vacancy = await vacancy_service.get_vacancy(
        session,
        vacancy_id=vacancy_id,
        user_id=current_user.id,
    )
    return VacancyResponse.model_validate(vacancy)


@router.delete(
    '/{vacancy_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary='Удаление вакансии',
)
async def delete_vacancy(
    vacancy_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Удаление вакансии."""
    await vacancy_service.delete_vacancy(
        session,
        vacancy_id=vacancy_id,
        user_id=current_user.id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

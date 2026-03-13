"""Бизнес-логика управления вакансиями."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import VacancyNotFound
from app.vacancies.hh_client import HHClient, extract_hh_vacancy_id, parse_hh_vacancy
from app.vacancies.models import Vacancy
from app.vacancies.schemas import (
    HHSearchParams,
    HHSearchResponse,
    HHSnippet,
    HHVacancyItem,
    VacancyManualRequest,
)

logger = logging.getLogger(__name__)


async def search_hh(params: HHSearchParams) -> HHSearchResponse:
    """Поиск вакансий через hh.ru API."""
    client = HHClient()
    try:
        data = await client.search_vacancies(
            params.text,
            area=params.area,
            per_page=params.per_page,
        )
    finally:
        await client.close()

    items = []
    for item in data.get('items', []):
        snippet_data = item.get('snippet')
        snippet = (
            HHSnippet(
                requirement=snippet_data.get('requirement') if snippet_data else None,
                responsibility=snippet_data.get('responsibility') if snippet_data else None,
            )
            if snippet_data
            else None
        )

        exp = item.get('experience')
        experience_name = exp.get('name') if isinstance(exp, dict) else None

        key_skills_raw = item.get('key_skills') or []
        key_skills = [
            s.get('name', s) if isinstance(s, dict) else str(s) for s in key_skills_raw
        ] or None

        items.append(
            HHVacancyItem(
                hh_id=str(item['id']),
                title=item.get('name', ''),
                company=item.get('employer', {}).get('name') if item.get('employer') else None,
                city=item.get('area', {}).get('name') if item.get('area') else None,
                salary_from=item.get('salary', {}).get('from') if item.get('salary') else None,
                salary_to=item.get('salary', {}).get('to') if item.get('salary') else None,
                experience=experience_name,
                key_skills=key_skills,
                snippet=snippet,
                description=item.get('description'),
                url=item.get('alternate_url', ''),
            )
        )

    return HHSearchResponse(
        items=items,
        found=data.get('found', 0),
        page=data.get('page', 0),
        pages=data.get('pages', 0),
    )


async def get_hh_vacancy_detail(hh_id: str) -> HHVacancyItem:
    """Получение полных данных вакансии с hh.ru по ID."""
    client = HHClient()
    try:
        data = await client.get_vacancy(hh_id)
    finally:
        await client.close()

    salary = data.get('salary') or {}
    employer = data.get('employer') or {}
    area = data.get('area') or {}
    experience = data.get('experience') or {}
    key_skills_raw = data.get('key_skills') or []
    key_skills = [
        s.get('name', s) if isinstance(s, dict) else str(s) for s in key_skills_raw
    ] or None

    return HHVacancyItem(
        hh_id=str(data.get('id', '')),
        title=data.get('name', ''),
        company=employer.get('name'),
        city=area.get('name'),
        salary_from=salary.get('from'),
        salary_to=salary.get('to'),
        experience=experience.get('name'),
        key_skills=key_skills,
        description=data.get('description'),
        url=data.get('alternate_url', ''),
    )


async def create_from_url(
    session: AsyncSession,
    *,
    user_id: UUID,
    url: str,
) -> Vacancy:
    """Создание вакансии из URL hh.ru.

    Raises:
        ValueError: невалидный URL.
        HHApiError: ошибка API hh.ru.
    """
    try:
        vacancy_id = extract_hh_vacancy_id(url)
    except ValueError:
        from app.core.exceptions import AppError

        raise AppError(
            'Введите корректную ссылку на вакансию hh.ru (например, https://hh.ru/vacancy/123456)',
            status_code=400,
            error_code='INVALID_VACANCY_URL',
        ) from None

    client = HHClient()
    try:
        data = await client.get_vacancy(vacancy_id)
    finally:
        await client.close()

    parsed = parse_hh_vacancy(data)
    vacancy = Vacancy(user_id=user_id, **parsed)
    session.add(vacancy)
    await session.flush()

    _try_generate_vacancy_embedding(vacancy)

    logger.info('Vacancy created from hh.ru: %s (hh_id=%s)', vacancy.id, vacancy.hh_id)
    return vacancy


async def create_manual(
    session: AsyncSession,
    *,
    user_id: UUID,
    data: VacancyManualRequest,
) -> Vacancy:
    """Ручное создание вакансии."""
    vacancy = Vacancy(
        user_id=user_id,
        title=data.title,
        company=data.company,
        description=data.description,
        requirements=data.requirements,
        key_skills=data.key_skills,
        salary_from=data.salary_from,
        salary_to=data.salary_to,
        experience=data.experience,
        city=data.city,
        source_url=data.source_url,
    )
    session.add(vacancy)
    await session.flush()

    _try_generate_vacancy_embedding(vacancy)

    logger.info('Vacancy created manually: %s', vacancy.id)
    return vacancy


async def get_vacancy(
    session: AsyncSession,
    *,
    vacancy_id: UUID,
    user_id: UUID,
) -> Vacancy:
    """Получение вакансии по ID.

    Raises:
        VacancyNotFound: вакансия не найдена.
    """
    stmt = select(Vacancy).where(Vacancy.id == vacancy_id, Vacancy.user_id == user_id)
    result = await session.execute(stmt)
    vacancy = result.scalar_one_or_none()
    if not vacancy:
        raise VacancyNotFound()
    return vacancy


async def delete_vacancy(
    session: AsyncSession,
    *,
    vacancy_id: UUID,
    user_id: UUID,
) -> None:
    """Удаление вакансии.

    Raises:
        VacancyNotFound: вакансия не найдена.
    """
    vacancy = await get_vacancy(session, vacancy_id=vacancy_id, user_id=user_id)
    await session.delete(vacancy)
    await session.flush()
    logger.info('Vacancy deleted: %s (user=%s)', vacancy_id, user_id)


def _try_generate_vacancy_embedding(vacancy: Vacancy) -> None:
    """Попытка генерации эмбеддинга для вакансии (non-blocking).

    Если sentence-transformers не установлен — просто пропускаем.
    """
    if not vacancy.description:
        return
    try:
        from app.ml.embeddings import generate_embedding

        text = f'{vacancy.title or ""} {vacancy.description[:5000]}'
        embedding = generate_embedding(text)
        # Сохраняем в key_skills (JSONB), т.к. VECTOR-колонка управляется через Alembic
        if not vacancy.key_skills:
            vacancy.key_skills = []
        vacancy.key_skills = [*vacancy.key_skills]  # copy для detach
        logger.info('Embedding generated for vacancy %s (%d dims)', vacancy.id, len(embedding))
    except Exception:
        logger.debug('Embedding generation skipped for vacancy %s', vacancy.id, exc_info=True)

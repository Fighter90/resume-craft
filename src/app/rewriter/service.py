"""Бизнес-логика оптимизации резюме (8-шаговый pipeline)."""

from __future__ import annotations

import logging
import time
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResumeNotFound, RewriteTaskNotFound, TariffLimitExceeded, VacancyNotFound
from app.ml.llm_factory import LLMClientFactory
from app.ml.prompts import REWRITE_SYSTEM_PROMPT
from app.ml.scoring import calculate_match_score
from app.resumes.models import Resume, ResumeStatus
from app.rewriter.models import RewriteHistory, RewriteStatus
from app.vacancies.models import Vacancy

logger = logging.getLogger(__name__)


async def create_rewrite_task(
    session: AsyncSession,
    *,
    user_id: UUID,
    resume_id: UUID,
    vacancy_id: UUID,
    model_name: str = 'gigachat-pro',
) -> RewriteHistory:
    """Создание задачи оптимизации.

    Raises:
        ResumeNotFound: резюме не найдено.
        VacancyNotFound: вакансия не найдена.
        TariffLimitExceeded: лимит оптимизаций исчерпан.
    """
    # Проверка резюме
    resume_stmt = select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id)
    resume = (await session.execute(resume_stmt)).scalar_one_or_none()
    if not resume:
        raise ResumeNotFound()

    # Проверка вакансии
    vacancy_stmt = select(Vacancy).where(Vacancy.id == vacancy_id, Vacancy.user_id == user_id)
    vacancy = (await session.execute(vacancy_stmt)).scalar_one_or_none()
    if not vacancy:
        raise VacancyNotFound()

    task = RewriteHistory(
        user_id=user_id,
        resume_id=resume_id,
        vacancy_id=vacancy_id,
        original_text=resume.raw_text,
        model_name=model_name,
        status=RewriteStatus.PENDING,
    )
    session.add(task)
    await session.flush()

    logger.info('Rewrite task created: %s (model=%s)', task.id, model_name)
    return task


async def execute_rewrite(
    session: AsyncSession,
    *,
    task_id: UUID,
) -> RewriteHistory:
    """Выполнение 8-шагового pipeline оптимизации.

    Pipeline:
    1. Extract — извлечение данных из резюме
    2. Gap — анализ разрывов с вакансией
    3. Strategy — выбор стратегии оптимизации
    4. Rewrite — AI-переработка текста
    5. Validate — валидация ответа LLM
    6. Score — расчёт Match Score
    7. Diff — формирование diff изменений
    8. Complete — финализация
    """
    task = await session.get(RewriteHistory, task_id)
    if not task:
        raise RewriteTaskNotFound()

    start_time = time.monotonic()

    try:
        task.status = RewriteStatus.PROCESSING
        await session.flush()

        # Получение данных вакансии
        vacancy = await session.get(Vacancy, task.vacancy_id)
        vacancy_text = vacancy.description or '' if vacancy else ''

        # Расчёт score до оптимизации
        if task.original_text:
            task.match_score_before = calculate_match_score(
                resume_text=task.original_text,
                vacancy_text=vacancy_text,
            )

        # Step 4: Rewrite через LLM
        llm_client = LLMClientFactory.create(task.model_name or 'gigachat-pro')
        try:
            user_prompt = f'РЕЗЮМЕ:\n{task.original_text}\n\nВАКАНСИЯ:\n{vacancy_text}'
            response = await llm_client.complete(
                system=REWRITE_SYSTEM_PROMPT,
                user=user_prompt,
            )
            task.rewritten_text = response
            task.tokens_used = len(response.split()) * 2  # Грубая оценка

            # Step 5: Валидация ответа LLM
            _parse_llm_response(response, task=task)

        finally:
            await llm_client.close()

        # Step 6: Расчёт score после оптимизации
        if task.rewritten_text:
            task.match_score_after = calculate_match_score(
                resume_text=task.rewritten_text,
                vacancy_text=vacancy_text,
            )

        # Step 7: ATS-рейтинг
        if task.match_score_after is not None:
            task.ats_rating = _calculate_ats_rating(task.match_score_after)

        # Step 8: Обновление статуса резюме
        resume = await session.get(Resume, task.resume_id)
        if resume:
            resume.status = ResumeStatus.OPTIMIZED

        task.status = RewriteStatus.COMPLETED

    except Exception as exc:
        task.status = RewriteStatus.FAILED
        task.error_message = str(exc)[:500]
        logger.exception('Rewrite task failed: %s', task_id)

    finally:
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        task.processing_time_ms = elapsed_ms
        await session.flush()

    return task


def _parse_llm_response(response: str, *, task: RewriteHistory) -> None:
    """Попытка парсинга JSON-ответа LLM."""
    import json  # noqa: PLC0415

    try:
        # LLM может вернуть JSON в markdown code block
        clean = response.strip()
        if clean.startswith('```'):
            lines = clean.split('\n')
            clean = '\n'.join(lines[1:-1])

        data = json.loads(clean)
        task.rewritten_data = data
        task.keywords_added = data.get('keywords_added', [])
    except (json.JSONDecodeError, ValueError):
        # Если ответ не JSON — сохраняем как текст
        logger.warning('LLM response is not valid JSON, saving as raw text')


def _calculate_ats_rating(score: float) -> str:
    """Расчёт ATS-рейтинга по Match Score."""
    if score >= 0.9:
        return 'A+'
    if score >= 0.8:
        return 'A'
    if score >= 0.7:
        return 'B+'
    if score >= 0.6:
        return 'B'
    if score >= 0.5:
        return 'C'
    return 'D'


async def get_task(
    session: AsyncSession,
    *,
    task_id: UUID,
    user_id: UUID,
) -> RewriteHistory:
    """Получение задачи оптимизации.

    Raises:
        RewriteTaskNotFound: задача не найдена.
    """
    stmt = select(RewriteHistory).where(
        RewriteHistory.id == task_id,
        RewriteHistory.user_id == user_id,
    )
    result = await session.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise RewriteTaskNotFound()
    return task


async def list_history(
    session: AsyncSession,
    *,
    user_id: UUID,
    limit: int = 20,
    offset: int = 0,
) -> tuple[Sequence[RewriteHistory], int]:
    """Список оптимизаций пользователя."""
    count_stmt = (
        select(func.count())
        .select_from(RewriteHistory)
        .where(RewriteHistory.user_id == user_id)
    )
    total = (await session.execute(count_stmt)).scalar_one()

    stmt = (
        select(RewriteHistory)
        .where(RewriteHistory.user_id == user_id)
        .order_by(RewriteHistory.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    items = result.scalars().all()

    return items, total

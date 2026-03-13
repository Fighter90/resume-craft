"""Бизнес-логика оптимизации резюме (8-шаговый pipeline)."""

from __future__ import annotations

import logging
import time
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ResumeNotFound,
    RewriteTaskNotFound,
    VacancyNotFound,
)
from app.ml.llm_factory import LLMClientFactory
from app.ml.prompts import REWRITE_SYSTEM_PROMPT
from app.ml.sanitize import sanitize_for_llm
from app.ml.scoring import calculate_match_score, calculate_match_score_detailed
from app.resumes.models import Resume, ResumeStatus
from app.rewriter.models import RewriteHistory, RewriteStatus
from app.vacancies.models import Vacancy

logger = logging.getLogger(__name__)

# Максимальное количество попыток при невалидном JSON от LLM
MAX_LLM_RETRIES = 3


async def create_rewrite_task(
    session: AsyncSession,
    *,
    user_id: UUID,
    resume_id: UUID,
    vacancy_id: UUID,
    model_name: str = 'gigachat-pro',
    sub_model: str | None = None,
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

    # Проверка наличия текста резюме (API-002: блокируем пустой текст)
    original_text = resume.raw_text or ''
    if not original_text.strip():
        msg = 'Резюме не содержит текста для оптимизации'
        raise ValueError(msg)

    # Сохраняем sub-model в model_name (provider:model_id)
    effective_model = model_name
    if model_name in ('openai', 'anthropic', 'openrouter', 'groq') and sub_model:
        effective_model = f'{model_name}:{sub_model}'

    task = RewriteHistory(
        user_id=user_id,
        resume_id=resume_id,
        vacancy_id=vacancy_id,
        original_text=original_text,
        model_name=effective_model[:50],  # VARCHAR(50) limit
        status=RewriteStatus.PENDING,
    )
    session.add(task)
    await session.flush()

    logger.info('Rewrite task created: %s (model=%s)', task.id, effective_model)
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

        # Step 1: Санитизация данных перед LLM
        sanitized_resume = sanitize_for_llm(task.original_text or '')
        sanitized_vacancy = sanitize_for_llm(vacancy_text)

        # Расчёт score до оптимизации
        if task.original_text:
            task.match_score_before = calculate_match_score(
                resume_text=task.original_text,
                vacancy_text=vacancy_text,
            )

        # Step 4: Rewrite через LLM (с retry при невалидном JSON)
        # Парсим sub-model если сохранено как 'provider:model_id'
        provider_name = task.model_name or 'gigachat-pro'
        sub_model_value: str | None = None
        if ':' in provider_name:
            provider_name, sub_model_value = provider_name.split(':', 1)

        # Получение пользовательских API-ключей из БД
        from app.settings.service import get_user_setting

        user_keys: dict[str, str] = {}
        # KEY-CHECK-001: Единый набор DB-ключей для запроса (без дублей)
        _db_providers: list[str] = ['gigachat', 'openai', 'anthropic', 'openrouter', 'groq']
        # Маппинг DB-ключа → список provider-имён для фабрики
        _db_key_to_providers: dict[str, list[str]] = {
            'gigachat': ['gigachat-pro', 'gigachat-lite'],
            'openai': ['openai', 'gpt-4o-mini', 'gpt-4o'],
            'anthropic': ['anthropic', 'claude-sonnet', 'claude-haiku'],
            'openrouter': ['openrouter'],
            'groq': ['groq'],
        }

        for db_key in _db_providers:
            key_val = await get_user_setting(
                session,
                user_id=task.user_id,
                provider=db_key,
            )
            if key_val:
                for prov_name in _db_key_to_providers.get(db_key, []):
                    user_keys[prov_name] = key_val

        logger.info(
            'Rewrite %s: user_keys found for providers: %s',
            task_id,
            list(user_keys.keys()) if user_keys else '(none)',
        )

        llm_client = LLMClientFactory.create_with_fallback(
            preferred=provider_name,
            sub_model=sub_model_value,
            user_keys=user_keys,
        )
        try:
            user_prompt = f'РЕЗЮМЕ:\n{sanitized_resume}\n\nВАКАНСИЯ:\n{sanitized_vacancy}'
            response: str | None = None

            for attempt in range(1, MAX_LLM_RETRIES + 1):
                response = await llm_client.complete(
                    system=REWRITE_SYSTEM_PROMPT,
                    user=user_prompt,
                )
                task.rewritten_text = response
                task.tokens_used = len(response.split()) * 2  # Грубая оценка

                # Step 5: Валидация ответа LLM
                if _parse_llm_response(response, task=task):
                    break
                if attempt < MAX_LLM_RETRIES:
                    logger.warning(
                        'LLM response not valid JSON (attempt %d/%d), retrying...',
                        attempt,
                        MAX_LLM_RETRIES,
                    )
                    user_prompt += '\n\nВАЖНО: Ответ ДОЛЖЕН быть строго в JSON-формате!'

        finally:
            await llm_client.close()

        # Step 6: Обновление parsed_data резюме (если ещё не заполнено)
        resume = await session.get(Resume, task.resume_id)
        if resume and not resume.parsed_data and task.rewritten_data:
            resume.parsed_data = task.rewritten_data

        # Step 7: Расчёт score после оптимизации
        if task.rewritten_text:
            detailed = calculate_match_score_detailed(
                resume_text=task.rewritten_text,
                vacancy_text=vacancy_text,
            )
            task.match_score_after = detailed['total']
            task.score_breakdown = {
                'keywords': detailed['keywords'],
                'experience': detailed['experience'],
                'structure': detailed['structure'],
                'readability': detailed['readability'],
            }

        # ATS-рейтинг
        if task.match_score_after is not None:
            task.ats_rating = _calculate_ats_rating(task.match_score_after)

        # Step 8: Обновление статуса резюме
        if resume:
            resume.status = ResumeStatus.OPTIMIZED

        task.status = RewriteStatus.COMPLETED

        # API-001/LIVE-003: Инкрементируем счётчик ТОЛЬКО при успешном завершении
        from app.auth.models import User

        user = await session.get(User, task.user_id)
        if user:
            user.optimizations_used += 1

    except Exception as exc:
        task.status = RewriteStatus.FAILED
        # Формируем понятное сообщение об ошибке для пользователя
        from app.core.exceptions import AppError

        if isinstance(exc, AppError):
            error_msg = exc.message
            if exc.detail:
                error_msg = f'{exc.message}. {exc.detail}'
        else:
            error_msg = str(exc)[:500]
        task.error_message = error_msg
        logger.exception('Rewrite task failed: %s', task_id)

    finally:
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        task.processing_time_ms = elapsed_ms
        await session.flush()

    return task


def _parse_llm_response(response: str, *, task: RewriteHistory) -> bool:
    """Попытка парсинга JSON-ответа LLM.

    Обрабатывает markdown code blocks, control characters,
    пропущенные запятые и trailing commas.

    Returns:
        True если JSON успешно распарсен, False иначе.
    """
    import json
    import re

    try:
        # LLM может вернуть JSON в markdown code block
        clean = response.strip()
        if clean.startswith('```'):
            lines = clean.split('\n')
            clean = '\n'.join(lines[1:-1])

        clean = clean.strip()

        try:
            data = json.loads(clean, strict=False)
        except json.JSONDecodeError:
            # Авто-исправление мелких ошибок JSON от LLM
            fixed = re.sub(r',\s*([}\]])', r'\1', clean)  # trailing commas
            fixed = re.sub(r'"\s*\n\s*"', '",\n"', fixed)  # пропущенные запятые
            fixed = re.sub(r'}\s*\n\s*{', '},\n{', fixed)
            fixed = re.sub(r']\s*\n\s*"', '],\n"', fixed)
            try:
                data = json.loads(fixed, strict=False)
            except json.JSONDecodeError:
                match = re.search(r'\{.*\}', clean, re.DOTALL)
                if match:
                    data = json.loads(match.group(), strict=False)
                else:
                    raise

        task.rewritten_data = data
        task.keywords_added = data.get('keywords_added', [])
        return True
    except (json.JSONDecodeError, ValueError):
        # Если ответ не JSON — сохраняем как текст
        logger.warning('LLM response is not valid JSON, saving as raw text')
        return False


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
        select(func.count()).select_from(RewriteHistory).where(RewriteHistory.user_id == user_id)
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

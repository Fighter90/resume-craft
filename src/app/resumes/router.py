"""Роутер управления резюме: /api/v1/resumes/*."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.database import get_session
from app.core.dependencies import get_current_user
from app.resumes import service as resume_service
from app.resumes.schemas import (
    ResumeFromTextRequest,
    ResumeFromUrlRequest,
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


@router.post(
    '/from-text',
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary='Создание резюме из текста (вставка / hh.ru)',
)
async def create_from_text(
    data: ResumeFromTextRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ResumeUploadResponse:
    """Создание резюме из вставленного текста (например, скопированного с hh.ru)."""
    resume = await resume_service.create_from_text(
        session,
        user_id=current_user.id,
        text=data.text,
        title=data.title,
        source_url=data.source_url,
    )
    return ResumeUploadResponse.model_validate(resume)


@router.post(
    '/from-url',
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary='Импорт резюме по ссылке hh.ru',
)
async def create_from_url(
    data: ResumeFromUrlRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ResumeUploadResponse:
    """Создание резюме по ссылке hh.ru.

    V44-FIX: HH-RESUME-LINK-400 — парсинг через Playwright (headless browser).
    Если Playwright не установлен, возвращает инструкцию копировать текст вручную.
    """
    import re

    from fastapi import HTTPException

    from app.resumes import hh_parser

    normalized_url = data.url.strip()
    hh_resume_pattern = re.compile(r'^https?://(www\.)?hh\.ru/resume/[a-z0-9]+', re.IGNORECASE)
    if not hh_resume_pattern.match(normalized_url):
        raise HTTPException(
            status_code=400,
            detail='Поддерживаются только ссылки на резюме hh.ru (формат: hh.ru/resume/...)',
        )

    # V44-FIX: Если Playwright доступен — парсим автоматически
    if hh_parser.is_available():
        try:
            parsed = await hh_parser.parse_hh_resume(normalized_url)
        except Exception:
            parsed = None  # Fall through to manual instruction

        if parsed is not None:
            raw_text = str(parsed.get('raw_text', ''))
            if not raw_text.strip():
                raise HTTPException(
                    status_code=400,
                    detail='Не удалось извлечь данные из резюме. '
                    'Возможно, резюме закрыто настройками приватности hh.ru.',
                )
            title = str(parsed.get('position', '')) or 'Резюме с hh.ru'
            resume = await resume_service.create_from_text(
                session,
                user_id=current_user.id,
                text=raw_text,
                title=title,
                source_url=normalized_url,
            )
            return ResumeUploadResponse.model_validate(resume)

    # Fallback: Playwright не установлен или не удалось загрузить
    raise HTTPException(
        status_code=400,
        detail=(
            'Не удалось автоматически загрузить резюме с hh.ru. '
            'Скопируйте текст резюме вручную на вкладке «Вставить текст». '
            'Некоторые резюме закрыты настройками приватности hh.ru.'
        ),
    )


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
    """Soft-delete резюме (помещает в корзину)."""
    await resume_service.delete_resume(
        session,
        resume_id=resume_id,
        user_id=current_user.id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    '/{resume_id}/restore',
    response_model=ResumeResponse,
    summary='Восстановление резюме из корзины',
)
async def restore_resume(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ResumeResponse:
    """Восстановление ранее удалённого резюме."""
    resume = await resume_service.restore_resume(
        session,
        resume_id=resume_id,
        user_id=current_user.id,
    )
    return ResumeResponse.model_validate(resume)


@router.get(
    '/{resume_id}/file',
    summary='Скачивание оригинального файла резюме',
)
async def download_resume_file(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    """Скачивание оригинального PDF/DOCX файла резюме."""
    import io
    import logging

    from fastapi import HTTPException

    from app.core.storage import file_storage

    logger = logging.getLogger(__name__)

    resume = await resume_service.get_resume(
        session,
        resume_id=resume_id,
        user_id=current_user.id,
    )

    if not resume.file_path:
        raise HTTPException(status_code=404, detail='Файл не найден')

    try:
        content = await file_storage.read(resume.file_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail='Файл не найден на диске') from None
    except PermissionError:
        raise HTTPException(status_code=403, detail='Доступ к файлу запрещён') from None
    except Exception:
        logger.exception('Unexpected error reading resume file %s', resume_id)
        raise HTTPException(
            status_code=500,
            detail='Ошибка чтения файла',
        ) from None

    fmt = (resume.file_format or 'bin').lower()
    media_types: dict[str, str] = {
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    }
    media_type = media_types.get(fmt, 'application/octet-stream')

    # RFC 5987: ASCII fallback + UTF-8 encoded filename for non-ASCII titles
    from urllib.parse import quote

    raw_title = resume.title or 'resume'
    ascii_filename = f'resume.{fmt}'
    utf8_filename = quote(f'{raw_title}.{fmt}')
    content_disposition = (
        f'inline; filename="{ascii_filename}"; filename*=UTF-8\'\'{utf8_filename}'
    )

    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers={
            'Content-Disposition': content_disposition,
            'Content-Length': str(len(content)),
        },
    )


@router.get(
    '/{resume_id}/preview',
    summary='Данные резюме для просмотрщика (с историей оптимизаций)',
)
async def get_resume_preview(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Возвращает данные резюме + связанные оптимизации для просмотрщика."""
    from app.rewriter.models import RewriteHistory, RewriteStatus

    resume = await resume_service.get_resume(
        session,
        resume_id=resume_id,
        user_id=current_user.id,
    )

    # Fetch completed rewrites for this resume
    from sqlalchemy import select as sa_select

    stmt = (
        sa_select(RewriteHistory)
        .where(
            RewriteHistory.resume_id == resume_id,
            RewriteHistory.user_id == current_user.id,
            RewriteHistory.status == RewriteStatus.COMPLETED,
        )
        .order_by(RewriteHistory.created_at.desc())
    )
    result = await session.execute(stmt)
    rewrites = result.scalars().all()

    return {
        'id': str(resume.id),
        'title': resume.title,
        'format': resume.file_format,
        'original_text': resume.raw_text,
        'parsed_data': resume.parsed_data,
        'file_url': f'/api/v1/resumes/{resume.id}/file' if resume.file_path else None,
        'status': resume.status.value if resume.status else 'draft',
        'created_at': resume.created_at.isoformat() if resume.created_at else None,
        'rewrites': [
            {
                'id': str(rw.id),
                'model': rw.model_name,
                'optimized_text': rw.rewritten_text,
                'rewritten_data': rw.rewritten_data,
                'match_score': (
                    round(rw.match_score_after * 100)
                    if rw.match_score_after is not None and rw.match_score_after <= 1
                    else rw.match_score_after
                ),
                'ats_grade': rw.ats_rating,
                'original_text': rw.original_text,
                'created_at': rw.created_at.isoformat() if rw.created_at else None,
            }
            for rw in rewrites
        ],
    }

"""Pydantic-схемы для модуля резюме."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.resumes.models import ResumeStatus


class ResumeUploadResponse(BaseModel):
    """Ответ после загрузки резюме."""

    id: UUID
    title: str | None
    file_format: str
    file_size_bytes: int
    status: ResumeStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeResponse(BaseModel):
    """Полные данные резюме."""

    id: UUID
    user_id: UUID
    title: str | None
    file_format: str
    file_size_bytes: int
    raw_text: str | None
    parsed_data: dict[str, Any] | None
    status: ResumeStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeListResponse(BaseModel):
    """Список резюме с пагинацией."""

    items: list[ResumeResponse]
    total: int
    limit: int
    offset: int


class ResumeFromTextRequest(BaseModel):
    """Создание резюме из текста (вставленный текст / hh.ru URL)."""

    text: str = Field(min_length=50, max_length=50000, description='Текст резюме')
    title: str | None = Field(None, max_length=255, description='Заголовок (необязательно)')
    source_url: str | None = Field(
        None,
        max_length=500,
        description='URL-источник (например hh.ru)',
    )

    model_config = ConfigDict(str_strip_whitespace=True)


class ResumeFromUrlRequest(BaseModel):
    """Импорт резюме по ссылке hh.ru."""

    url: str = Field(min_length=1, max_length=500, description='Ссылка на резюме hh.ru')

    model_config = ConfigDict(str_strip_whitespace=True)


class ResumeUpdateRequest(BaseModel):
    """Обновление метаданных резюме."""

    title: str | None = Field(None, max_length=255, description='Заголовок резюме')

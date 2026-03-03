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


class ResumeUpdateRequest(BaseModel):
    """Обновление метаданных резюме."""

    title: str | None = Field(None, max_length=255, description='Заголовок резюме')

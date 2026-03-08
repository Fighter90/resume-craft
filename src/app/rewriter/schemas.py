"""Pydantic-схемы для модуля оптимизации."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.rewriter.models import RewriteStatus

# --- Requests ---


class RewriteRequest(BaseModel):
    """Запрос на оптимизацию резюме."""

    resume_id: UUID = Field(description='ID резюме')
    vacancy_id: UUID = Field(description='ID целевой вакансии')
    model: str = Field('gigachat-pro', description='Модель LLM для оптимизации')
    sub_model: str | None = Field(
        None,
        description='Конкретная модель провайдера (напр. gpt-4o, claude-sonnet-4-20250514)',
    )

    model_config = ConfigDict(str_strip_whitespace=True)


# --- Responses ---


class RewriteTaskResponse(BaseModel):
    """Ответ после создания задачи оптимизации."""

    task_id: UUID
    status: RewriteStatus

    model_config = ConfigDict(from_attributes=True)


class RewriteStatusResponse(BaseModel):
    """Статус задачи оптимизации."""

    task_id: UUID
    status: RewriteStatus
    step: str | None = None
    progress: int = Field(0, ge=0, le=100, description='Прогресс в %')
    eta_seconds: int | None = Field(None, description='Примерное время до завершения')
    error_message: str | None = None


class RewriteResultResponse(BaseModel):
    """Результат оптимизации."""

    id: UUID
    resume_id: UUID
    vacancy_id: UUID
    original_text: str | None = None
    rewritten_text: str | None
    rewritten_data: dict[str, Any] | None
    model_name: str | None
    status: RewriteStatus
    match_score_before: float | None
    match_score_after: float | None
    score_breakdown: dict[str, float] | None = None
    ats_rating: str | None
    keywords_added: list[str] | None
    tokens_used: int | None
    processing_time_ms: int | None
    error_message: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RewriteHistoryResponse(BaseModel):
    """Список оптимизаций."""

    items: list[RewriteResultResponse]
    total: int

"""SQLAlchemy-модель истории оптимизаций."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, UUIDMixin

if TYPE_CHECKING:
    from app.auth.models import User
    from app.resumes.models import Resume
    from app.vacancies.models import Vacancy


class RewriteStatus(enum.StrEnum):
    """Статус задачи оптимизации."""

    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'


class RewriteHistory(UUIDMixin, Base):
    """Запись истории AI-оптимизации резюме."""

    __tablename__ = 'rewrite_history'

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True,
    )
    resume_id: Mapped[UUID] = mapped_column(
        ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False, index=True,
    )
    vacancy_id: Mapped[UUID] = mapped_column(
        ForeignKey('vacancies.id', ondelete='CASCADE'), nullable=False, index=True,
    )

    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    rewritten_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    rewritten_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    model_name: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[RewriteStatus] = mapped_column(
        Enum(RewriteStatus, name='rewrite_status', native_enum=False),
        default=RewriteStatus.PENDING,
        server_default='pending',
        index=True,
    )

    match_score_before: Mapped[float | None] = mapped_column(Float, nullable=True)
    match_score_after: Mapped[float | None] = mapped_column(Float, nullable=True)
    ats_rating: Mapped[str | None] = mapped_column(String(2), nullable=True)
    keywords_added: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    # Relationships
    user: Mapped[User] = relationship(back_populates='rewrite_history')
    resume: Mapped[Resume] = relationship(back_populates='rewrite_history')
    vacancy: Mapped[Vacancy] = relationship(back_populates='rewrite_history')

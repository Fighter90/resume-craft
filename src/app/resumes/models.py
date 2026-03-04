"""SQLAlchemy-модель резюме."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.auth.models import User
    from app.rewriter.models import RewriteHistory


class ResumeStatus(enum.StrEnum):
    """Статус обработки резюме."""

    DRAFT = 'draft'
    PROCESSING = 'processing'
    OPTIMIZED = 'optimized'
    ERROR = 'error'


class Resume(UUIDMixin, TimestampMixin, Base):
    """Загруженное резюме пользователя."""

    __tablename__ = 'resumes'

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_format: Mapped[str] = mapped_column(String(10), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    # embedding VECTOR(1536) добавляется через Alembic (расширение pgvector)
    status: Mapped[ResumeStatus] = mapped_column(
        Enum(ResumeStatus, name='resume_status', native_enum=False),
        default=ResumeStatus.DRAFT,
        server_default='draft',
    )

    # Relationships
    user: Mapped[User] = relationship(back_populates='resumes')
    rewrite_history: Mapped[list[RewriteHistory]] = relationship(
        back_populates='resume',
        cascade='all, delete-orphan',
        lazy='selectin',
    )

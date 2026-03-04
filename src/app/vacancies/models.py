"""SQLAlchemy-модель вакансии."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, UUIDMixin

if TYPE_CHECKING:
    from app.auth.models import User
    from app.rewriter.models import RewriteHistory


class Vacancy(UUIDMixin, Base):
    """Вакансия (из hh.ru или введённая вручную)."""

    __tablename__ = 'vacancies'

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    hh_id: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    key_skills: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    salary_from: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_to: Mapped[int | None] = mapped_column(Integer, nullable=True)
    experience: Mapped[str | None] = mapped_column(String(50), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # embedding VECTOR(1536) добавляется через Alembic
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    # Relationships
    user: Mapped[User] = relationship(back_populates='vacancies')
    rewrite_history: Mapped[list[RewriteHistory]] = relationship(
        back_populates='vacancy',
        cascade='all, delete-orphan',
        lazy='selectin',
    )

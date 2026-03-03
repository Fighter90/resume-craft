"""SQLAlchemy-модель пользователя."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.resumes.models import Resume
    from app.rewriter.models import RewriteHistory
    from app.vacancies.models import Vacancy


class UserPlan(str, enum.Enum):
    """Тарифный план пользователя."""

    FREE = 'free'
    STANDARD = 'standard'
    PRO = 'pro'


# Лимиты оптимизаций по тарифу
PLAN_LIMITS: dict[UserPlan, int | None] = {
    UserPlan.FREE: 5,
    UserPlan.STANDARD: 30,
    UserPlan.PRO: None,  # безлимит
}


class User(UUIDMixin, TimestampMixin, Base):
    """Модель пользователя."""

    __tablename__ = 'users'

    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True,
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    plan: Mapped[UserPlan] = mapped_column(
        Enum(UserPlan, name='user_plan', native_enum=False),
        default=UserPlan.FREE,
        server_default='free',
    )
    optimizations_used: Mapped[int] = mapped_column(Integer, default=0, server_default='0')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default='true')

    # Relationships
    resumes: Mapped[list[Resume]] = relationship(
        back_populates='user', cascade='all, delete-orphan', lazy='selectin',
    )
    vacancies: Mapped[list[Vacancy]] = relationship(
        back_populates='user', cascade='all, delete-orphan', lazy='selectin',
    )
    rewrite_history: Mapped[list[RewriteHistory]] = relationship(
        back_populates='user', cascade='all, delete-orphan', lazy='selectin',
    )

    @property
    def optimization_limit(self) -> int | None:
        """Лимит оптимизаций для текущего тарифа (None = безлимит)."""
        return PLAN_LIMITS.get(self.plan)

    @property
    def can_optimize(self) -> bool:
        """Может ли пользователь выполнить ещё одну оптимизацию."""
        limit = self.optimization_limit
        if limit is None:
            return True
        return self.optimizations_used < limit

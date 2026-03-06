"""SQLAlchemy-модель пользовательских настроек."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDMixin


class UserSetting(UUIDMixin, TimestampMixin, Base):
    """Настройка пользователя (включая зашифрованные API-ключи)."""

    __tablename__ = 'user_settings'
    __table_args__ = (
        UniqueConstraint('user_id', 'category', 'key', name='uq_user_settings_user_cat_key'),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False, default='')
    is_encrypted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

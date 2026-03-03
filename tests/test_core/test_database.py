"""Тесты модуля core/database.py."""

from __future__ import annotations

from app.core.database import Base, TimestampMixin, UUIDMixin, get_engine, get_session_factory


class TestDatabase:
    """Тесты базы данных."""

    def test_base_exists(self) -> None:
        """Base — описанная DeclarativeBase."""
        assert hasattr(Base, 'metadata')

    def test_base_naming_convention(self) -> None:
        """Naming convention для constraints."""
        nc = Base.metadata.naming_convention
        assert 'ix' in nc
        assert 'uq' in nc
        assert 'fk' in nc
        assert 'pk' in nc

    def test_get_engine(self) -> None:
        """get_engine() возвращает engine."""
        engine = get_engine()
        assert engine is not None

    def test_get_engine_singleton(self) -> None:
        """get_engine() возвращает один и тот же объект."""
        e1 = get_engine()
        e2 = get_engine()
        assert e1 is e2

    def test_get_session_factory(self) -> None:
        """get_session_factory() возвращает фабрику."""
        factory = get_session_factory()
        assert factory is not None

    def test_timestamp_mixin_fields(self) -> None:
        """TimestampMixin имеет created_at и updated_at."""
        assert hasattr(TimestampMixin, 'created_at')
        assert hasattr(TimestampMixin, 'updated_at')

    def test_uuid_mixin_field(self) -> None:
        """UUIDMixin имеет id."""
        assert hasattr(UUIDMixin, 'id')

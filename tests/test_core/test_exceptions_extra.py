"""Дополнительные тесты core/exceptions.py — FileContentMismatch."""

from __future__ import annotations

from app.core.exceptions import FileContentMismatch, LLMResponseError, TariffLimitExceeded


class TestFileContentMismatch:
    """Тест создания FileContentMismatch."""

    def test_default_message(self) -> None:
        exc = FileContentMismatch()
        assert exc.message == 'Содержимое файла не соответствует расширению'
        assert exc.status_code == 400
        assert exc.error_code == 'FILE_CONTENT_MISMATCH'


class TestTariffLimitExceededDetail:
    """Тест TariffLimitExceeded с detail."""

    def test_with_limits(self) -> None:
        exc = TariffLimitExceeded(used=5, limit=5)
        assert exc.detail == 'Использовано 5 из 5. Обновите тарифный план.'

    def test_without_limits(self) -> None:
        exc = TariffLimitExceeded()
        assert exc.detail is None


class TestLLMResponseError:
    """Тест LLMResponseError."""

    def test_with_detail(self) -> None:
        exc = LLMResponseError(detail='Invalid JSON')
        assert exc.status_code == 502
        assert exc.detail == 'Invalid JSON'

    def test_without_detail(self) -> None:
        exc = LLMResponseError()
        assert exc.detail is None

"""Тесты модуля core/exceptions.py."""

from __future__ import annotations

import pytest

from app.core.exceptions import (
    AppError,
    FileTooLarge,
    HHApiError,
    InactiveUser,
    InvalidCredentials,
    LLMProviderUnavailable,
    LLMResponseError,
    ResumeNotFound,
    RewriteTaskNotFound,
    TariffLimitExceeded,
    TokenExpired,
    TokenInvalid,
    UnsupportedFileFormat,
    UserAlreadyExists,
    UserNotFound,
    VacancyNotFound,
)


class TestAppError:
    """Тесты базового AppError."""

    def test_default_values(self) -> None:
        err = AppError('test')
        assert err.message == 'test'
        assert err.status_code == 500
        assert err.error_code == 'INTERNAL_ERROR'
        assert err.detail is None

    def test_custom_values(self) -> None:
        err = AppError('msg', status_code=400, error_code='CUSTOM', detail='x')
        assert err.status_code == 400
        assert err.error_code == 'CUSTOM'
        assert err.detail == 'x'

    def test_str_representation(self) -> None:
        err = AppError('hello')
        assert str(err) == 'hello'


class TestAuthExceptions:
    def test_invalid_credentials(self) -> None:
        err = InvalidCredentials()
        assert err.status_code == 401
        assert err.error_code == 'INVALID_CREDENTIALS'

    def test_token_expired(self) -> None:
        err = TokenExpired()
        assert err.status_code == 401
        assert err.error_code == 'TOKEN_EXPIRED'

    def test_token_invalid(self) -> None:
        err = TokenInvalid()
        assert err.status_code == 401

    def test_user_already_exists_default(self) -> None:
        err = UserAlreadyExists()
        assert err.status_code == 409
        assert 'уже существует' in err.message

    def test_user_already_exists_with_email(self) -> None:
        err = UserAlreadyExists('test@example.com')
        assert 'test@example.com' in err.message
        assert err.status_code == 409

    def test_user_not_found(self) -> None:
        err = UserNotFound()
        assert err.status_code == 404

    def test_inactive_user(self) -> None:
        err = InactiveUser()
        assert err.status_code == 403


class TestResumeExceptions:
    def test_resume_not_found(self) -> None:
        err = ResumeNotFound()
        assert err.status_code == 404

    def test_unsupported_format_default(self) -> None:
        err = UnsupportedFileFormat()
        assert err.status_code == 400

    def test_unsupported_format_with_detail(self) -> None:
        err = UnsupportedFileFormat('exe не поддерживается')
        assert 'exe' in err.message

    def test_file_too_large_default(self) -> None:
        err = FileTooLarge()
        assert '10' in err.message
        assert err.status_code == 413

    def test_file_too_large_custom(self) -> None:
        err = FileTooLarge(max_mb=50)
        assert '50' in err.message


class TestVacancyExceptions:
    def test_vacancy_not_found(self) -> None:
        err = VacancyNotFound()
        assert err.status_code == 404

    def test_hh_api_error(self) -> None:
        err = HHApiError('connection timeout')
        assert err.status_code == 502
        assert err.detail == 'connection timeout'

    def test_hh_api_error_default(self) -> None:
        err = HHApiError()
        assert err.status_code == 502


class TestRewriterExceptions:
    def test_tariff_limit_default(self) -> None:
        err = TariffLimitExceeded()
        assert err.status_code == 429

    def test_tariff_limit_with_values(self) -> None:
        err = TariffLimitExceeded(used=5, limit=5)
        assert '5 из 5' in (err.detail or '')
        assert err.status_code == 429

    def test_rewrite_task_not_found_default(self) -> None:
        err = RewriteTaskNotFound()
        assert err.status_code == 404

    def test_rewrite_task_not_found_with_id(self) -> None:
        err = RewriteTaskNotFound('abc-123')
        assert 'abc-123' in err.message

    def test_llm_provider_unavailable(self) -> None:
        err = LLMProviderUnavailable('gigachat')
        assert err.status_code == 503
        assert 'gigachat' in err.message

    def test_llm_response_error(self) -> None:
        err = LLMResponseError('bad json')
        assert err.status_code == 502
        assert err.detail == 'bad json'

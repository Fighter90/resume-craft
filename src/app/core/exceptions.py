"""Кастомные HTTP-исключения с единым JSON-форматом."""

from __future__ import annotations


class AppError(Exception):
    """Базовое исключение приложения."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 500,
        error_code: str = 'INTERNAL_ERROR',
        detail: str | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.detail = detail
        super().__init__(message)


# --- Auth ---
class InvalidCredentials(AppError):
    def __init__(self) -> None:
        super().__init__(
            message='Неверный email или пароль',
            status_code=401,
            error_code='INVALID_CREDENTIALS',
        )


class TokenExpired(AppError):
    def __init__(self) -> None:
        super().__init__(
            message='Токен истёк',
            status_code=401,
            error_code='TOKEN_EXPIRED',
        )


class TokenInvalid(AppError):
    def __init__(self) -> None:
        super().__init__(
            message='Невалидный токен',
            status_code=401,
            error_code='TOKEN_INVALID',
        )


class UserAlreadyExists(AppError):
    def __init__(self, email: str = '') -> None:
        msg = (
            f'Пользователь с email {email} уже существует'
            if email
            else 'Пользователь уже существует'
        )
        super().__init__(
            message=msg,
            status_code=409,
            error_code='USER_ALREADY_EXISTS',
        )


class UserNotFound(AppError):
    def __init__(self) -> None:
        super().__init__(
            message='Пользователь не найден',
            status_code=404,
            error_code='USER_NOT_FOUND',
        )


class InactiveUser(AppError):
    def __init__(self) -> None:
        super().__init__(
            message='Аккаунт деактивирован',
            status_code=403,
            error_code='INACTIVE_USER',
        )


# --- Resumes ---
class ResumeNotFound(AppError):
    def __init__(self) -> None:
        super().__init__(
            message='Резюме не найдено',
            status_code=404,
            error_code='RESUME_NOT_FOUND',
        )


class UnsupportedFileFormat(AppError):
    def __init__(self, detail: str = '') -> None:
        super().__init__(
            message=detail or 'Неподдерживаемый формат файла',
            status_code=400,
            error_code='UNSUPPORTED_FORMAT',
        )


class FileTooLarge(AppError):
    def __init__(self, max_mb: int = 10) -> None:
        super().__init__(
            message=f'Файл слишком большой (максимум {max_mb} МБ)',
            status_code=413,
            error_code='FILE_TOO_LARGE',
        )


class FileContentMismatch(AppError):
    def __init__(self) -> None:
        super().__init__(
            message='Содержимое файла не соответствует расширению',
            status_code=400,
            error_code='FILE_CONTENT_MISMATCH',
        )


# --- Vacancies ---
class VacancyNotFound(AppError):
    def __init__(self) -> None:
        super().__init__(
            message='Вакансия не найдена',
            status_code=404,
            error_code='VACANCY_NOT_FOUND',
        )


class HHApiError(AppError):
    def __init__(self, detail: str | None = None) -> None:
        super().__init__(
            message='Ошибка API HeadHunter',
            status_code=502,
            error_code='HH_API_ERROR',
            detail=detail,
        )


# --- Rewriter ---
class TariffLimitExceeded(AppError):
    def __init__(self, used: int = 0, limit: int = 0) -> None:
        detail = f'Использовано {used} из {limit}. Обновите тарифный план.' if limit else None
        super().__init__(
            message='Лимит оптимизаций исчерпан',
            status_code=429,
            error_code='TARIFF_LIMIT_EXCEEDED',
            detail=detail,
        )


class RewriteTaskNotFound(AppError):
    def __init__(self, task_id: str = '') -> None:
        msg = (
            f'Задача оптимизации {task_id} не найдена'
            if task_id
            else 'Задача оптимизации не найдена'
        )
        super().__init__(
            message=msg,
            status_code=404,
            error_code='REWRITE_TASK_NOT_FOUND',
        )


class LLMProviderUnavailable(AppError):
    def __init__(self, provider: str) -> None:
        super().__init__(
            message=f'LLM-провайдер {provider} временно недоступен',
            status_code=503,
            error_code='LLM_UNAVAILABLE',
        )


class LLMResponseError(AppError):
    def __init__(self, detail: str | None = None) -> None:
        super().__init__(
            message='Невалидный ответ от LLM',
            status_code=502,
            error_code='LLM_RESPONSE_ERROR',
            detail=detail,
        )

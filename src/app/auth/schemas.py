"""Pydantic-схемы для модуля аутентификации."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.auth.models import UserPlan

# --- Requests ---


class RegisterRequest(BaseModel):
    """Запрос на регистрацию."""

    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=128,
        description='Пароль (≥8 символов, минимум 1 цифра и 1 буква)',
    )
    full_name: str | None = Field(None, max_length=255, description='Полное имя')

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Проверка надёжности пароля."""
        if not any(c.isdigit() for c in v):
            msg = 'Пароль должен содержать хотя бы одну цифру'
            raise ValueError(msg)
        if not any(c.isalpha() for c in v):
            msg = 'Пароль должен содержать хотя бы одну букву'
            raise ValueError(msg)
        return v

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            'examples': [
                {
                    'email': 'user@example.com',
                    'password': 'SecurePass1',
                    'full_name': 'Иван Иванов',
                },
            ],
        },
    )


class LoginRequest(BaseModel):
    """Запрос на авторизацию."""

    email: EmailStr
    password: str = Field(min_length=1, description='Пароль')

    model_config = ConfigDict(str_strip_whitespace=True)


class RefreshRequest(BaseModel):
    """Запрос на обновление токена."""

    refresh_token: str = Field(min_length=1, description='Refresh-токен')


# --- Responses ---


class TokenResponse(BaseModel):
    """Ответ с JWT-токенами."""

    access_token: str
    refresh_token: str
    token_type: str = 'bearer'  # noqa: S105


class UserResponse(BaseModel):
    """Публичные данные пользователя."""

    id: UUID
    email: str
    full_name: str | None
    plan: UserPlan
    optimizations_used: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    """Ответ с сообщением."""

    message: str


class UpdateUserRequest(BaseModel):
    """Обновление профиля пользователя."""

    full_name: str | None = Field(None, max_length=255, description='Полное имя')
    email: EmailStr | None = Field(None, description='Новый email')

    model_config = ConfigDict(str_strip_whitespace=True)


class PasswordChangeRequest(BaseModel):
    """Запрос на смену пароля."""

    current_password: str = Field(min_length=1, description='Текущий пароль')
    new_password: str = Field(
        min_length=8,
        max_length=128,
        description='Новый пароль (≥8 символов, минимум 1 цифра и 1 буква)',
    )

    @field_validator('new_password')
    @classmethod
    def validate_new_password_strength(cls, v: str) -> str:
        """Проверка надёжности нового пароля."""
        if not any(c.isdigit() for c in v):
            msg = 'Пароль должен содержать хотя бы одну цифру'
            raise ValueError(msg)
        if not any(c.isalpha() for c in v):
            msg = 'Пароль должен содержать хотя бы одну букву'
            raise ValueError(msg)
        return v

    model_config = ConfigDict(str_strip_whitespace=True)


class DeleteAccountRequest(BaseModel):
    """Запрос на удаление аккаунта — требует подтверждение паролем."""

    password: str = Field(min_length=1, description='Текущий пароль для подтверждения')

    model_config = ConfigDict(str_strip_whitespace=True)

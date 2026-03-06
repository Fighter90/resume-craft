"""Pydantic-схемы для настроек пользователя."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AIKeyUpdate(BaseModel):
    """Обновление API-ключа провайдера."""

    api_key: str = Field(min_length=1, max_length=500, description='API-ключ провайдера')

    model_config = ConfigDict(str_strip_whitespace=True)


class AIKeyStatus(BaseModel):
    """Статус API-ключа провайдера (маскированный)."""

    provider: str
    has_key: bool
    masked_key: str = ''


class AIKeysResponse(BaseModel):
    """Ответ со статусами всех API-ключей."""

    keys: list[AIKeyStatus]


class AIToggle(BaseModel):
    """Настройка AI-переключателя."""

    key: str
    value: bool


class AITogglesUpdate(BaseModel):
    """Обновление AI-настроек (toggles)."""

    toggles: list[AIToggle]

    model_config = ConfigDict(str_strip_whitespace=True)


class AITogglesResponse(BaseModel):
    """Текущие AI-настройки (toggles)."""

    toggles: dict[str, bool]


class SelectedModelUpdate(BaseModel):
    """Обновление выбранной модели."""

    model: str = Field(min_length=1, max_length=100)
    sub_model: str | None = Field(None, max_length=200)

    model_config = ConfigDict(str_strip_whitespace=True)


class SelectedModelResponse(BaseModel):
    """Текущая выбранная модель."""

    model: str
    sub_model: str | None = None

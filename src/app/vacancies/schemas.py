"""Pydantic-схемы для модуля вакансий."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class VacancyFromUrlRequest(BaseModel):
    """Создание вакансии из URL hh.ru."""

    url: HttpUrl = Field(description='Ссылка на вакансию hh.ru')

    model_config = ConfigDict(str_strip_whitespace=True)


class VacancyManualRequest(BaseModel):
    """Ручное создание вакансии."""

    title: str = Field(max_length=255, description='Название вакансии')
    company: str | None = Field(None, max_length=255, description='Компания')
    description: str = Field(description='Описание вакансии')
    requirements: dict[str, Any] | None = Field(None, description='Требования (JSON)')
    key_skills: list[str] | None = Field(None, description='Ключевые навыки')
    salary_from: int | None = Field(None, ge=0, description='Зарплата от')
    salary_to: int | None = Field(None, ge=0, description='Зарплата до')
    experience: str | None = Field(None, max_length=50, description='Требуемый опыт')
    city: str | None = Field(None, max_length=100, description='Город')
    source_url: str | None = Field(None, max_length=500, description='URL источника')

    model_config = ConfigDict(str_strip_whitespace=True)


class VacancyResponse(BaseModel):
    """Данные вакансии."""

    id: UUID
    user_id: UUID
    hh_id: str | None
    title: str
    company: str | None
    description: str | None
    requirements: dict[str, Any] | None
    key_skills: list[str] | None
    salary_from: int | None
    salary_to: int | None
    experience: str | None
    city: str | None
    source_url: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HHSearchParams(BaseModel):
    """Параметры поиска вакансий на hh.ru."""

    text: str = Field(min_length=1, max_length=500, description='Поисковый запрос')
    area: int = Field(1, description='Регион (1 = Москва)')
    per_page: int = Field(20, ge=1, le=100, description='Кол-во результатов')


class HHVacancyItem(BaseModel):
    """Краткая информация о вакансии с hh.ru."""

    hh_id: str
    title: str
    company: str | None = None
    city: str | None = None
    salary_from: int | None = None
    salary_to: int | None = None
    url: str


class HHSearchResponse(BaseModel):
    """Результаты поиска вакансий hh.ru."""

    items: list[HHVacancyItem]
    found: int
    page: int
    pages: int

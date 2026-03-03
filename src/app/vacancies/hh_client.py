"""Async HTTP-клиент для api.hh.ru."""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.exceptions import HHApiError

logger = logging.getLogger(__name__)

settings = get_settings()


class HHClient:
    """Асинхронный клиент для HeadHunter API.

    Rate limits:
    - Анонимный: ≤ 2 req/sec
    - Авторизованный: ≤ 7 req/sec
    """

    BASE_URL = 'https://api.hh.ru'

    def __init__(self, user_agent: str | None = None) -> None:
        self._headers = {'User-Agent': user_agent or settings.hh_user_agent}
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=self._headers,
            timeout=httpx.Timeout(10.0),
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        reraise=True,
    )
    async def search_vacancies(
        self,
        text: str,
        *,
        area: int = 1,
        per_page: int = 20,
        page: int = 0,
    ) -> dict[str, Any]:
        """Поиск вакансий.

        Raises:
            HHApiError: при ошибке API hh.ru.
        """
        try:
            response = await self._client.get(
                '/vacancies',
                params={
                    'text': text,
                    'area': area,
                    'per_page': min(per_page, 100),
                    'page': page,
                },
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            msg = f'hh.ru API returned {exc.response.status_code}'
            raise HHApiError(msg) from exc
        except httpx.RequestError as exc:
            msg = f'hh.ru API connection error: {exc}'
            raise HHApiError(msg) from exc

        return response.json()  # type: ignore[no-any-return]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        reraise=True,
    )
    async def get_vacancy(self, vacancy_id: str) -> dict[str, Any]:
        """Получение полной информации о вакансии.

        Raises:
            HHApiError: при ошибке API hh.ru.
        """
        try:
            response = await self._client.get(f'/vacancies/{vacancy_id}')
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            msg = f'hh.ru vacancy {vacancy_id}: HTTP {exc.response.status_code}'
            raise HHApiError(msg) from exc
        except httpx.RequestError as exc:
            msg = f'hh.ru API connection error: {exc}'
            raise HHApiError(msg) from exc

        return response.json()  # type: ignore[no-any-return]

    async def close(self) -> None:
        """Закрытие HTTP-клиента."""
        await self._client.aclose()


def extract_hh_vacancy_id(url: str) -> str:
    """Извлечение ID вакансии из URL hh.ru.

    Поддерживаемые форматы:
    - https://hh.ru/vacancy/12345678
    - https://api.hh.ru/vacancies/12345678

    Raises:
        ValueError: невалидный URL.
    """
    pattern = r'(?:hh\.ru/vacancy|api\.hh\.ru/vacancies)/(\d+)'
    match = re.search(pattern, url)
    if not match:
        msg = f'Невалидный URL вакансии hh.ru: {url}'
        raise ValueError(msg)
    return match.group(1)


def parse_hh_vacancy(data: dict[str, Any]) -> dict[str, Any]:
    """Преобразование ответа hh.ru API в формат приложения."""
    salary = data.get('salary') or {}
    employer = data.get('employer') or {}
    area = data.get('area') or {}
    experience = data.get('experience') or {}
    key_skills = [s.get('name', '') for s in data.get('key_skills', []) if s.get('name')]

    return {
        'hh_id': str(data.get('id', '')),
        'title': data.get('name', ''),
        'company': employer.get('name'),
        'description': data.get('description', ''),
        'requirements': {
            'experience': experience.get('name'),
            'description': data.get('description'),
        },
        'key_skills': key_skills,
        'salary_from': salary.get('from'),
        'salary_to': salary.get('to'),
        'experience': experience.get('name'),
        'city': area.get('name'),
        'source_url': data.get('alternate_url', ''),
    }

"""Дополнительные тесты vacancies/hh_client.py — RequestError paths."""

from __future__ import annotations

from unittest.mock import AsyncMock

import httpx
import pytest

from app.core.exceptions import HHApiError
from app.vacancies.hh_client import HHClient


class TestSearchVacanciesErrors:
    """Тесты ошибок search_vacancies()."""

    async def test_search_connection_error(self) -> None:
        """ConnectionError при поиске → HHApiError."""
        client = HHClient(user_agent='TestAgent/1.0')

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(
            side_effect=httpx.ConnectError('Connection refused'),
        )
        mock_http.aclose = AsyncMock()

        client._client = mock_http

        with pytest.raises(HHApiError):
            await client.search_vacancies(text='python')

        await client.close()

    async def test_search_timeout_error(self) -> None:
        """Timeout при поиске → HHApiError."""
        client = HHClient(user_agent='TestAgent/1.0')

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(
            side_effect=httpx.ReadTimeout('Read timed out'),
        )
        mock_http.aclose = AsyncMock()

        client._client = mock_http

        with pytest.raises(HHApiError):
            await client.search_vacancies(text='python')

        await client.close()


class TestGetVacancyErrors:
    """Тесты ошибок get_vacancy()."""

    async def test_get_vacancy_connection_error(self) -> None:
        """ConnectionError при получении вакансии → HHApiError."""
        client = HHClient(user_agent='TestAgent/1.0')

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(
            side_effect=httpx.ConnectError('Connection refused'),
        )
        mock_http.aclose = AsyncMock()

        client._client = mock_http

        with pytest.raises(HHApiError):
            await client.get_vacancy(vacancy_id='12345')

        await client.close()

    async def test_get_vacancy_timeout_error(self) -> None:
        """Timeout при получении вакансии → HHApiError."""
        client = HHClient(user_agent='TestAgent/1.0')

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(
            side_effect=httpx.ReadTimeout('Read timed out'),
        )
        mock_http.aclose = AsyncMock()

        client._client = mock_http

        with pytest.raises(HHApiError):
            await client.get_vacancy(vacancy_id='12345')

        await client.close()

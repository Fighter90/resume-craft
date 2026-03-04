"""Дополнительные тесты vacancies/hh_client.py — все непокрытые пути."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from tenacity import stop_after_attempt, wait_none

from app.core.exceptions import HHApiError
from app.vacancies.hh_client import HHClient


def _disable_retry(client: HHClient) -> None:
    """Отключаем retry (1 попытка) чтобы тесты не ждали backoff."""
    client.search_vacancies.retry.stop = stop_after_attempt(1)  # type: ignore[union-attr]
    client.search_vacancies.retry.wait = wait_none()  # type: ignore[union-attr]
    client.get_vacancy.retry.stop = stop_after_attempt(1)  # type: ignore[union-attr]
    client.get_vacancy.retry.wait = wait_none()  # type: ignore[union-attr]


def _make_client() -> HHClient:
    """Создать HHClient с отключённым retry."""
    c = HHClient(user_agent='TestAgent/1.0')
    _disable_retry(c)
    return c


class TestSearchVacanciesSuccess:
    """Успешные пути search_vacancies()."""

    async def test_search_returns_json(self) -> None:
        """Успешный поиск → dict с items."""
        client = _make_client()
        expected = {'items': [{'id': '1', 'name': 'Dev'}], 'found': 1}

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = expected

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=mock_response)
        mock_http.aclose = AsyncMock()
        client._client = mock_http

        result = await client.search_vacancies(text='python')
        assert result == expected
        await client.close()


class TestSearchVacanciesErrors:
    """Тесты ошибок search_vacancies()."""

    async def test_search_connection_error(self) -> None:
        """ConnectionError при поиске → HHApiError."""
        client = _make_client()

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
        client = _make_client()

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(
            side_effect=httpx.ReadTimeout('Read timed out'),
        )
        mock_http.aclose = AsyncMock()
        client._client = mock_http

        with pytest.raises(HHApiError):
            await client.search_vacancies(text='python')
        await client.close()

    async def test_search_http_status_error(self) -> None:
        """HTTP 500 при поиске → HHApiError."""
        client = _make_client()

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            'Server Error',
            request=httpx.Request('GET', 'https://api.hh.ru/vacancies'),
            response=httpx.Response(500),
        )

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=mock_response)
        mock_http.aclose = AsyncMock()
        client._client = mock_http

        with pytest.raises(HHApiError):
            await client.search_vacancies(text='python')
        await client.close()


class TestGetVacancySuccess:
    """Успешные пути get_vacancy()."""

    async def test_get_vacancy_returns_json(self) -> None:
        """Успешное получение вакансии → dict."""
        client = _make_client()
        expected = {'id': '12345', 'name': 'Python Dev', 'description': 'test'}

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = expected

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=mock_response)
        mock_http.aclose = AsyncMock()
        client._client = mock_http

        result = await client.get_vacancy(vacancy_id='12345')
        assert result == expected
        await client.close()


class TestGetVacancyErrors:
    """Тесты ошибок get_vacancy()."""

    async def test_get_vacancy_connection_error(self) -> None:
        """ConnectionError при получении вакансии → HHApiError."""
        client = _make_client()

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
        client = _make_client()

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(
            side_effect=httpx.ReadTimeout('Read timed out'),
        )
        mock_http.aclose = AsyncMock()
        client._client = mock_http

        with pytest.raises(HHApiError):
            await client.get_vacancy(vacancy_id='12345')
        await client.close()

    async def test_get_vacancy_http_status_error(self) -> None:
        """HTTP 404 при получении вакансии → HHApiError."""
        client = _make_client()

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            'Not Found',
            request=httpx.Request('GET', 'https://api.hh.ru/vacancies/99999'),
            response=httpx.Response(404),
        )

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=mock_response)
        mock_http.aclose = AsyncMock()
        client._client = mock_http

        with pytest.raises(HHApiError):
            await client.get_vacancy(vacancy_id='99999')
        await client.close()

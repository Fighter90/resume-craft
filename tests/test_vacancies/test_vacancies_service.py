"""Тесты vacancies/service.py и vacancies/hh_client.py."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.exceptions import HHApiError, VacancyNotFound
from app.vacancies.hh_client import HHClient, extract_hh_vacancy_id, parse_hh_vacancy
from app.vacancies.models import Vacancy
from app.vacancies.schemas import HHSearchParams, VacancyManualRequest
from app.vacancies.service import create_from_url, create_manual, get_vacancy, search_hh

# ── HHClient ──────────────────────────────────────────────────────────────────


class TestExtractHHVacancyId:
    """Тесты extract_hh_vacancy_id()."""

    def test_standard_url(self) -> None:
        result = extract_hh_vacancy_id('https://hh.ru/vacancy/12345678')
        assert result == '12345678'

    def test_api_url(self) -> None:
        result = extract_hh_vacancy_id('https://api.hh.ru/vacancies/99999999')
        assert result == '99999999'

    def test_url_with_query(self) -> None:
        result = extract_hh_vacancy_id('https://hh.ru/vacancy/12345678?from=search')
        assert result == '12345678'

    def test_invalid_url(self) -> None:
        with pytest.raises(ValueError, match='Невалидный URL'):
            extract_hh_vacancy_id('https://google.com/search?q=vacancy')

    def test_empty_url(self) -> None:
        with pytest.raises(ValueError, match='Невалидный URL'):
            extract_hh_vacancy_id('')


class TestParseHHVacancy:
    """Тесты parse_hh_vacancy()."""

    def test_full_data(self) -> None:
        data = {
            'id': '12345',
            'name': 'Python Developer',
            'employer': {'name': 'Yandex'},
            'area': {'name': 'Москва'},
            'salary': {'from': 200000, 'to': 350000},
            'experience': {'name': '3–6 лет'},
            'description': '<p>Описание вакансии</p>',
            'key_skills': [{'name': 'Python'}, {'name': 'FastAPI'}],
            'alternate_url': 'https://hh.ru/vacancy/12345',
        }
        result = parse_hh_vacancy(data)
        assert result['hh_id'] == '12345'
        assert result['title'] == 'Python Developer'
        assert result['company'] == 'Yandex'
        assert result['city'] == 'Москва'
        assert result['salary_from'] == 200000
        assert result['salary_to'] == 350000
        assert result['key_skills'] == ['Python', 'FastAPI']

    def test_minimal_data(self) -> None:
        data = {'id': '1', 'name': 'Test'}
        result = parse_hh_vacancy(data)
        assert result['hh_id'] == '1'
        assert result['title'] == 'Test'
        assert result['company'] is None
        assert result['salary_from'] is None
        assert result['key_skills'] == []

    def test_empty_salary(self) -> None:
        data = {'id': '1', 'name': 'Test', 'salary': None}
        result = parse_hh_vacancy(data)
        assert result['salary_from'] is None


class TestHHClient:
    """Тесты HHClient."""

    async def test_search_vacancies_success(self) -> None:
        """Успешный поиск вакансий."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'items': [{'id': '1', 'name': 'Dev'}],
            'found': 1,
            'page': 0,
            'pages': 1,
        }
        mock_response.raise_for_status = MagicMock()

        client = HHClient(user_agent='Test/1.0')
        with patch.object(
            client._client,
            'get',
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await client.search_vacancies('python')
            assert result['items'][0]['id'] == '1'

        await client.close()

    async def test_search_vacancies_http_error(self) -> None:
        """HTTP ошибка → HHApiError."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        error = httpx.HTTPStatusError('too many', request=MagicMock(), response=mock_response)
        mock_response.raise_for_status.side_effect = error

        client = HHClient(user_agent='Test/1.0')
        with (
            patch.object(
                client._client,
                'get',
                new_callable=AsyncMock,
                return_value=mock_response,
            ),
            pytest.raises(HHApiError),
        ):
            await client.search_vacancies('python')
        await client.close()

    async def test_get_vacancy_success(self) -> None:
        """Получение вакансии по ID."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'id': '123', 'name': 'Test'}
        mock_response.raise_for_status = MagicMock()

        client = HHClient(user_agent='Test/1.0')
        with patch.object(
            client._client,
            'get',
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await client.get_vacancy('123')
            assert result['id'] == '123'
        await client.close()

    async def test_get_vacancy_connection_error(self) -> None:
        """Ошибка подключения → HHApiError."""
        client = HHClient(user_agent='Test/1.0')
        error = httpx.RequestError('connection failed', request=MagicMock())
        with (
            patch.object(
                client._client,
                'get',
                new_callable=AsyncMock,
                side_effect=error,
            ),
            pytest.raises(HHApiError),
        ):
            await client.get_vacancy('123')
        await client.close()


# ── VacancyService ────────────────────────────────────────────────────────────


class TestSearchHH:
    """Тесты search_hh()."""

    @patch('app.vacancies.service.HHClient')
    async def test_search_success(self, mock_hh_cls: MagicMock) -> None:
        """Успешный поиск."""
        mock_client = AsyncMock()
        mock_client.search_vacancies.return_value = {
            'items': [
                {
                    'id': '1',
                    'name': 'Dev',
                    'employer': {'name': 'Yandex'},
                    'area': {'name': 'Москва'},
                    'salary': {'from': 200000, 'to': None},
                    'alternate_url': 'https://hh.ru/vacancy/1',
                },
            ],
            'found': 1,
            'page': 0,
            'pages': 1,
        }
        mock_client.close = AsyncMock()
        mock_hh_cls.return_value = mock_client

        params = HHSearchParams(text='python developer')
        result = await search_hh(params)
        assert result.found == 1
        assert len(result.items) == 1
        assert result.items[0].hh_id == '1'


class TestCreateFromUrl:
    """Тесты create_from_url()."""

    @patch('app.vacancies.service.HHClient')
    async def test_success(
        self,
        mock_hh_cls: MagicMock,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        """Создание вакансии из URL."""
        mock_client = AsyncMock()
        mock_client.get_vacancy.return_value = {
            'id': '12345',
            'name': 'Python Dev',
            'employer': {'name': 'Company'},
            'area': {'name': 'Москва'},
            'salary': {'from': 100000, 'to': 200000},
            'experience': {'name': '1–3 года'},
            'description': 'Full description',
            'key_skills': [{'name': 'Python'}],
            'alternate_url': 'https://hh.ru/vacancy/12345',
        }
        mock_client.close = AsyncMock()
        mock_hh_cls.return_value = mock_client

        vacancy = await create_from_url(
            session,
            user_id=test_user.id,
            url='https://hh.ru/vacancy/12345',
        )
        assert vacancy.hh_id == '12345'
        assert vacancy.title == 'Python Dev'
        assert vacancy.user_id == test_user.id


class TestCreateManual:
    """Тесты create_manual()."""

    async def test_success(self, session: AsyncSession, test_user: User) -> None:
        """Ручное создание вакансии."""
        data = VacancyManualRequest(
            title='Test Vacancy',
            company='TestCorp',
            description='Senior developer needed',
            key_skills=['Python', 'FastAPI'],
            city='Москва',
        )
        vacancy = await create_manual(session, user_id=test_user.id, data=data)
        assert vacancy.title == 'Test Vacancy'
        assert vacancy.company == 'TestCorp'
        assert vacancy.user_id == test_user.id


class TestGetVacancy:
    """Тесты get_vacancy()."""

    async def test_existing(self, session: AsyncSession, test_user: User) -> None:
        """Получение существующей вакансии."""
        vacancy = Vacancy(
            user_id=test_user.id,
            title='Test',
            description='Desc',
        )
        session.add(vacancy)
        await session.flush()

        result = await get_vacancy(session, vacancy_id=vacancy.id, user_id=test_user.id)
        assert result.id == vacancy.id

    async def test_nonexistent(self, session: AsyncSession, test_user: User) -> None:
        """Несуществующая → VacancyNotFound."""
        with pytest.raises(VacancyNotFound):
            await get_vacancy(session, vacancy_id=uuid4(), user_id=test_user.id)

    async def test_other_user(self, session: AsyncSession, test_user: User) -> None:
        """Чужая вакансия → VacancyNotFound (IDOR)."""
        vacancy = Vacancy(user_id=uuid4(), title='Other', description='Desc')
        session.add(vacancy)
        await session.flush()

        with pytest.raises(VacancyNotFound):
            await get_vacancy(session, vacancy_id=vacancy.id, user_id=test_user.id)

"""Тесты vacancies/router.py — API вакансий."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.vacancies.models import Vacancy
from app.vacancies.schemas import HHSearchResponse


class TestSearchVacancies:
    """GET /api/v1/vacancies/search."""

    async def test_no_auth(self, client: AsyncClient) -> None:
        resp = await client.get('/api/v1/vacancies/search', params={'text': 'python'})
        assert resp.status_code == 401

    @patch('app.vacancies.router.vacancy_service')
    async def test_success(self, mock_svc: AsyncMock, auth_client: AsyncClient) -> None:
        mock_svc.search_hh = AsyncMock(return_value=HHSearchResponse(
            items=[], found=0, page=0, pages=0,
        ))
        resp = await auth_client.get('/api/v1/vacancies/search', params={'text': 'python'})
        assert resp.status_code == 200


class TestCreateManualVacancy:
    """POST /api/v1/vacancies/manual."""

    async def test_no_auth(self, client: AsyncClient) -> None:
        resp = await client.post('/api/v1/vacancies/manual', json={'title': 'Test'})
        assert resp.status_code == 401

    async def test_success(
        self, auth_client: AsyncClient, session: AsyncSession, test_user: User,
    ) -> None:
        resp = await auth_client.post('/api/v1/vacancies/manual', json={
            'title': 'Python Dev',
            'description': 'Need a dev',
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data['title'] == 'Python Dev'


class TestCreateFromUrl:
    """POST /api/v1/vacancies/from-url."""

    async def test_no_auth(self, client: AsyncClient) -> None:
        resp = await client.post('/api/v1/vacancies/from-url', json={
            'url': 'https://hh.ru/vacancy/12345',
        })
        assert resp.status_code == 401

    @patch('app.vacancies.router.vacancy_service')
    async def test_success(
        self, mock_svc: AsyncMock,
        auth_client: AsyncClient, session: AsyncSession, test_user: User,
    ) -> None:
        """Успешное создание из URL hh.ru."""
        mock_vacancy = Vacancy(
            user_id=test_user.id, title='Developer', description='Desc',
            hh_id='12345', source_url='https://hh.ru/vacancy/12345',
        )
        session.add(mock_vacancy)
        await session.flush()

        mock_svc.create_from_url = AsyncMock(return_value=mock_vacancy)

        resp = await auth_client.post('/api/v1/vacancies/from-url', json={
            'url': 'https://hh.ru/vacancy/12345',
        })
        assert resp.status_code == 201


class TestGetVacancy:
    """GET /api/v1/vacancies/{id}."""

    async def test_not_found(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.get(f'/api/v1/vacancies/{uuid4()}')
        assert resp.status_code == 404

    async def test_success(
        self, auth_client: AsyncClient, session: AsyncSession, test_user: User,
    ) -> None:
        vacancy = Vacancy(
            user_id=test_user.id, title='Test', description='D',
        )
        session.add(vacancy)
        await session.flush()

        resp = await auth_client.get(f'/api/v1/vacancies/{vacancy.id}')
        assert resp.status_code == 200
        assert resp.json()['title'] == 'Test'


class TestDeleteVacancy:
    """DELETE /api/v1/vacancies/{id}."""

    async def test_not_found(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.delete(f'/api/v1/vacancies/{uuid4()}')
        assert resp.status_code == 404

    async def test_success(
        self, auth_client: AsyncClient, session: AsyncSession, test_user: User,
    ) -> None:
        vacancy = Vacancy(
            user_id=test_user.id, title='To Delete', description='D',
        )
        session.add(vacancy)
        await session.flush()

        resp = await auth_client.delete(f'/api/v1/vacancies/{vacancy.id}')
        assert resp.status_code == 204

    async def test_no_auth(self, client: AsyncClient) -> None:
        resp = await client.delete(f'/api/v1/vacancies/{uuid4()}')
        assert resp.status_code == 401

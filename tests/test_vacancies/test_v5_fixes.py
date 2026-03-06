"""Тесты для исправлений v5."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.vacancies.schemas import HHSearchParams, HHSnippet, HHVacancyItem
from app.vacancies.service import get_hh_vacancy_detail, search_hh


class TestGetHHVacancyDetail:
    """Тест get_hh_vacancy_detail() — получение полных данных вакансии с hh.ru."""

    @pytest.mark.asyncio
    async def test_returns_full_vacancy_item(self) -> None:
        """Полные данные вакансии преобразуются в HHVacancyItem."""
        mock_data = {
            'id': '12345',
            'name': 'Python Developer',
            'employer': {'name': 'Яндекс'},
            'area': {'name': 'Москва'},
            'salary': {'from': 200000, 'to': 350000},
            'experience': {'name': '3-6 лет'},
            'key_skills': [{'name': 'Python'}, {'name': 'FastAPI'}, {'name': 'Docker'}],
            'description': '<p>Описание вакансии</p>',
            'alternate_url': 'https://hh.ru/vacancy/12345',
        }

        with patch('app.vacancies.service.HHClient') as mock_cls:
            mock_client = AsyncMock()
            mock_client.get_vacancy.return_value = mock_data
            mock_cls.return_value = mock_client

            result = await get_hh_vacancy_detail('12345')

        assert isinstance(result, HHVacancyItem)
        assert result.hh_id == '12345'
        assert result.title == 'Python Developer'
        assert result.company == 'Яндекс'
        assert result.city == 'Москва'
        assert result.salary_from == 200000
        assert result.salary_to == 350000
        assert result.experience == '3-6 лет'
        assert result.key_skills == ['Python', 'FastAPI', 'Docker']
        assert result.description == '<p>Описание вакансии</p>'
        assert result.url == 'https://hh.ru/vacancy/12345'
        mock_client.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handles_missing_optional_fields(self) -> None:
        """Пустые поля не вызывают ошибок."""
        mock_data = {
            'id': '99',
            'name': 'Test',
            'alternate_url': '',
        }

        with patch('app.vacancies.service.HHClient') as mock_cls:
            mock_client = AsyncMock()
            mock_client.get_vacancy.return_value = mock_data
            mock_cls.return_value = mock_client

            result = await get_hh_vacancy_detail('99')

        assert result.hh_id == '99'
        assert result.company is None
        assert result.salary_from is None
        assert result.key_skills is None
        assert result.description is None

    @pytest.mark.asyncio
    async def test_closes_client_on_error(self) -> None:
        """Клиент закрывается даже при ошибке."""
        with patch('app.vacancies.service.HHClient') as mock_cls:
            mock_client = AsyncMock()
            mock_client.get_vacancy.side_effect = Exception('API error')
            mock_cls.return_value = mock_client

            with pytest.raises(Exception, match='API error'):
                await get_hh_vacancy_detail('fail')

            mock_client.close.assert_awaited_once()


class TestSearchHHWithSnippets:
    """Тест search_hh() — возвращает snippet, experience, key_skills."""

    @pytest.mark.asyncio
    async def test_returns_snippets_and_experience(self) -> None:
        """Поиск возвращает сниппеты и опыт."""
        mock_response = {
            'items': [{
                'id': '1',
                'name': 'Developer',
                'employer': {'name': 'Corp'},
                'area': {'name': 'СПб'},
                'salary': {'from': 100000, 'to': None},
                'experience': {'name': '1-3 года'},
                'key_skills': [{'name': 'Python'}, {'name': 'SQL'}],
                'snippet': {
                    'requirement': 'Знание Python',
                    'responsibility': 'Разработка API',
                },
                'description': '<p>Full description</p>',
                'alternate_url': 'https://hh.ru/vacancy/1',
            }],
            'found': 1,
            'page': 0,
            'pages': 1,
        }

        with patch('app.vacancies.service.HHClient') as mock_cls:
            mock_client = AsyncMock()
            mock_client.search_vacancies.return_value = mock_response
            mock_cls.return_value = mock_client

            params = HHSearchParams(text='Python')
            result = await search_hh(params)

        assert len(result.items) == 1
        item = result.items[0]
        assert item.experience == '1-3 года'
        assert item.key_skills == ['Python', 'SQL']
        assert item.snippet is not None
        assert item.snippet.requirement == 'Знание Python'
        assert item.snippet.responsibility == 'Разработка API'
        assert item.description == '<p>Full description</p>'

    @pytest.mark.asyncio
    async def test_null_snippets_are_handled(self) -> None:
        """Отсутствие сниппетов не вызывает ошибок."""
        mock_response = {
            'items': [{
                'id': '2',
                'name': 'Manager',
                'alternate_url': '',
            }],
            'found': 1,
            'page': 0,
            'pages': 1,
        }

        with patch('app.vacancies.service.HHClient') as mock_cls:
            mock_client = AsyncMock()
            mock_client.search_vacancies.return_value = mock_response
            mock_cls.return_value = mock_client

            params = HHSearchParams(text='Manager')
            result = await search_hh(params)

        item = result.items[0]
        assert item.snippet is None
        assert item.experience is None
        assert item.key_skills is None


class TestHHSnippetSchema:
    """Тест HHSnippet Pydantic-модели."""

    def test_snippet_with_data(self) -> None:
        s = HHSnippet(requirement='Python 3+', responsibility='Разработка')
        assert s.requirement == 'Python 3+'
        assert s.responsibility == 'Разработка'

    def test_snippet_nullable(self) -> None:
        s = HHSnippet()
        assert s.requirement is None
        assert s.responsibility is None


class TestHHVacancyItemExtended:
    """Тест расширенной HHVacancyItem с новыми полями."""

    def test_all_fields(self) -> None:
        item = HHVacancyItem(
            hh_id='123',
            title='Dev',
            company='Corp',
            city='Москва',
            salary_from=200000,
            salary_to=300000,
            experience='3-6 лет',
            key_skills=['Python', 'FastAPI'],
            snippet=HHSnippet(requirement='test', responsibility='test2'),
            description='Full description',
            url='https://hh.ru/vacancy/123',
        )
        assert item.experience == '3-6 лет'
        assert item.key_skills == ['Python', 'FastAPI']
        assert item.snippet is not None
        assert item.description == 'Full description'

    def test_minimal_fields(self) -> None:
        item = HHVacancyItem(hh_id='1', title='Test', url='')
        assert item.experience is None
        assert item.key_skills is None
        assert item.snippet is None
        assert item.description is None


class TestResumeDeleteGuard:
    """Тест: delete_resume не падает для резюме без файла."""

    @pytest.mark.asyncio
    async def test_delete_text_resume_no_file_path(self) -> None:
        """Удаление резюме с пустым file_path не вызывает ошибку."""
        from app.resumes.service import delete_resume

        mock_session = AsyncMock(spec=AsyncSession)
        mock_resume = MagicMock()
        mock_resume.id = uuid4()
        mock_resume.user_id = uuid4()
        mock_resume.file_path = ''  # Text resume — no file

        with patch('app.resumes.service.get_resume', return_value=mock_resume):
            with patch('app.resumes.service.file_storage') as mock_storage:
                await delete_resume(mock_session, resume_id=mock_resume.id, user_id=mock_resume.user_id)

                # file_storage.delete should NOT be called for empty file_path
                mock_storage.delete.assert_not_called()
                mock_session.delete.assert_awaited_once_with(mock_resume)

    @pytest.mark.asyncio
    async def test_delete_file_resume_calls_storage(self) -> None:
        """Удаление файлового резюме вызывает storage.delete."""
        from app.resumes.service import delete_resume

        mock_session = AsyncMock(spec=AsyncSession)
        mock_resume = MagicMock()
        mock_resume.id = uuid4()
        mock_resume.user_id = uuid4()
        mock_resume.file_path = 'uploads/resume.pdf'

        with patch('app.resumes.service.get_resume', return_value=mock_resume):
            with patch('app.resumes.service.file_storage') as mock_storage:
                mock_storage.delete = AsyncMock()
                await delete_resume(mock_session, resume_id=mock_resume.id, user_id=mock_resume.user_id)

                mock_storage.delete.assert_awaited_once_with('uploads/resume.pdf')
                mock_session.delete.assert_awaited_once_with(mock_resume)

    @pytest.mark.asyncio
    async def test_delete_handles_is_directory_error(self) -> None:
        """IsADirectoryError не роняет удаление."""
        from app.resumes.service import delete_resume

        mock_session = AsyncMock(spec=AsyncSession)
        mock_resume = MagicMock()
        mock_resume.id = uuid4()
        mock_resume.user_id = uuid4()
        mock_resume.file_path = 'some/path'

        with patch('app.resumes.service.get_resume', return_value=mock_resume):
            with patch('app.resumes.service.file_storage') as mock_storage:
                mock_storage.delete = AsyncMock(side_effect=IsADirectoryError('is a dir'))
                await delete_resume(mock_session, resume_id=mock_resume.id, user_id=mock_resume.user_id)
                # Should NOT raise, just log a warning
                mock_session.delete.assert_awaited_once_with(mock_resume)

    @pytest.mark.asyncio
    async def test_delete_handles_permission_error(self) -> None:
        """PermissionError не роняет удаление."""
        from app.resumes.service import delete_resume

        mock_session = AsyncMock(spec=AsyncSession)
        mock_resume = MagicMock()
        mock_resume.id = uuid4()
        mock_resume.user_id = uuid4()
        mock_resume.file_path = 'some/path'

        with patch('app.resumes.service.get_resume', return_value=mock_resume):
            with patch('app.resumes.service.file_storage') as mock_storage:
                mock_storage.delete = AsyncMock(side_effect=PermissionError('no perms'))
                await delete_resume(mock_session, resume_id=mock_resume.id, user_id=mock_resume.user_id)
                mock_session.delete.assert_awaited_once_with(mock_resume)


class TestVacancyRouterHHEndpoint:
    """Тест нового эндпоинта /vacancies/hh/{hh_id}."""

    @pytest.mark.asyncio
    async def test_hh_endpoint_registered(self) -> None:
        """GET /vacancies/hh/{hh_id} зарегистрирован в роутере."""
        from app.vacancies.router import router

        routes = [r.path for r in router.routes]  # type: ignore[union-attr]
        assert any('/hh/{hh_id}' in r for r in routes)

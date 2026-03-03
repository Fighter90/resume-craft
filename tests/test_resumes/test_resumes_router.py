"""Тесты модуля резюме."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.resumes.models import Resume, ResumeStatus


class TestResumeUpload:
    """Тесты POST /resumes/upload."""

    async def test_upload_without_auth(self, client: AsyncClient) -> None:
        """Без JWT → 401."""
        response = await client.post('/api/v1/resumes/upload')
        assert response.status_code == 401

    async def test_upload_unsupported_format(self, auth_client: AsyncClient) -> None:
        """Неподдерживаемый формат → 400."""
        response = await auth_client.post(
            '/api/v1/resumes/upload',
            files={'file': ('test.txt', b'plain text content', 'text/plain')},
        )
        assert response.status_code == 400

    @patch('app.resumes.service.file_storage')
    async def test_upload_success(
        self, mock_storage: AsyncMock, auth_client: AsyncClient,
    ) -> None:
        """Успешная загрузка PDF → 201."""
        mock_storage.save = AsyncMock(return_value='uploads/resume.pdf')
        content = b'%PDF-1.5 valid pdf content here'
        response = await auth_client.post(
            '/api/v1/resumes/upload',
            files={'file': ('resume.pdf', content, 'application/pdf')},
        )
        assert response.status_code == 201
        data = response.json()
        assert data['file_format'] == 'pdf'
        assert data['status'] == 'draft'


class TestResumeList:
    """Тесты GET /resumes."""

    async def test_list_empty(self, auth_client: AsyncClient) -> None:
        """Пустой список резюме → 200."""
        response = await auth_client.get('/api/v1/resumes')
        assert response.status_code == 200
        data = response.json()
        assert data['total'] >= 0
        assert isinstance(data['items'], list)

    async def test_list_without_auth(self, client: AsyncClient) -> None:
        """Без JWT → 401."""
        response = await client.get('/api/v1/resumes')
        assert response.status_code == 401


class TestResumeGetById:
    """Тесты GET /resumes/{id}."""

    async def test_not_found(self, auth_client: AsyncClient) -> None:
        """Несуществующее резюме → 404."""
        response = await auth_client.get(f'/api/v1/resumes/{uuid4()}')
        assert response.status_code == 404

    async def test_success(
        self, auth_client: AsyncClient, session: AsyncSession, test_user: User,
    ) -> None:
        """Получение резюме → 200."""
        resume = Resume(
            user_id=test_user.id, title='My CV',
            file_path='uploads/cv.pdf', file_format='pdf', file_size_bytes=5000,
            raw_text='My experience', status=ResumeStatus.DRAFT,
        )
        session.add(resume)
        await session.flush()

        response = await auth_client.get(f'/api/v1/resumes/{resume.id}')
        assert response.status_code == 200
        data = response.json()
        assert data['title'] == 'My CV'


class TestResumeDelete:
    """Тесты DELETE /resumes/{id}."""

    async def test_not_found(self, auth_client: AsyncClient) -> None:
        """Несуществующее резюме → 404."""
        response = await auth_client.delete(f'/api/v1/resumes/{uuid4()}')
        assert response.status_code == 404

    @patch('app.resumes.service.file_storage')
    async def test_success(
        self, mock_storage: AsyncMock,
        auth_client: AsyncClient, session: AsyncSession, test_user: User,
    ) -> None:
        """Удаление резюме → 204."""
        mock_storage.delete = AsyncMock()
        resume = Resume(
            user_id=test_user.id, title='To Delete',
            file_path='uploads/del.pdf', file_format='pdf', file_size_bytes=100,
        )
        session.add(resume)
        await session.flush()

        response = await auth_client.delete(f'/api/v1/resumes/{resume.id}')
        assert response.status_code == 204


class TestResumeUpdate:
    """Тесты PUT /resumes/{id}."""

    async def test_not_found(self, auth_client: AsyncClient) -> None:
        """Несуществующее резюме → 404."""
        response = await auth_client.put(
            f'/api/v1/resumes/{uuid4()}',
            json={'title': 'New Title'},
        )
        assert response.status_code == 404

    async def test_update_title(
        self, auth_client: AsyncClient, session: AsyncSession, test_user: User,
    ) -> None:
        """Обновление заголовка → 200."""
        resume = Resume(
            user_id=test_user.id, title='Old Title',
            file_path='uploads/cv.pdf', file_format='pdf', file_size_bytes=3000,
            raw_text='Some text', status=ResumeStatus.DRAFT,
        )
        session.add(resume)
        await session.flush()

        response = await auth_client.put(
            f'/api/v1/resumes/{resume.id}',
            json={'title': 'Updated Title'},
        )
        assert response.status_code == 200
        assert response.json()['title'] == 'Updated Title'

    async def test_update_no_auth(self, client: AsyncClient) -> None:
        """Без JWT → 401."""
        response = await client.put(
            f'/api/v1/resumes/{uuid4()}',
            json={'title': 'Test'},
        )
        assert response.status_code == 401

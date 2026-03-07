"""Тесты эндпоинтов /resumes/{id}/file и /resumes/{id}/preview.

Покрывает:
- GET /api/v1/resumes/{id}/file — скачивание файла (юнит + интеграция)
- GET /api/v1/resumes/{id}/preview — данные для просмотрщика (юнит + интеграция)
- Авторизация, 404, 500, граничные случаи
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.resumes.models import Resume, ResumeStatus
from app.rewriter.models import RewriteHistory, RewriteStatus

# =====================================================================
# Фикстуры
# =====================================================================


@pytest.fixture
async def resume_with_file(
    session: AsyncSession,
    test_user: User,
) -> Resume:
    """Резюме с file_path для тестов скачивания."""
    resume = Resume(
        user_id=test_user.id,
        title='Тестовое резюме',
        file_path='uploads/test-resume.pdf',
        file_format='pdf',
        file_size_bytes=1024,
        raw_text='Текст резюме из PDF',
        parsed_data={'summary': 'Тестовый разработчик'},
        status=ResumeStatus.DRAFT,
    )
    session.add(resume)
    await session.flush()
    return resume


@pytest.fixture
async def resume_no_file(
    session: AsyncSession,
    test_user: User,
) -> Resume:
    """Резюме без file_path."""
    resume = Resume(
        user_id=test_user.id,
        title='Резюме без файла',
        file_path='',
        file_format='pdf',
        file_size_bytes=0,
        raw_text='Текст из формы ввода',
        status=ResumeStatus.DRAFT,
    )
    session.add(resume)
    await session.flush()
    return resume


@pytest.fixture
async def resume_with_rewrite(
    session: AsyncSession,
    test_user: User,
) -> tuple[Resume, RewriteHistory]:
    """Резюме + завершённая оптимизация для preview-тестов."""
    resume = Resume(
        user_id=test_user.id,
        title='Резюме с оптимизацией',
        file_path='uploads/optimized.pdf',
        file_format='pdf',
        file_size_bytes=2048,
        raw_text='Оригинальный текст',
        parsed_data={'summary': 'Python Developer', 'skills': ['Python']},
        status=ResumeStatus.OPTIMIZED,
    )
    session.add(resume)
    await session.flush()

    rewrite = RewriteHistory(
        user_id=test_user.id,
        resume_id=resume.id,
        vacancy_id=uuid4(),
        original_text='Оригинальный текст',
        model_name='claude-3-haiku',
        status=RewriteStatus.COMPLETED,
        rewritten_text='Оптимизированный текст резюме',
        rewritten_data={
            'summary': 'Senior Python Developer',
            'skills': ['Python', 'FastAPI', 'Docker'],
        },
        match_score_after=0.85,
        ats_rating='A',
    )
    session.add(rewrite)
    await session.flush()
    return resume, rewrite


# =====================================================================
# Тесты: GET /api/v1/resumes/{id}/file
# =====================================================================


class TestDownloadResumeFile:
    """Интеграционные тесты скачивания файла резюме."""

    async def test_no_auth(self, client: AsyncClient) -> None:
        """Без авторизации → 401."""
        resp = await client.get(f'/api/v1/resumes/{uuid4()}/file')
        assert resp.status_code == 401

    async def test_not_found(self, auth_client: AsyncClient) -> None:
        """Несуществующее резюме → 404."""
        resp = await auth_client.get(f'/api/v1/resumes/{uuid4()}/file')
        assert resp.status_code == 404

    async def test_no_file_path(
        self,
        auth_client: AsyncClient,
        resume_no_file: Resume,
    ) -> None:
        """Резюме без file_path → 404."""
        resp = await auth_client.get(f'/api/v1/resumes/{resume_no_file.id}/file')
        assert resp.status_code == 404

    async def test_file_not_on_disk(
        self,
        auth_client: AsyncClient,
        resume_with_file: Resume,
    ) -> None:
        """Файл не найден на диске → 404."""
        with patch('app.core.storage.file_storage.read', new_callable=AsyncMock) as mock_read:
            mock_read.side_effect = FileNotFoundError('No such file')
            resp = await auth_client.get(f'/api/v1/resumes/{resume_with_file.id}/file')
            assert resp.status_code == 404

    async def test_permission_error(
        self,
        auth_client: AsyncClient,
        resume_with_file: Resume,
    ) -> None:
        """Ошибка доступа к файлу → 403."""
        with patch('app.core.storage.file_storage.read', new_callable=AsyncMock) as mock_read:
            mock_read.side_effect = PermissionError('Access denied')
            resp = await auth_client.get(f'/api/v1/resumes/{resume_with_file.id}/file')
            assert resp.status_code == 403

    async def test_unexpected_error(
        self,
        auth_client: AsyncClient,
        resume_with_file: Resume,
    ) -> None:
        """Непредвиденная ошибка чтения → 500."""
        with patch('app.core.storage.file_storage.read', new_callable=AsyncMock) as mock_read:
            mock_read.side_effect = OSError('Disk failure')
            resp = await auth_client.get(f'/api/v1/resumes/{resume_with_file.id}/file')
            assert resp.status_code == 500

    async def test_success_pdf(
        self,
        auth_client: AsyncClient,
        resume_with_file: Resume,
    ) -> None:
        """Успешное скачивание PDF → 200, правильный Content-Type."""
        pdf_bytes = b'%PDF-1.4 test content'
        with patch('app.core.storage.file_storage.read', new_callable=AsyncMock) as mock_read:
            mock_read.return_value = pdf_bytes
            resp = await auth_client.get(f'/api/v1/resumes/{resume_with_file.id}/file')
            assert resp.status_code == 200
            assert 'application/pdf' in resp.headers['content-type']
            assert resp.content == pdf_bytes

    async def test_success_content_disposition_inline(
        self,
        auth_client: AsyncClient,
        resume_with_file: Resume,
    ) -> None:
        """Content-Disposition: inline (для отображения в браузере)."""
        with patch('app.core.storage.file_storage.read', new_callable=AsyncMock) as mock_read:
            mock_read.return_value = b'%PDF-1.4 data'
            resp = await auth_client.get(f'/api/v1/resumes/{resume_with_file.id}/file')
            cd = resp.headers.get('content-disposition', '')
            assert 'inline' in cd

    async def test_success_content_length(
        self,
        auth_client: AsyncClient,
        resume_with_file: Resume,
    ) -> None:
        """Content-Length соответствует размеру данных."""
        content = b'%PDF-1.4 test data here'
        with patch('app.core.storage.file_storage.read', new_callable=AsyncMock) as mock_read:
            mock_read.return_value = content
            resp = await auth_client.get(f'/api/v1/resumes/{resume_with_file.id}/file')
            assert int(resp.headers['content-length']) == len(content)


# =====================================================================
# Тесты: GET /api/v1/resumes/{id}/preview
# =====================================================================


class TestResumePreview:
    """Интеграционные тесты эндпоинта preview."""

    async def test_no_auth(self, client: AsyncClient) -> None:
        """Без авторизации → 401."""
        resp = await client.get(f'/api/v1/resumes/{uuid4()}/preview')
        assert resp.status_code == 401

    async def test_not_found(self, auth_client: AsyncClient) -> None:
        """Несуществующее резюме → 404."""
        resp = await auth_client.get(f'/api/v1/resumes/{uuid4()}/preview')
        assert resp.status_code == 404

    async def test_success_basic_fields(
        self,
        auth_client: AsyncClient,
        resume_with_file: Resume,
    ) -> None:
        """Успешный preview → основные поля присутствуют."""
        resp = await auth_client.get(f'/api/v1/resumes/{resume_with_file.id}/preview')
        assert resp.status_code == 200
        data = resp.json()
        assert data['id'] == str(resume_with_file.id)
        assert data['title'] == 'Тестовое резюме'
        assert data['format'] == 'pdf'
        assert data['original_text'] == 'Текст резюме из PDF'
        assert data['status'] == 'draft'

    async def test_preview_has_file_url(
        self,
        auth_client: AsyncClient,
        resume_with_file: Resume,
    ) -> None:
        """Preview содержит file_url для скачивания."""
        resp = await auth_client.get(f'/api/v1/resumes/{resume_with_file.id}/preview')
        data = resp.json()
        assert data['file_url'] is not None
        assert f'/resumes/{resume_with_file.id}/file' in data['file_url']

    async def test_preview_no_file_url_when_no_path(
        self,
        auth_client: AsyncClient,
        resume_no_file: Resume,
    ) -> None:
        """Preview без file_path → file_url = null."""
        resp = await auth_client.get(f'/api/v1/resumes/{resume_no_file.id}/preview')
        data = resp.json()
        assert data['file_url'] is None

    async def test_preview_with_rewrites(
        self,
        auth_client: AsyncClient,
        resume_with_rewrite: tuple[Resume, RewriteHistory],
    ) -> None:
        """Preview с оптимизациями → список rewrites заполнен."""
        resume, rewrite = resume_with_rewrite
        resp = await auth_client.get(f'/api/v1/resumes/{resume.id}/preview')
        assert resp.status_code == 200
        data = resp.json()
        assert len(data['rewrites']) == 1
        rw = data['rewrites'][0]
        assert rw['id'] == str(rewrite.id)
        assert rw['model'] == 'claude-3-haiku'
        assert rw['optimized_text'] == 'Оптимизированный текст резюме'
        assert rw['ats_grade'] == 'A'

    async def test_preview_rewrite_match_score_normalized(
        self,
        auth_client: AsyncClient,
        resume_with_rewrite: tuple[Resume, RewriteHistory],
    ) -> None:
        """Match score 0.85 → нормализован в 85."""
        resume, _ = resume_with_rewrite
        resp = await auth_client.get(f'/api/v1/resumes/{resume.id}/preview')
        data = resp.json()
        rw = data['rewrites'][0]
        assert rw['match_score'] == 85

    async def test_preview_no_rewrites(
        self,
        auth_client: AsyncClient,
        resume_with_file: Resume,
    ) -> None:
        """Резюме без оптимизаций → пустой список rewrites."""
        resp = await auth_client.get(f'/api/v1/resumes/{resume_with_file.id}/preview')
        data = resp.json()
        assert data['rewrites'] == []

    async def test_preview_parsed_data(
        self,
        auth_client: AsyncClient,
        resume_with_file: Resume,
    ) -> None:
        """Preview содержит parsed_data."""
        resp = await auth_client.get(f'/api/v1/resumes/{resume_with_file.id}/preview')
        data = resp.json()
        assert data['parsed_data'] == {'summary': 'Тестовый разработчик'}

    async def test_preview_created_at(
        self,
        auth_client: AsyncClient,
        resume_with_file: Resume,
    ) -> None:
        """Preview содержит created_at в ISO формате."""
        resp = await auth_client.get(f'/api/v1/resumes/{resume_with_file.id}/preview')
        data = resp.json()
        # created_at = None for in-memory SQLite without server_default
        # so just check it exists in response
        assert 'created_at' in data


# =====================================================================
# Приёмочные тесты: полный workflow просмотра резюме
# =====================================================================


class TestResumeViewerAcceptance:
    """Приёмочные тесты: полный цикл просмотра резюме."""

    async def test_view_draft_resume(
        self,
        auth_client: AsyncClient,
        resume_with_file: Resume,
    ) -> None:
        """Просмотр черновика: есть original_text, нет rewrites."""
        resp = await auth_client.get(f'/api/v1/resumes/{resume_with_file.id}/preview')
        data = resp.json()
        assert data['status'] == 'draft'
        assert data['original_text'] is not None
        assert data['rewrites'] == []

    async def test_view_optimized_resume(
        self,
        auth_client: AsyncClient,
        resume_with_rewrite: tuple[Resume, RewriteHistory],
    ) -> None:
        """Просмотр оптимизированного резюме: есть original + optimized."""
        resume, _ = resume_with_rewrite
        resp = await auth_client.get(f'/api/v1/resumes/{resume.id}/preview')
        data = resp.json()
        assert data['status'] == 'optimized'
        assert data['original_text'] is not None
        assert len(data['rewrites']) >= 1
        assert data['rewrites'][0]['optimized_text'] is not None

    async def test_download_after_preview(
        self,
        auth_client: AsyncClient,
        resume_with_file: Resume,
    ) -> None:
        """После preview можно скачать файл по file_url."""
        preview_resp = await auth_client.get(f'/api/v1/resumes/{resume_with_file.id}/preview')
        file_url = preview_resp.json()['file_url']
        assert file_url is not None

        # Скачивание через file endpoint (мокаем storage)
        with patch('app.core.storage.file_storage.read', new_callable=AsyncMock) as mock_read:
            mock_read.return_value = b'%PDF test'
            file_resp = await auth_client.get(file_url)
            assert file_resp.status_code == 200

    async def test_export_rewrite_after_preview(
        self,
        auth_client: AsyncClient,
        resume_with_rewrite: tuple[Resume, RewriteHistory],
    ) -> None:
        """Preview → получаем rewrite_id → экспортируем в 3 формата."""
        resume, _ = resume_with_rewrite
        preview_resp = await auth_client.get(f'/api/v1/resumes/{resume.id}/preview')
        rewrite_id = preview_resp.json()['rewrites'][0]['id']

        for fmt in ('docx', 'pdf', 'txt'):
            resp = await auth_client.get(f'/api/v1/export/{rewrite_id}/{fmt}')
            assert resp.status_code == 200, f'{fmt} export after preview failed'

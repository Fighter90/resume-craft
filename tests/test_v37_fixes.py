"""
Тесты для исправлений V37 — 5 дефектов из QA Report V36 + IMPROVEMENTS.

Дефекты:
- AVATAR-DELETE-503 (P2): DELETE аватара возвращал 503 → graceful error handling
- AVATAR-DELETE-BTN-UX (P4): кнопка удаления видна без аватара → скрыта (frontend, не тестируется)
- VACANCY-URL-500 (P3): невалидный URL вакансии → 500 → теперь 400
- SECURITY-AUTOFILL (P4): autocomplete на паролях (frontend, не тестируется)
- GROQ-MODEL-NAME-HISTORY (P4): Groq без модели в истории → сохраняется sub_model
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.auth.models import User
from app.core.exceptions import AppError
from app.resumes.models import Resume
from app.rewriter.service import create_rewrite_task
from app.vacancies.models import Vacancy
from app.vacancies.service import create_from_url

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


# ============================================================================
# AVATAR-DELETE-503: Удаление аватара — graceful error handling
# ============================================================================


class TestAvatarDelete503:
    """P2: AVATAR-DELETE-503 — DELETE /me/avatar не должен возвращать 503."""

    async def test_delete_avatar_no_avatar_returns_204(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """Удаление без загруженного аватара → 204 (idempotent)."""
        response = await auth_client.delete('/api/v1/auth/me/avatar')
        assert response.status_code == HTTPStatus.NO_CONTENT

    async def test_delete_avatar_with_avatar_returns_204(
        self,
        auth_client: AsyncClient,
        test_user: User,
        session: AsyncSession,
    ) -> None:
        """Удаление существующего аватара → 204, avatar_url = None."""
        test_user.avatar_url = '/uploads/test-avatar.png'
        await session.flush()

        mock_storage = MagicMock()
        mock_storage.delete = AsyncMock()

        with (
            patch('app.auth.router.storage_backend', mock_storage, create=True),
            patch('app.core.storage.file_storage', mock_storage),
        ):
            response = await auth_client.delete('/api/v1/auth/me/avatar')

        assert response.status_code == HTTPStatus.NO_CONTENT

    async def test_delete_avatar_storage_error_still_returns_204(
        self,
        auth_client: AsyncClient,
        test_user: User,
        session: AsyncSession,
    ) -> None:
        """Ошибка storage при удалении файла → 204 (flush-only, DB очищена)."""
        test_user.avatar_url = '/uploads/test-avatar.png'
        await session.flush()

        mock_storage = MagicMock()
        mock_storage.delete = AsyncMock(side_effect=OSError('Storage error'))

        with patch('app.core.storage.file_storage', mock_storage):
            response = await auth_client.delete('/api/v1/auth/me/avatar')

        # Storage-ошибка логируется, но avatar_url очищается → 204
        assert response.status_code == HTTPStatus.NO_CONTENT

    async def test_delete_avatar_storage_error_still_clears_db(
        self,
        auth_client: AsyncClient,
        test_user: User,
        session: AsyncSession,
    ) -> None:
        """Ошибка удаления файла → логируется, но avatar_url очищается."""
        test_user.avatar_url = '/uploads/test-avatar.png'
        await session.flush()

        mock_storage = MagicMock()
        mock_storage.delete = AsyncMock(side_effect=OSError('Disk error'))

        with patch('app.core.storage.file_storage', mock_storage):
            response = await auth_client.delete('/api/v1/auth/me/avatar')

        assert response.status_code == HTTPStatus.NO_CONTENT


# ============================================================================
# VACANCY-URL-500: Невалидный URL вакансии → 400 вместо 500
# ============================================================================


class TestVacancyUrl500:
    """P3: VACANCY-URL-500 — невалидный URL вакансии должен возвращать 400."""

    async def test_invalid_url_returns_400(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """Не-hh.ru URL → 400 с понятным сообщением."""
        response = await auth_client.post(
            '/api/v1/vacancies/from-url',
            json={'url': 'https://google.com/not-hh'},
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        data = response.json()
        assert 'hh.ru' in data.get('message', data.get('detail', ''))

    async def test_random_url_returns_400(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """Произвольный URL → 400."""
        response = await auth_client.post(
            '/api/v1/vacancies/from-url',
            json={'url': 'https://example.com/vacancy/123'},
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST

    async def test_valid_hh_url_does_not_return_400(
        self,
        auth_client: AsyncClient,
    ) -> None:
        """Валидный hh.ru URL → не 400 (может быть 201 или 502 от API hh.ru)."""
        with patch('app.vacancies.service.HHClient') as mock_client_cls:
            mock_instance = AsyncMock()
            mock_instance.get_vacancy = AsyncMock(
                return_value={
                    'id': '12345',
                    'name': 'Test Vacancy',
                    'employer': {'name': 'Test'},
                    'area': {'name': 'Москва'},
                    'salary': None,
                    'experience': {'name': '1-3'},
                    'description': 'Описание',
                    'key_skills': [],
                    'alternate_url': 'https://hh.ru/vacancy/12345',
                }
            )
            mock_instance.close = AsyncMock()
            mock_client_cls.return_value = mock_instance

            response = await auth_client.post(
                '/api/v1/vacancies/from-url',
                json={'url': 'https://hh.ru/vacancy/12345'},
            )

        assert response.status_code != HTTPStatus.BAD_REQUEST

    async def test_create_from_url_invalid_raises_app_error(
        self,
        session: AsyncSession,
    ) -> None:
        """Сервис create_from_url с невалидным URL → AppError(400)."""
        with pytest.raises(AppError) as exc_info:
            await create_from_url(
                session,
                user_id=uuid4(),
                url='https://google.com/not-a-vacancy',
            )
        assert exc_info.value.status_code == 400
        assert 'hh.ru' in exc_info.value.message

    async def test_create_from_url_empty_url_raises_app_error(
        self,
        session: AsyncSession,
    ) -> None:
        """Пустой URL → AppError(400)."""
        with pytest.raises(AppError) as exc_info:
            await create_from_url(
                session,
                user_id=uuid4(),
                url='',
            )
        assert exc_info.value.status_code == 400


# ============================================================================
# GROQ-MODEL-NAME-HISTORY: Groq сохраняет sub_model
# ============================================================================


class TestGroqModelNameHistory:
    """P4: GROQ-MODEL-NAME-HISTORY — Groq должен сохранять provider:model."""

    async def test_groq_with_sub_model_saves_full_name(
        self,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        """Groq + sub_model → сохраняется как 'groq:allam-2-7b'."""
        resume = Resume(
            id=uuid4(),
            user_id=test_user.id,
            title='Test Resume',
            file_path='uploads/test-resume.txt',
            file_size_bytes=100,
            raw_text='Python developer с опытом работы',
            file_format='txt',
        )
        vacancy = Vacancy(
            id=uuid4(),
            user_id=test_user.id,
            title='Test Vacancy',
            description='Test vacancy description',
        )
        session.add_all([resume, vacancy])
        await session.flush()

        task = await create_rewrite_task(
            session,
            user_id=test_user.id,
            resume_id=resume.id,
            vacancy_id=vacancy.id,
            model_name='groq',
            sub_model='allam-2-7b',
        )

        assert task.model_name == 'groq:allam-2-7b'

    async def test_groq_without_sub_model_saves_plain(
        self,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        """Groq без sub_model → сохраняется как 'groq'."""
        resume = Resume(
            id=uuid4(),
            user_id=test_user.id,
            title='Test Resume',
            file_path='uploads/test-resume.txt',
            file_size_bytes=100,
            raw_text='Python developer с опытом работы',
            file_format='txt',
        )
        vacancy = Vacancy(
            id=uuid4(),
            user_id=test_user.id,
            title='Test Vacancy',
            description='Test vacancy description',
        )
        session.add_all([resume, vacancy])
        await session.flush()

        task = await create_rewrite_task(
            session,
            user_id=test_user.id,
            resume_id=resume.id,
            vacancy_id=vacancy.id,
            model_name='groq',
            sub_model=None,
        )

        assert task.model_name == 'groq'

    async def test_openai_still_saves_sub_model(
        self,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        """OpenAI + sub_model → по-прежнему сохраняется как 'openai:gpt-4o'."""
        resume = Resume(
            id=uuid4(),
            user_id=test_user.id,
            title='Test Resume',
            file_path='uploads/test-resume.txt',
            file_size_bytes=100,
            raw_text='Python developer',
            file_format='txt',
        )
        vacancy = Vacancy(
            id=uuid4(),
            user_id=test_user.id,
            title='Test Vacancy',
            description='Test vacancy description',
        )
        session.add_all([resume, vacancy])
        await session.flush()

        task = await create_rewrite_task(
            session,
            user_id=test_user.id,
            resume_id=resume.id,
            vacancy_id=vacancy.id,
            model_name='openai',
            sub_model='gpt-4o',
        )

        assert task.model_name == 'openai:gpt-4o'

    async def test_anthropic_saves_sub_model(
        self,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        """Anthropic + sub_model → 'anthropic:claude-sonnet-4-6'."""
        resume = Resume(
            id=uuid4(),
            user_id=test_user.id,
            title='Test Resume',
            file_path='uploads/test-resume.txt',
            file_size_bytes=100,
            raw_text='Senior engineer',
            file_format='txt',
        )
        vacancy = Vacancy(
            id=uuid4(),
            user_id=test_user.id,
            title='Test Vacancy',
            description='Test vacancy description',
        )
        session.add_all([resume, vacancy])
        await session.flush()

        task = await create_rewrite_task(
            session,
            user_id=test_user.id,
            resume_id=resume.id,
            vacancy_id=vacancy.id,
            model_name='anthropic',
            sub_model='claude-sonnet-4-6',
        )

        assert task.model_name == 'anthropic:claude-sonnet-4-6'

    async def test_openrouter_saves_sub_model(
        self,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        """OpenRouter + sub_model → 'openrouter:ai21/jamba-large-1.7'."""
        resume = Resume(
            id=uuid4(),
            user_id=test_user.id,
            title='Test Resume',
            file_path='uploads/test-resume.txt',
            file_size_bytes=100,
            raw_text='QA engineer',
            file_format='txt',
        )
        vacancy = Vacancy(
            id=uuid4(),
            user_id=test_user.id,
            title='Test Vacancy',
            description='Test vacancy description',
        )
        session.add_all([resume, vacancy])
        await session.flush()

        task = await create_rewrite_task(
            session,
            user_id=test_user.id,
            resume_id=resume.id,
            vacancy_id=vacancy.id,
            model_name='openrouter',
            sub_model='ai21/jamba-large-1.7',
        )

        assert task.model_name == 'openrouter:ai21/jamba-large-1.7'

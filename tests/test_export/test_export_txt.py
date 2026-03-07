"""Тесты экспорта TXT: юнит, функциональные, интеграционные.

Покрывает:
- generate_txt() — юнит-тесты генерации plain-text
- GET /api/v1/export/{task_id}/txt — интеграционные API-тесты
- Граничные случаи: пустые данные, JSON, plain text, UTF-8
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.export.service import generate_txt
from app.rewriter.models import RewriteHistory, RewriteStatus

# =====================================================================
# Юнит-тесты: generate_txt()
# =====================================================================


class TestGenerateTxtUnit:
    """Юнит-тесты для функции generate_txt()."""

    def test_structured_data_full(self) -> None:
        """Генерация из полных структурированных данных → содержит все секции."""
        data = {
            'summary': 'Senior Python Developer с 10-летним опытом',
            'experience': [
                {
                    'position': 'Lead Developer',
                    'company': 'TechCorp',
                    'period': '2020-2024',
                    'achievements': ['Увеличил производительность на 40%', 'Внедрил CI/CD'],
                },
            ],
            'education': [
                {
                    'institution': 'МГУ',
                    'degree': 'Магистр',
                    'specialization': 'Информатика',
                    'year': 2020,
                },
            ],
            'skills': ['Python', 'FastAPI', 'PostgreSQL'],
        }
        result = generate_txt(data)
        assert isinstance(result, bytes)
        text = result.decode('utf-8')

        # Проверяем заголовки секций
        assert 'ПРОФЕССИОНАЛЬНОЕ РЕЗЮМЕ' in text
        assert 'ОПЫТ РАБОТЫ' in text
        assert 'ОБРАЗОВАНИЕ' in text
        assert 'НАВЫКИ' in text

        # Проверяем содержимое
        assert 'Senior Python Developer' in text
        assert 'Lead Developer' in text
        assert 'TechCorp' in text
        assert '2020-2024' in text
        assert 'Увеличил производительность на 40%' in text
        assert 'Внедрил CI/CD' in text
        assert 'МГУ' in text
        assert 'Магистр' in text
        assert 'Python' in text
        assert 'FastAPI' in text

    def test_structured_data_summary_only(self) -> None:
        """Структурированные данные только с summary."""
        data = {'summary': 'Experienced backend developer'}
        result = generate_txt(data)
        text = result.decode('utf-8')
        assert 'ПРОФЕССИОНАЛЬНОЕ РЕЗЮМЕ' in text
        assert 'Experienced backend developer' in text
        assert 'ОПЫТ РАБОТЫ' not in text

    def test_structured_data_skills_only(self) -> None:
        """Только навыки."""
        data = {'skills': ['Go', 'Docker', 'Kubernetes']}
        result = generate_txt(data)
        text = result.decode('utf-8')
        assert 'НАВЫКИ' in text
        assert 'Go' in text
        assert 'Docker' in text

    def test_structured_data_experience_no_achievements(self) -> None:
        """Опыт работы без достижений."""
        data = {
            'experience': [
                {'position': 'Developer', 'company': 'Corp', 'period': '2023'},
            ],
        }
        result = generate_txt(data)
        text = result.decode('utf-8')
        assert 'ОПЫТ РАБОТЫ' in text
        assert 'Developer' in text
        assert 'Corp' in text

    def test_structured_data_education_no_year(self) -> None:
        """Образование без года."""
        data = {
            'education': [
                {'institution': 'МФТИ', 'degree': 'Бакалавр', 'specialization': 'CS'},
            ],
        }
        result = generate_txt(data)
        text = result.decode('utf-8')
        assert 'ОБРАЗОВАНИЕ' in text
        assert 'МФТИ' in text

    def test_plain_text_fallback(self) -> None:
        """Генерация из raw_text (fallback)."""
        result = generate_txt(None, raw_text='Тестовое резюме.\nОпыт работы: 5 лет.')
        text = result.decode('utf-8')
        assert 'Тестовое резюме.' in text
        assert 'Опыт работы: 5 лет.' in text

    def test_empty_data_returns_placeholder(self) -> None:
        """Пустые данные → текст-заглушка."""
        result = generate_txt(None)
        text = result.decode('utf-8')
        assert 'Данные для экспорта отсутствуют' in text

    def test_returns_bytes(self) -> None:
        """Результат всегда bytes."""
        result = generate_txt(None, raw_text='test')
        assert isinstance(result, bytes)

    def test_utf8_encoding(self) -> None:
        """Корректная UTF-8 кодировка для русского текста."""
        data = {'summary': 'Опытный разработчик — 10+ лет'}
        result = generate_txt(data)
        text = result.decode('utf-8')
        assert 'Опытный разработчик — 10+ лет' in text

    def test_separators_present(self) -> None:
        """Разделители секций (= и -) присутствуют."""
        data = {
            'summary': 'Dev',
            'experience': [{'position': 'Dev', 'company': 'Corp', 'period': '2023'}],
        }
        result = generate_txt(data)
        text = result.decode('utf-8')
        assert '=' * 40 in text
        assert '-' * 40 in text

    def test_multiple_experience_entries(self) -> None:
        """Несколько записей в опыте работы."""
        data = {
            'experience': [
                {'position': 'Senior Dev', 'company': 'A', 'period': '2022-2024'},
                {'position': 'Junior Dev', 'company': 'B', 'period': '2020-2022'},
            ],
        }
        result = generate_txt(data)
        text = result.decode('utf-8')
        assert 'Senior Dev' in text
        assert 'Junior Dev' in text
        assert 'A' in text
        assert 'B' in text

    def test_bullet_points_in_achievements(self) -> None:
        """Достижения форматируются с маркерами •."""
        data = {
            'experience': [
                {
                    'position': 'Dev',
                    'company': 'Corp',
                    'period': '2023',
                    'achievements': ['First achievement', 'Second achievement'],
                },
            ],
        }
        result = generate_txt(data)
        text = result.decode('utf-8')
        assert '• First achievement' in text
        assert '• Second achievement' in text

    def test_empty_experience_list(self) -> None:
        """Пустой список опыта → секция не отображается."""
        data = {'experience': [], 'skills': ['Python']}
        result = generate_txt(data)
        text = result.decode('utf-8')
        assert 'ОПЫТ РАБОТЫ' not in text
        assert 'НАВЫКИ' in text

    def test_empty_skills_list(self) -> None:
        """Пустой список навыков → секция не отображается."""
        data = {'skills': [], 'summary': 'Dev'}
        result = generate_txt(data)
        text = result.decode('utf-8')
        assert 'НАВЫКИ' not in text

    def test_empty_education_list(self) -> None:
        """Пустой список образования → секция не отображается."""
        data = {'education': [], 'summary': 'Dev'}
        result = generate_txt(data)
        text = result.decode('utf-8')
        assert 'ОБРАЗОВАНИЕ' not in text


# =====================================================================
# Интеграционные тесты: GET /api/v1/export/{task_id}/txt
# =====================================================================


class TestExportTxtRouter:
    """Интеграционные тесты API экспорта TXT."""

    async def test_no_auth(self, client: AsyncClient) -> None:
        """Запрос без авторизации → 401."""
        resp = await client.get(f'/api/v1/export/{uuid4()}/txt')
        assert resp.status_code == 401

    async def test_not_found(self, auth_client: AsyncClient) -> None:
        """Несуществующий task_id → 404."""
        resp = await auth_client.get(f'/api/v1/export/{uuid4()}/txt')
        assert resp.status_code == 404

    async def test_success_with_plain_text(
        self,
        auth_client: AsyncClient,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        """Экспорт с plain text → TXT файл, Content-Type: text/plain."""
        task = RewriteHistory(
            user_id=test_user.id,
            resume_id=uuid4(),
            vacancy_id=uuid4(),
            original_text='Original resume',
            model_name='gigachat-pro',
            status=RewriteStatus.COMPLETED,
            rewritten_text='Оптимизированное резюме.\nОпыт работы: 10 лет.',
        )
        session.add(task)
        await session.flush()

        resp = await auth_client.get(f'/api/v1/export/{task.id}/txt')
        assert resp.status_code == 200
        assert 'text/plain' in resp.headers['content-type']
        text = resp.content.decode('utf-8')
        assert 'Оптимизированное резюме' in text

    async def test_success_with_structured_data(
        self,
        auth_client: AsyncClient,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        """Экспорт со структурированными данными → TXT с секциями."""
        task = RewriteHistory(
            user_id=test_user.id,
            resume_id=uuid4(),
            vacancy_id=uuid4(),
            original_text='Original resume',
            model_name='gigachat-pro',
            status=RewriteStatus.COMPLETED,
            rewritten_text='Optimized text fallback',
            rewritten_data={
                'summary': 'Senior Developer',
                'skills': ['Python', 'Docker'],
            },
        )
        session.add(task)
        await session.flush()

        resp = await auth_client.get(f'/api/v1/export/{task.id}/txt')
        assert resp.status_code == 200
        text = resp.content.decode('utf-8')
        assert 'Senior Developer' in text
        assert 'НАВЫКИ' in text

    async def test_content_disposition_header(
        self,
        auth_client: AsyncClient,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        """Заголовок Content-Disposition содержит filename .txt."""
        task = RewriteHistory(
            user_id=test_user.id,
            resume_id=uuid4(),
            vacancy_id=uuid4(),
            original_text='test',
            model_name='test-model',
            status=RewriteStatus.COMPLETED,
            rewritten_text='Result text',
        )
        session.add(task)
        await session.flush()

        resp = await auth_client.get(f'/api/v1/export/{task.id}/txt')
        assert resp.status_code == 200
        cd = resp.headers.get('content-disposition', '')
        assert '.txt' in cd

    async def test_no_data_to_export(
        self,
        auth_client: AsyncClient,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        """Задача без rewritten_text и rewritten_data → 404."""
        task = RewriteHistory(
            user_id=test_user.id,
            resume_id=uuid4(),
            vacancy_id=uuid4(),
            original_text='original',
            model_name='gigachat-pro',
            status=RewriteStatus.PENDING,
        )
        session.add(task)
        await session.flush()

        resp = await auth_client.get(f'/api/v1/export/{task.id}/txt')
        assert resp.status_code == 404

    async def test_content_length_header(
        self,
        auth_client: AsyncClient,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        """Заголовок Content-Length присутствует и > 0."""
        task = RewriteHistory(
            user_id=test_user.id,
            resume_id=uuid4(),
            vacancy_id=uuid4(),
            original_text='test',
            model_name='test-model',
            status=RewriteStatus.COMPLETED,
            rewritten_text='Some text content',
        )
        session.add(task)
        await session.flush()

        resp = await auth_client.get(f'/api/v1/export/{task.id}/txt')
        assert resp.status_code == 200
        length = int(resp.headers.get('content-length', '0'))
        assert length > 0


# =====================================================================
# Приёмочные тесты: TXT vs DOCX vs PDF — кросс-формат
# =====================================================================


class TestExportCrossFormat:
    """Приёмочные тесты: одни и те же данные → все 3 формата."""

    @pytest.fixture
    async def completed_task(
        self,
        session: AsyncSession,
        test_user: User,
    ) -> RewriteHistory:
        """Задача с полными данными для экспорта."""
        task = RewriteHistory(
            user_id=test_user.id,
            resume_id=uuid4(),
            vacancy_id=uuid4(),
            original_text='Original text',
            model_name='test-model',
            status=RewriteStatus.COMPLETED,
            rewritten_text='Optimized resume text',
            rewritten_data={
                'summary': 'Full stack developer',
                'experience': [
                    {
                        'position': 'Dev',
                        'company': 'Corp',
                        'period': '2023',
                        'achievements': ['Built API'],
                    },
                ],
                'skills': ['Python', 'TypeScript'],
            },
        )
        session.add(task)
        await session.flush()
        return task

    async def test_all_three_formats_succeed(
        self,
        auth_client: AsyncClient,
        completed_task: RewriteHistory,
    ) -> None:
        """Все 3 формата возвращают 200 для одной задачи."""
        for fmt in ('docx', 'pdf', 'txt'):
            resp = await auth_client.get(f'/api/v1/export/{completed_task.id}/{fmt}')
            assert resp.status_code == 200, f'Format {fmt} failed: {resp.status_code}'

    async def test_docx_magic_bytes(
        self,
        auth_client: AsyncClient,
        completed_task: RewriteHistory,
    ) -> None:
        """DOCX начинается с PK (ZIP)."""
        resp = await auth_client.get(f'/api/v1/export/{completed_task.id}/docx')
        assert resp.content[:2] == b'PK'

    async def test_pdf_magic_bytes(
        self,
        auth_client: AsyncClient,
        completed_task: RewriteHistory,
    ) -> None:
        """PDF начинается с %PDF."""
        resp = await auth_client.get(f'/api/v1/export/{completed_task.id}/pdf')
        assert resp.content[:4] == b'%PDF'

    async def test_txt_is_valid_utf8(
        self,
        auth_client: AsyncClient,
        completed_task: RewriteHistory,
    ) -> None:
        """TXT содержит валидный UTF-8 текст."""
        resp = await auth_client.get(f'/api/v1/export/{completed_task.id}/txt')
        text = resp.content.decode('utf-8')
        assert 'Full stack developer' in text

    async def test_different_content_types(
        self,
        auth_client: AsyncClient,
        completed_task: RewriteHistory,
    ) -> None:
        """Каждый формат возвращает свой Content-Type."""
        expected = {
            'docx': 'application/vnd.openxmlformats',
            'pdf': 'application/pdf',
            'txt': 'text/plain',
        }
        for fmt, ct_prefix in expected.items():
            resp = await auth_client.get(f'/api/v1/export/{completed_task.id}/{fmt}')
            assert ct_prefix in resp.headers['content-type'], (
                f'Format {fmt}: expected {ct_prefix}, got {resp.headers["content-type"]}'
            )

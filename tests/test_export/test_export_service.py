"""Тесты export/service.py — генерация DOCX."""

from __future__ import annotations

from app.export.service import generate_docx


class TestGenerateDocx:
    """Тесты generate_docx()."""

    def test_structured_data(self) -> None:
        """Генерация из структурированных JSON-данных."""
        data = {
            'summary': 'Senior Python Developer',
            'experience': [
                {
                    'position': 'Lead Developer',
                    'company': 'TechCorp',
                    'period': '2020-2024',
                    'achievements': ['Увеличил производительность на 40%'],
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
        result = generate_docx(data)
        assert isinstance(result, bytes)
        assert len(result) > 0
        # DOCX = ZIP (PK magic bytes)
        assert result[:2] == b'PK'

    def test_plain_text_fallback(self) -> None:
        """Генерация из plain text."""
        result = generate_docx(None, raw_text='Тестовое резюме.\nОпыт работы.')
        assert isinstance(result, bytes)
        assert result[:2] == b'PK'

    def test_empty_data(self) -> None:
        """Пустые данные → DOCX с сообщением."""
        result = generate_docx(None)
        assert isinstance(result, bytes)
        assert result[:2] == b'PK'

    def test_experience_without_achievements(self) -> None:
        """Опыт без достижений."""
        data = {
            'experience': [
                {'position': 'Dev', 'company': 'Corp', 'period': '2023'},
            ],
        }
        result = generate_docx(data)
        assert isinstance(result, bytes)

    def test_education_without_year(self) -> None:
        """Образование без года."""
        data = {
            'education': [
                {'institution': 'МФТИ', 'degree': 'Бакалавр', 'specialization': 'CS'},
            ],
        }
        result = generate_docx(data)
        assert isinstance(result, bytes)

    def test_skills_only(self) -> None:
        """Только навыки."""
        data = {'skills': ['Python', 'Docker', 'K8s']}
        result = generate_docx(data)
        assert isinstance(result, bytes)

    def test_summary_only(self) -> None:
        """Только саммари."""
        data = {'summary': 'Experienced developer'}
        result = generate_docx(data)
        assert isinstance(result, bytes)

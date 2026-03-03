"""Дополнительные тесты для покрытия edge-cases.

resumes/service, vacancies/service, scoring, export.
"""

from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

from app.export.service import generate_docx
from app.ml.scoring import _keywords_score, _readability_score, calculate_match_score
from app.resumes.models import Resume
from app.resumes.service import _try_generate_embedding
from app.vacancies.models import Vacancy
from app.vacancies.service import _try_generate_vacancy_embedding


class TestTryGenerateEmbedding:
    """Тесты _try_generate_embedding() для resumes/service.py."""

    def test_empty_raw_text(self) -> None:
        """Пустой raw_text → возврат без действий."""
        resume = Resume(
            id=uuid4(),
            user_id=uuid4(),
            file_path='/test.pdf',
            file_format='pdf',
            file_size_bytes=100,
            raw_text='',
        )
        _try_generate_embedding(resume)
        assert resume.parsed_data is None

    def test_none_raw_text(self) -> None:
        """None raw_text → возврат без действий."""
        resume = Resume(
            id=uuid4(),
            user_id=uuid4(),
            file_path='/test.pdf',
            file_format='pdf',
            file_size_bytes=100,
            raw_text=None,
        )
        _try_generate_embedding(resume)

    def test_embedding_generation_success(self) -> None:
        """Успешная генерация эмбеддинга."""
        resume = Resume(
            id=uuid4(),
            user_id=uuid4(),
            file_path='/test.pdf',
            file_format='pdf',
            file_size_bytes=100,
            raw_text='Python разработчик с опытом',
        )
        with patch('app.ml.embeddings.generate_embedding', return_value=[0.1] * 1536):
            _try_generate_embedding(resume)

        assert resume.parsed_data is not None
        assert resume.parsed_data.get('_embedding_generated') is True

    def test_embedding_generation_error(self) -> None:
        """Ошибка генерации → логируется, без исключения."""
        resume = Resume(
            id=uuid4(),
            user_id=uuid4(),
            file_path='/test.pdf',
            file_format='pdf',
            file_size_bytes=100,
            raw_text='Python разработчик',
        )
        with patch(
            'app.ml.embeddings.generate_embedding',
            side_effect=RuntimeError('Model not available'),
        ):
            # Не должно бросить исключение
            _try_generate_embedding(resume)


class TestTryGenerateVacancyEmbedding:
    """Тесты _try_generate_vacancy_embedding() для vacancies/service.py."""

    def test_empty_description(self) -> None:
        """Пустое description → возврат без действий."""
        vacancy = Vacancy(
            id=uuid4(),
            user_id=uuid4(),
            title='Python Dev',
            description='',
        )
        _try_generate_vacancy_embedding(vacancy)

    def test_none_description(self) -> None:
        """None description → возврат без действий."""
        vacancy = Vacancy(
            id=uuid4(),
            user_id=uuid4(),
            title='Python Dev',
            description=None,
        )
        _try_generate_vacancy_embedding(vacancy)

    def test_embedding_error(self) -> None:
        """Ошибка генерации → логируется, без исключения."""
        vacancy = Vacancy(
            id=uuid4(),
            user_id=uuid4(),
            title='Python Dev',
            description='Нужен Python разработчик',
        )
        with patch(
            'app.ml.embeddings.generate_embedding',
            side_effect=RuntimeError('Model not available'),
        ):
            _try_generate_vacancy_embedding(vacancy)


class TestKeywordsScoreStopWords:
    """Тесты _keywords_score() — edge-cases."""

    def test_vacancy_only_stop_words(self) -> None:
        """Вакансия из стоп-слов → 0.5 (fallback)."""
        score = _keywords_score('python разработчик', 'и в на с по')
        assert score == 0.5

    def test_resume_only_stop_words(self) -> None:
        """Резюме из стоп-слов → 0."""
        score = _keywords_score('и в на', 'python developer')
        assert score == 0.0


class TestReadabilityScoreEdgeCases:
    """Тесты _readability_score() — edge-cases."""

    def test_duplicate_sentences(self) -> None:
        """Повторяющиеся предложения → нет бонуса за уникальность."""
        text = 'Работал программистом. ' * 20
        score = _readability_score(text)
        # Повторы снижают uniqueness ratio, бонус 0.2 не даётся
        assert score < 0.5

    def test_unique_sentences_bonus(self) -> None:
        """Текст с >3 уникальных предложений (>80%) → бонус +0.2."""
        text = (
            'Реализовал микросервисную архитектуру. '
            'Разработал REST API на FastAPI. '
            'Внедрил CI/CD пайплайн. '
            'Оптимизировал запросы к базе данных. '
            'Увеличил производительность на 40%. '
        )
        score = _readability_score(text)
        # Все предложения уникальны (100% > 80%) → бонус 0.2 выдан
        assert score >= 0.2

    def test_medium_word_count_bonus(self) -> None:
        """Текст 200-499 слов → частичный бонус +0.1 за длину."""
        # ~300 слов: попадаем в elif 200 <= word_count <= 3000
        words = ' '.join(['слово'] * 300)
        text = f'Реализовал систему. Разработал API. {words}'
        score = _readability_score(text)
        assert score >= 0.1

    def test_medium_metrics(self) -> None:
        """Текст с 1-2 метриками → частичный бонус."""
        text = 'Увеличил производительность на 40%. Работал в команде.'
        score = _readability_score(text)
        assert score >= 0.1

    def test_medium_verb_count(self) -> None:
        """Текст с 2-4 глаголами действия → частичный бонус."""
        text = (
            'Реализовал систему. Разработал API. '
            'Работал с базой данных. Просто текст для объема. ' * 50
        )
        score = _readability_score(text)
        assert score > 0.0

    def test_short_text(self) -> None:
        """Очень короткий текст → нет бонуса за длину."""
        score = _readability_score('Программист')
        assert score < 0.3


class TestMatchScoreEdgeCases:
    """Дополнительные edge-cases для calculate_match_score."""

    def test_both_empty(self) -> None:
        """Оба пустые → 0."""
        score = calculate_match_score(resume_text='', vacancy_text='')
        assert score == 0.0

    def test_very_long_texts(self) -> None:
        """Длинные тексты → score в диапазоне [0, 1]."""
        resume = 'Python FastAPI PostgreSQL Docker Redis ' * 200
        vacancy = 'Python FastAPI PostgreSQL ' * 100
        score = calculate_match_score(resume_text=resume, vacancy_text=vacancy)
        assert 0.0 <= score <= 1.0


class TestExportDocxEdgeCases:
    """Дополнительные edge-cases для export/service.py."""

    def test_experience_period_only(self) -> None:
        """Опыт с period но без company → period отображается."""
        data = {
            'experience': [
                {'position': 'Developer', 'period': '2020-2024'},
            ],
        }
        result = generate_docx(data)
        assert isinstance(result, bytes)
        assert result[:2] == b'PK'

    def test_experience_company_and_period(self) -> None:
        """Опыт с company и period → оба отображаются."""
        data = {
            'experience': [
                {
                    'position': 'Dev',
                    'company': 'BigCorp',
                    'period': '2020-2024',
                    'achievements': ['Did things', 'Made stuff'],
                },
            ],
        }
        result = generate_docx(data)
        assert isinstance(result, bytes)

    def test_experience_no_company_no_period(self) -> None:
        """Опыт без company и period → только позиция."""
        data = {
            'experience': [
                {'position': 'Freelance Developer'},
            ],
        }
        result = generate_docx(data)
        assert isinstance(result, bytes)

    def test_education_full(self) -> None:
        """Полное образование с годом."""
        data = {
            'education': [
                {
                    'institution': 'МФТИ',
                    'degree': 'Магистр',
                    'specialization': 'Прикладная математика',
                    'year': 2022,
                },
            ],
        }
        result = generate_docx(data)
        assert isinstance(result, bytes)

    def test_empty_lists(self) -> None:
        """Пустые списки → DOCX генерируется."""
        data = {
            'summary': '',
            'experience': [],
            'education': [],
            'skills': [],
        }
        result = generate_docx(data)
        assert isinstance(result, bytes)

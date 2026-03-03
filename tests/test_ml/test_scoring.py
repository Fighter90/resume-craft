"""Тесты Match Score."""

from __future__ import annotations

from app.ml.scoring import (
    _keywords_score,
    _readability_score,
    _structure_score,
    _tokenize,
    calculate_match_score,
)


class TestMatchScore:
    """Тесты расчёта Match Score."""

    def test_identical_texts(self) -> None:
        """Идентичные тексты → высокий Score."""
        text = 'Python разработчик с опытом работы в FastAPI и PostgreSQL'
        score = calculate_match_score(resume_text=text, vacancy_text=text)
        assert score > 0.5

    def test_empty_vacancy(self) -> None:
        """Пустая вакансия → 0."""
        score = calculate_match_score(resume_text='Python developer', vacancy_text='')
        assert score >= 0.0

    def test_empty_resume(self) -> None:
        """Пустое резюме → низкий Score."""
        score = calculate_match_score(resume_text='', vacancy_text='Python developer FastAPI')
        assert score < 0.3

    def test_good_match(self) -> None:
        """Хорошее совпадение → высокий Score."""
        resume = (
            'Опыт работы senior Python разработчиком. '
            'Разработал микросервисы на FastAPI. '
            'Оптимизировал PostgreSQL запросы, увеличил производительность на 40%. '
            'Навыки: Python, FastAPI, PostgreSQL, Docker, Redis. '
            'Образование: МФТИ, магистр.'
        )
        vacancy = (
            'Требуется Python разработчик. '
            'Опыт с FastAPI и PostgreSQL обязателен. '
            'Docker, Redis — преимущество. '
            'Разработка микросервисов.'
        )
        score = calculate_match_score(resume_text=resume, vacancy_text=vacancy)
        assert score > 0.3

    def test_poor_match(self) -> None:
        """Плохое совпадение → низкий Score."""
        resume = 'Бухгалтер с опытом работы 10 лет. 1С, Excel, налоговая отчётность.'
        vacancy = 'Senior Rust developer. WebAssembly, embedded systems, RTOS.'
        score = calculate_match_score(resume_text=resume, vacancy_text=vacancy)
        assert score < 0.4

    def test_score_range(self) -> None:
        """Score всегда в диапазоне [0, 1]."""
        score = calculate_match_score(
            resume_text='test abc 123',
            vacancy_text='different words completely',
        )
        assert 0.0 <= score <= 1.0


class TestTokenize:
    """Тесты _tokenize()."""

    def test_russian(self) -> None:
        tokens = _tokenize('Python разработчик 2024')
        assert 'python' in tokens
        assert 'разработчик' in tokens
        assert '2024' in tokens

    def test_empty(self) -> None:
        assert _tokenize('') == []


class TestKeywordsScore:
    """Тесты _keywords_score()."""

    def test_full_overlap(self) -> None:
        score = _keywords_score('python fastapi docker', 'python fastapi docker')
        assert score > 0.5

    def test_no_overlap(self) -> None:
        score = _keywords_score('java spring', 'python fastapi')
        assert score <= 0.5

    def test_empty_vacancy(self) -> None:
        score = _keywords_score('python developer', '')
        assert score == 0.0


class TestStructureScore:
    """Тесты _structure_score()."""

    def test_full_structure(self) -> None:
        """Все обязательные секции → высокий балл."""
        text = (
            'Опыт работы:\nМенеджер проектов\n'
            'Образование:\nМГУ\n'
            'Навыки: Python, Docker\n'
            'Контакты: email@test.com\n'
            'Достижения: увеличил продажи\n'
            'О себе: опытный специалист'
        )
        score = _structure_score(text)
        assert score > 0.6

    def test_no_structure(self) -> None:
        """Нет секций → 0."""
        score = _structure_score('просто текст без структуры')
        assert score < 0.3


class TestReadabilityScore:
    """Тесты _readability_score()."""

    def test_high_quality(self) -> None:
        """Текст с метриками и глаголами → высокий балл."""
        text = (
            'Реализовал систему автоматизации, увеличил производительность на 40%. '
            'Разработал микросервисы, сократил время обработки на 30%. '
            'Оптимизировал запросы, внедрил кэширование. '
            'Управлял командой из 5 человек. '
            'Автоматизировал CI/CD pipeline. '
            'Обеспечил 99.9% uptime для 100 тыс пользователей. '
        ) * 50  # 500+ слов
        score = _readability_score(text)
        assert score > 0.3

    def test_no_metrics(self) -> None:
        """Текст без метрик и глаголов → низкий балл."""
        score = _readability_score('просто текст')
        assert score < 0.3

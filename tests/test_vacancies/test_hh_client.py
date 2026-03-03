"""Тесты hh.ru клиента."""

from __future__ import annotations

import pytest

from app.vacancies.hh_client import extract_hh_vacancy_id


class TestExtractHHVacancyId:
    """Тесты извлечения ID вакансии из URL."""

    def test_standard_url(self) -> None:
        """Стандартный URL hh.ru."""
        url = 'https://hh.ru/vacancy/12345678'
        assert extract_hh_vacancy_id(url) == '12345678'

    def test_api_url(self) -> None:
        """API URL."""
        url = 'https://api.hh.ru/vacancies/87654321'
        assert extract_hh_vacancy_id(url) == '87654321'

    def test_url_with_params(self) -> None:
        """URL с query-параметрами."""
        url = 'https://hh.ru/vacancy/12345678?from=suggest'
        assert extract_hh_vacancy_id(url) == '12345678'

    def test_invalid_url(self) -> None:
        """Невалидный URL → ValueError."""
        with pytest.raises(ValueError, match='Невалидный URL'):
            extract_hh_vacancy_id('https://google.com/search?q=test')

    def test_empty_url(self) -> None:
        """Пустой URL → ValueError."""
        with pytest.raises(ValueError, match='Невалидный URL'):
            extract_hh_vacancy_id('')

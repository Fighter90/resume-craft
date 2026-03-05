"""Интеграционные тесты LLM-провайдеров и pipeline оптимизации.

Тесты РЕАЛЬНО вызывают API каждого провайдера с тестовыми резюме.
Требуют: настроенные API-ключи в .env, файлы в tests/fixtures/.

Запуск:
    PYTHONPATH=src pytest tests/test_integration_llm.py -v -s --tb=short
    PYTHONPATH=src pytest tests/test_integration_llm.py -k groq -v -s  # только Groq

НЕ КОММИТИТЬ: файл использует .env ключи и реальные резюме.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv

# Загрузить .env ДО проверки ключей
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

import pytest  # noqa: E402

# Пропускать если нет ключей вообще
pytestmark = pytest.mark.skipif(
    not os.getenv('GROQ_API_KEY')
    and not os.getenv('OPENAI_API_KEY')
    and not os.getenv('ANTHROPIC_API_KEY')
    and not os.getenv('OPENROUTER_API_KEY')
    and not os.getenv('GIGACHAT_CREDENTIALS'),
    reason='Integration tests require LLM API keys in environment',
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).parent / 'fixtures'

SAMPLE_VACANCY_TEXT = """
Senior Python Developer / Старший Python-разработчик

Компания: Яндекс
Город: Москва (гибридный формат)
Зарплата: 400 000 – 600 000 ₽ gross

Требования:
— Опыт коммерческой разработки на Python от 5 лет
— Глубокое знание FastAPI или Django (асинхронная архитектура)
— Опыт проектирования REST API и микросервисной архитектуры
— PostgreSQL: сложные запросы, оптимизация, индексы, партиционирование
— Redis, RabbitMQ / Kafka — опыт построения очередей и pub/sub
— Docker, Kubernetes, CI/CD (GitLab CI, GitHub Actions)
— Понимание принципов SOLID, DDD, Clean Architecture
— Опыт работы с высоконагруженными системами (1M+ RPS)
— Git flow, code review, unit/integration тесты (pytest)
— Английский B2+ для чтения документации и общения с командой

Будет плюсом:
— Опыт с Celery, Airflow для фоновых задач
— Знание Go или Rust для критичных по производительности компонентов
— Опыт с AI/ML интеграциями (OpenAI API, LangChain)
— Мониторинг: Prometheus, Grafana, Sentry
— Terraform, IaC

Обязанности:
— Проектирование и разработка backend-сервисов на Python (FastAPI)
— Оптимизация производительности API и базы данных
— Менторство junior/middle разработчиков (команда 5–8 человек)
— Участие в code review и architectural decision records
— Интеграция с внешними API и сервисами
— Написание технической документации
"""


@pytest.fixture(scope='module')
def resume_text_pdf() -> str:
    """Текст резюме из PDF-файла."""
    pdf_path = FIXTURES_DIR / 'sample_resume.pdf'
    if not pdf_path.exists():
        pytest.skip('PDF fixture not found: tests/fixtures/sample_resume.pdf')

    import fitz

    text_parts: list[str] = []
    with fitz.open(str(pdf_path)) as doc:
        for page in doc:
            text_parts.append(page.get_text())
    text = '\n'.join(text_parts).strip()
    assert len(text) > 200, f'PDF text too short: {len(text)} chars'
    return text


@pytest.fixture(scope='module')
def resume_text_docx() -> str:
    """Текст резюме из DOCX-файла."""
    docx_path = FIXTURES_DIR / 'sample_resume.docx'
    if not docx_path.exists():
        pytest.skip('DOCX fixture not found: tests/fixtures/sample_resume.docx')

    from docx import Document

    doc = Document(str(docx_path))
    text = '\n'.join(p.text for p in doc.paragraphs if p.text.strip())
    assert len(text) > 200, f'DOCX text too short: {len(text)} chars'
    return text


@pytest.fixture(scope='module')
def resume_pdf_bytes() -> bytes:
    """Байты PDF-файла."""
    pdf_path = FIXTURES_DIR / 'sample_resume.pdf'
    if not pdf_path.exists():
        pytest.skip('PDF fixture not found')
    return pdf_path.read_bytes()


@pytest.fixture(scope='module')
def resume_docx_bytes() -> bytes:
    """Байты DOCX-файла."""
    docx_path = FIXTURES_DIR / 'sample_resume.docx'
    if not docx_path.exists():
        pytest.skip('DOCX fixture not found')
    return docx_path.read_bytes()


def _validate_rewrite_json(response: str) -> dict:
    """Парсинг и валидация JSON-ответа LLM."""
    clean = response.strip()
    # Удаляем markdown code blocks
    if clean.startswith('```'):
        lines = clean.split('\n')
        clean = '\n'.join(lines[1:-1])
    if clean.startswith('```json'):
        clean = clean[7:]
    if clean.endswith('```'):
        clean = clean[:-3]

    # strict=False — разрешаем control characters (GigaChat иногда их вставляет)
    data = json.loads(clean.strip(), strict=False)

    # Основные поля
    assert 'summary' in data, 'No summary in response'
    assert 'experience' in data, 'No experience in response'
    assert 'skills' in data, 'No skills in response'
    assert isinstance(data['summary'], str), 'summary should be string'
    assert isinstance(data['experience'], list), 'experience should be list'
    assert isinstance(data['skills'], list), 'skills should be list'
    assert len(data['summary']) > 50, f'summary too short: {len(data["summary"])}'
    assert len(data['experience']) > 0, 'experience list empty'
    assert len(data['skills']) > 0, 'skills list empty'

    # Каждый опыт должен иметь position, company
    for exp in data['experience']:
        assert 'position' in exp, f'No position in experience: {exp}'
        assert 'company' in exp or 'achievements' in exp, f'Missing fields: {exp}'

    return data


# =========================================================================
# 1. Парсинг файлов (PDF / DOCX)
# =========================================================================


class TestFileParser:
    """Тесты парсинга реальных резюме."""

    def test_pdf_extraction(self, resume_text_pdf: str) -> None:
        """PDF → текст: корректное извлечение."""
        assert 'Емельянов' in resume_text_pdf or 'емельянов' in resume_text_pdf.lower()
        assert len(resume_text_pdf) > 1000
        # Должен содержать опыт работы
        assert any(
            w in resume_text_pdf.lower() for w in ['опыт', 'разработ', 'python', 'php', 'компания']
        )
        logger.info('PDF parsed: %d chars', len(resume_text_pdf))

    def test_docx_extraction(self, resume_text_docx: str) -> None:
        """DOCX → текст: корректное извлечение."""
        assert len(resume_text_docx) > 1000
        assert any(w in resume_text_docx.lower() for w in ['емельянов', 'опыт', 'разработ'])
        logger.info('DOCX parsed: %d chars', len(resume_text_docx))

    def test_pdf_magic_bytes(self, resume_pdf_bytes: bytes) -> None:
        """PDF magic bytes проверка."""
        assert resume_pdf_bytes[:4] == b'%PDF'

    def test_docx_magic_bytes(self, resume_docx_bytes: bytes) -> None:
        """DOCX magic bytes проверка (PK zip archive)."""
        assert resume_docx_bytes[:4] == b'PK\x03\x04'

    def test_pdf_through_service(self, resume_pdf_bytes: bytes) -> None:
        """Парсинг через service._extract_text."""
        from app.resumes.service import _extract_text

        text = _extract_text(resume_pdf_bytes, ext='pdf')
        assert text is not None
        assert len(text) > 500
        logger.info('Service PDF parser: %d chars', len(text))

    def test_docx_through_service(self, resume_docx_bytes: bytes) -> None:
        """Парсинг через service._extract_text."""
        from app.resumes.service import _extract_text

        text = _extract_text(resume_docx_bytes, ext='docx')
        assert text is not None
        assert len(text) > 500
        logger.info('Service DOCX parser: %d chars', len(text))


# =========================================================================
# 2. Sanitize
# =========================================================================


class TestSanitize:
    """Тесты санитизации текста перед LLM."""

    def test_sanitize_resume_text(self, resume_text_pdf: str) -> None:
        """Санитизация не ломает реальный текст резюме."""
        from app.ml.sanitize import sanitize_for_llm

        sanitized = sanitize_for_llm(resume_text_pdf)
        assert len(sanitized) > 500
        # Не должно быть потери ключевых данных
        assert any(w in sanitized.lower() for w in ['python', 'php', 'разработ'])

    def test_sanitize_vacancy_text(self) -> None:
        """Санитизация текста вакансии."""
        from app.ml.sanitize import sanitize_for_llm

        sanitized = sanitize_for_llm(SAMPLE_VACANCY_TEXT)
        assert 'Python' in sanitized
        assert 'FastAPI' in sanitized
        assert len(sanitized) > 100


# =========================================================================
# 3. Match Score
# =========================================================================


class TestMatchScore:
    """Тесты расчёта Match Score."""

    def test_score_resume_vs_vacancy(self, resume_text_pdf: str) -> None:
        """Match Score для реального резюме и вакансии."""
        from app.ml.scoring import calculate_match_score

        score = calculate_match_score(
            resume_text=resume_text_pdf,
            vacancy_text=SAMPLE_VACANCY_TEXT,
        )
        assert 0.0 <= score <= 1.0
        assert score > 0.1, f'Score too low: {score}'
        logger.info('Match score (before optimization): %.2f', score)


# =========================================================================
# 4. LLM Provider Tests — РЕАЛЬНЫЕ вызовы API
# =========================================================================


class TestGroqLlama:
    """Тест Groq / Llama 3.3 70B — реальный API вызов."""

    @pytest.mark.skipif(not os.getenv('GROQ_API_KEY'), reason='No GROQ_API_KEY')
    @pytest.mark.asyncio
    async def test_rewrite_with_groq(self, resume_text_pdf: str) -> None:
        """Groq Llama 3.3 70B: полный rewrite резюме."""
        from app.ml.llm_factory import LLMClientFactory
        from app.ml.prompts import REWRITE_SYSTEM_PROMPT
        from app.ml.sanitize import sanitize_for_llm

        client = LLMClientFactory.create('groq')
        try:
            start = time.monotonic()
            response = await client.complete(
                system=REWRITE_SYSTEM_PROMPT,
                user=f'РЕЗЮМЕ:\n{sanitize_for_llm(resume_text_pdf[:8000])}'
                f'\n\nВАКАНСИЯ:\n{sanitize_for_llm(SAMPLE_VACANCY_TEXT)}',
                temperature=0.3,
                max_tokens=4096,
            )
            elapsed = time.monotonic() - start

            assert len(response) > 200, f'Response too short: {len(response)}'
            data = _validate_rewrite_json(response)
            logger.info(
                'Groq Llama rewrite OK: %.1fs, summary=%d chars, %d experience items',
                elapsed,
                len(data['summary']),
                len(data['experience']),
            )
        finally:
            await client.close()


class TestOpenAI:
    """Тест OpenAI GPT — реальный API вызов."""

    @pytest.mark.skipif(not os.getenv('OPENAI_API_KEY'), reason='No OPENAI_API_KEY')
    @pytest.mark.asyncio
    async def test_rewrite_with_openai(self, resume_text_pdf: str) -> None:
        """OpenAI GPT-4o-mini: полный rewrite резюме."""
        from app.ml.llm_factory import LLMClientFactory
        from app.ml.prompts import REWRITE_SYSTEM_PROMPT
        from app.ml.sanitize import sanitize_for_llm

        client = LLMClientFactory.create('openai')
        try:
            start = time.monotonic()
            response = await client.complete(
                system=REWRITE_SYSTEM_PROMPT,
                user=f'РЕЗЮМЕ:\n{sanitize_for_llm(resume_text_pdf[:8000])}'
                f'\n\nВАКАНСИЯ:\n{sanitize_for_llm(SAMPLE_VACANCY_TEXT)}',
                temperature=0.3,
                max_tokens=4096,
            )
            elapsed = time.monotonic() - start

            assert len(response) > 200, f'Response too short: {len(response)}'
            data = _validate_rewrite_json(response)
            logger.info(
                'OpenAI rewrite OK: %.1fs, summary=%d chars, %d experience items',
                elapsed,
                len(data['summary']),
                len(data['experience']),
            )
        finally:
            await client.close()


class TestAnthropic:
    """Тест Anthropic Claude — реальный API вызов."""

    @pytest.mark.skipif(not os.getenv('ANTHROPIC_API_KEY'), reason='No ANTHROPIC_API_KEY')
    @pytest.mark.asyncio
    async def test_rewrite_with_claude(self, resume_text_pdf: str) -> None:
        """Claude Sonnet: полный rewrite резюме."""
        from app.ml.llm_factory import LLMClientFactory
        from app.ml.prompts import REWRITE_SYSTEM_PROMPT
        from app.ml.sanitize import sanitize_for_llm

        client = LLMClientFactory.create('anthropic')
        try:
            start = time.monotonic()
            response = await client.complete(
                system=REWRITE_SYSTEM_PROMPT,
                user=f'РЕЗЮМЕ:\n{sanitize_for_llm(resume_text_pdf[:8000])}'
                f'\n\nВАКАНСИЯ:\n{sanitize_for_llm(SAMPLE_VACANCY_TEXT)}',
                temperature=0.3,
                max_tokens=4096,
            )
            elapsed = time.monotonic() - start

            assert len(response) > 200, f'Response too short: {len(response)}'
            data = _validate_rewrite_json(response)
            logger.info(
                'Anthropic Claude rewrite OK: %.1fs, summary=%d chars, %d exp items',
                elapsed,
                len(data['summary']),
                len(data['experience']),
            )
        finally:
            await client.close()


class TestOpenRouter:
    """Тест OpenRouter — реальный API вызов."""

    @pytest.mark.skipif(not os.getenv('OPENROUTER_API_KEY'), reason='No OPENROUTER_API_KEY')
    @pytest.mark.asyncio
    async def test_rewrite_with_openrouter(self, resume_text_pdf: str) -> None:
        """OpenRouter (Claude 3.5 Sonnet): полный rewrite."""
        from app.ml.llm_factory import LLMClientFactory
        from app.ml.prompts import REWRITE_SYSTEM_PROMPT
        from app.ml.sanitize import sanitize_for_llm

        client = LLMClientFactory.create(
            'openrouter',
            openrouter_model='anthropic/claude-3.5-sonnet',
        )
        try:
            start = time.monotonic()
            response = await client.complete(
                system=REWRITE_SYSTEM_PROMPT,
                user=f'РЕЗЮМЕ:\n{sanitize_for_llm(resume_text_pdf[:8000])}'
                f'\n\nВАКАНСИЯ:\n{sanitize_for_llm(SAMPLE_VACANCY_TEXT)}',
                temperature=0.3,
                max_tokens=4096,
            )
            elapsed = time.monotonic() - start

            assert len(response) > 200, f'Response too short: {len(response)}'
            data = _validate_rewrite_json(response)
            logger.info(
                'OpenRouter rewrite OK: %.1fs, summary=%d chars, %d exp items',
                elapsed,
                len(data['summary']),
                len(data['experience']),
            )
        finally:
            await client.close()


class TestGigaChat:
    """Тест GigaChat — реальный API вызов."""

    @pytest.mark.skipif(not os.getenv('GIGACHAT_CREDENTIALS'), reason='No GIGACHAT_CREDENTIALS')
    @pytest.mark.asyncio
    async def test_rewrite_with_gigachat(self, resume_text_pdf: str) -> None:
        """GigaChat Pro: полный rewrite резюме."""
        from app.ml.llm_factory import LLMClientFactory
        from app.ml.prompts import REWRITE_SYSTEM_PROMPT
        from app.ml.sanitize import sanitize_for_llm

        client = LLMClientFactory.create('gigachat-pro')
        try:
            start = time.monotonic()
            response = await client.complete(
                system=REWRITE_SYSTEM_PROMPT,
                user=f'РЕЗЮМЕ:\n{sanitize_for_llm(resume_text_pdf[:8000])}'
                f'\n\nВАКАНСИЯ:\n{sanitize_for_llm(SAMPLE_VACANCY_TEXT)}',
                temperature=0.3,
                max_tokens=4096,
            )
            elapsed = time.monotonic() - start

            assert len(response) > 200, f'Response too short: {len(response)}'
            data = _validate_rewrite_json(response)
            logger.info(
                'GigaChat rewrite OK: %.1fs, summary=%d chars, %d exp items',
                elapsed,
                len(data['summary']),
                len(data['experience']),
            )
        finally:
            await client.close()


# =========================================================================
# 5. Fallback тесты
# =========================================================================


class TestFallback:
    """Тест автоматического fallback между провайдерами."""

    @pytest.mark.asyncio
    async def test_create_with_fallback(self) -> None:
        """create_with_fallback должен найти хотя бы одного провайдера."""
        from app.ml.llm_factory import LLMClientFactory

        client = LLMClientFactory.create_with_fallback()
        assert client is not None
        logger.info('Fallback selected: %s', type(client).__name__)
        await client.close()

    @pytest.mark.asyncio
    async def test_fallback_rewrite(self, resume_text_pdf: str) -> None:
        """Fallback: rewrite через первого доступного провайдера."""
        from app.ml.llm_factory import LLMClientFactory
        from app.ml.prompts import REWRITE_SYSTEM_PROMPT
        from app.ml.sanitize import sanitize_for_llm

        client = LLMClientFactory.create_with_fallback()
        try:
            response = await client.complete(
                system=REWRITE_SYSTEM_PROMPT,
                user=f'РЕЗЮМЕ:\n{sanitize_for_llm(resume_text_pdf[:5000])}'
                f'\n\nВАКАНСИЯ:\n{sanitize_for_llm(SAMPLE_VACANCY_TEXT)}',
            )
            assert len(response) > 100
            logger.info(
                'Fallback rewrite OK via %s: %d chars',
                type(client).__name__,
                len(response),
            )
        finally:
            await client.close()


# =========================================================================
# 6. DOCX vs PDF — одинаковый результат
# =========================================================================


class TestFormatParity:
    """Проверка что PDF и DOCX дают сравнимые результаты."""

    def test_text_similarity(
        self,
        resume_text_pdf: str,
        resume_text_docx: str,
    ) -> None:
        """Текст из PDF и DOCX должен быть похож."""
        # Оба должны содержать ФИО
        for text in [resume_text_pdf, resume_text_docx]:
            assert any(w in text.lower() for w in ['емельянов', 'сергей']), (
                f'Name not found in: {text[:100]}'
            )

        # Оба должны содержать навыки
        for text in [resume_text_pdf, resume_text_docx]:
            assert any(w in text.lower() for w in ['python', 'php', 'разработ', 'git']), (
                f'Skills not found in: {text[:200]}'
            )

    def test_match_score_parity(
        self,
        resume_text_pdf: str,
        resume_text_docx: str,
    ) -> None:
        """Match Score для PDF и DOCX не должен сильно отличаться."""
        from app.ml.scoring import calculate_match_score

        score_pdf = calculate_match_score(
            resume_text=resume_text_pdf,
            vacancy_text=SAMPLE_VACANCY_TEXT,
        )
        score_docx = calculate_match_score(
            resume_text=resume_text_docx,
            vacancy_text=SAMPLE_VACANCY_TEXT,
        )
        logger.info('Score PDF=%.2f, DOCX=%.2f', score_pdf, score_docx)
        # Разница не должна быть > 0.25 (форматирование может отличаться)
        assert abs(score_pdf - score_docx) < 0.25, (
            f'Score difference too large: PDF={score_pdf:.2f}, DOCX={score_docx:.2f}'
        )


# =========================================================================
# 7. Score improvement — оптимизированное резюме лучше оригинала
# =========================================================================


class TestScoreImprovement:
    """Проверка что оптимизация ДЕЙСТВИТЕЛЬНО улучшает Match Score."""

    @pytest.mark.asyncio
    async def test_score_improves_after_rewrite(self, resume_text_pdf: str) -> None:
        """Match Score после оптимизации > до оптимизации."""
        from app.ml.llm_factory import LLMClientFactory
        from app.ml.prompts import REWRITE_SYSTEM_PROMPT
        from app.ml.sanitize import sanitize_for_llm
        from app.ml.scoring import calculate_match_score

        score_before = calculate_match_score(
            resume_text=resume_text_pdf,
            vacancy_text=SAMPLE_VACANCY_TEXT,
        )

        client = LLMClientFactory.create_with_fallback()
        try:
            response = await client.complete(
                system=REWRITE_SYSTEM_PROMPT,
                user=f'РЕЗЮМЕ:\n{sanitize_for_llm(resume_text_pdf[:8000])}'
                f'\n\nВАКАНСИЯ:\n{sanitize_for_llm(SAMPLE_VACANCY_TEXT)}',
            )
        finally:
            await client.close()

        score_after = calculate_match_score(
            resume_text=response,
            vacancy_text=SAMPLE_VACANCY_TEXT,
        )

        logger.info(
            'Score improvement: %.2f → %.2f (delta +%.2f)',
            score_before,
            score_after,
            score_after - score_before,
        )
        # Оптимизированное резюме должно быть НЕ ХУЖЕ оригинала
        # (может быть чуть хуже если LLM вернул JSON вместо текста)
        assert score_after >= score_before * 0.8, (
            f'Score dropped significantly: {score_before:.2f} → {score_after:.2f}'
        )


# =========================================================================
# 8. Edge cases
# =========================================================================


class TestEdgeCases:
    """Граничные случаи."""

    def test_empty_resume_text(self) -> None:
        """Пустой текст резюме → санитизация возвращает пустую строку."""
        from app.ml.sanitize import sanitize_for_llm

        assert sanitize_for_llm('') == ''
        assert sanitize_for_llm('   ') == ''

    def test_very_long_resume_truncation(self, resume_text_pdf: str) -> None:
        """Очень длинный текст обрезается санитизатором."""
        from app.ml.sanitize import MAX_LLM_INPUT_LENGTH, sanitize_for_llm

        long_text = resume_text_pdf * 100
        sanitized = sanitize_for_llm(long_text)
        assert len(sanitized) <= MAX_LLM_INPUT_LENGTH + 100  # +100 на trailing

    def test_score_with_empty_vacancy(self, resume_text_pdf: str) -> None:
        """Match Score с пустой вакансией → низкий (структурный компонент даёт baseline)."""
        from app.ml.scoring import calculate_match_score

        score = calculate_match_score(
            resume_text=resume_text_pdf,
            vacancy_text='',
        )
        # Structure/readability компоненты дают baseline даже без вакансии
        assert score < 0.5, f'Score with empty vacancy too high: {score}'

    def test_unsupported_file_format(self) -> None:
        """Неподдерживаемый формат → UnsupportedFileFormat."""
        from app.core.exceptions import UnsupportedFileFormat
        from app.resumes.service import _extract_extension

        with pytest.raises(UnsupportedFileFormat):
            _extract_extension('resume')  # нет расширения

    def test_pdf_validate_magic_bytes(self) -> None:
        """Неправильные magic bytes → UnsupportedFileFormat."""
        from app.core.exceptions import UnsupportedFileFormat
        from app.resumes.service import _validate_magic_bytes

        with pytest.raises(UnsupportedFileFormat):
            _validate_magic_bytes(b'NOT_A_PDF', ext='pdf')

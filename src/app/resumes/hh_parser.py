"""Парсинг резюме с hh.ru через Playwright (headless browser).

hh.ru блокирует обычные HTTP-запросы (httpx/requests),
поэтому используется headless Chromium через Playwright.

Зависимость опциональна: если playwright не установлен,
from-url endpoint возвращает user-friendly ошибку с инструкцией.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Флаг доступности Playwright
_HAS_PLAYWRIGHT = False
try:
    from playwright.async_api import async_playwright  # noqa: F401

    _HAS_PLAYWRIGHT = True
except ImportError:
    pass


def is_available() -> bool:
    """Проверка доступности Playwright."""
    return _HAS_PLAYWRIGHT


async def parse_hh_resume(url: str) -> dict[str, object]:
    """Парсинг резюме с hh.ru через headless browser.

    Returns:
        Словарь с полями: name, position, salary, skills, experience, raw_text.

    Raises:
        RuntimeError: Playwright не установлен.
        ValueError: не удалось загрузить или распарсить страницу.
    """
    if not _HAS_PLAYWRIGHT:
        msg = 'playwright не установлен'
        raise RuntimeError(msg)

    from bs4 import BeautifulSoup
    from playwright.async_api import async_playwright

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            )
            page = await context.new_page()
            await page.goto(url, timeout=60000)
            await page.wait_for_timeout(4000)
            html = await page.content()
            await browser.close()
    except Exception as exc:
        logger.warning('Playwright failed to load %s: %s', url, exc)
        msg = 'Не удалось загрузить страницу резюме с hh.ru'
        raise ValueError(msg) from exc

    soup = BeautifulSoup(html, 'html.parser')
    result: dict[str, object] = {}

    # Имя
    name_el = soup.select_one("h2[data-qa='resume-personal-name']")
    result['name'] = name_el.text.strip() if name_el else None

    # Должность
    pos_el = soup.select_one("span[data-qa='resume-block-title-position']")
    result['position'] = pos_el.text.strip() if pos_el else None

    # Зарплата
    salary_el = soup.select_one("[data-qa='resume-block-salary']")
    result['salary'] = salary_el.text.strip() if salary_el else None

    # Навыки
    skills = soup.select("[data-qa='bloko-tag__text']")
    result['skills'] = [s.text.strip() for s in skills]

    # Опыт работы
    experience = []
    jobs = soup.select("[data-qa='resume-block-experience'] .resume-block-item-gap")
    for job in jobs:
        title_el = job.select_one("[data-qa='resume-block-experience-position']")
        company_el = job.select_one("[data-qa='resume-block-experience-employer']")
        period_el = job.select_one("[data-qa='resume-block-experience-date']")
        experience.append(
            {
                'title': title_el.text.strip() if title_el else None,
                'company': company_el.text.strip() if company_el else None,
                'period': period_el.text.strip() if period_el else None,
            }
        )
    result['experience'] = experience

    # Собираем raw_text для оптимизации
    parts: list[str] = []
    if result.get('name'):
        parts.append(str(result['name']))
    if result.get('position'):
        parts.append(f'Должность: {result["position"]}')
    if result.get('salary'):
        parts.append(f'Зарплата: {result["salary"]}')
    for exp in experience:
        line = ', '.join(
            str(v) for v in [exp.get('title'), exp.get('company'), exp.get('period')] if v
        )
        if line:
            parts.append(line)
    if result.get('skills'):
        parts.append('Навыки: ' + ', '.join(str(s) for s in result['skills']))  # type: ignore[union-attr]
    result['raw_text'] = '\n'.join(parts)

    if not result.get('position') and not result.get('name'):
        msg = (
            'Не удалось извлечь данные из резюме. '
            'Возможно, резюме закрыто настройками приватности hh.ru.'
        )
        raise ValueError(msg)

    return result

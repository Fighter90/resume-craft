"""Match Score: расчёт соответствия резюме вакансии.

Формула:
    Keywords  (40%) — TF-IDF пересечение токенов
    Experience (25%) — перекрытие навыков + cosine similarity
    Structure  (20%) — наличие обязательных секций
    Readability (15%) — качество формулировок, метрики
"""

from __future__ import annotations

import math
import re
from collections import Counter


def calculate_match_score(
    *,
    resume_text: str,
    vacancy_text: str,
) -> float:
    """Расчёт общего Match Score (0.0 – 1.0).

    Args:
        resume_text: Текст резюме.
        vacancy_text: Описание вакансии.

    Returns:
        Итоговый балл от 0.0 до 1.0.
    """
    keywords_score = _keywords_score(resume_text, vacancy_text)
    experience_score = _experience_score(resume_text, vacancy_text)
    structure_score = _structure_score(resume_text)
    readability_score = _readability_score(resume_text)

    total = (
        keywords_score * 0.40
        + experience_score * 0.25
        + structure_score * 0.20
        + readability_score * 0.15
    )

    return round(min(max(total, 0.0), 1.0), 3)


def _tokenize(text: str) -> list[str]:
    """Токенизация текста: приведение к lower, удаление не-букв."""
    return re.findall(r'[а-яёa-z0-9]+', text.lower())


def _keywords_score(resume_text: str, vacancy_text: str) -> float:
    """Keywords (40%): TF-IDF пересечение токенов."""
    resume_tokens = set(_tokenize(resume_text))
    vacancy_tokens = set(_tokenize(vacancy_text))

    if not vacancy_tokens:
        return 0.0

    # Фильтрация стоп-слов (упрощённый список)
    stop_words = {
        'и', 'в', 'на', 'с', 'по', 'для', 'от', 'из', 'к', 'за', 'не', 'но', 'а',
        'или', 'как', 'это', 'что', 'все', 'при', 'так', 'бы', 'же', 'его', 'мы',
        'the', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'of', 'is', 'are', 'was',
    }

    resume_tokens -= stop_words
    vacancy_tokens -= stop_words

    if not vacancy_tokens:
        return 0.5

    intersection = resume_tokens & vacancy_tokens
    return len(intersection) / len(vacancy_tokens)


def _experience_score(resume_text: str, vacancy_text: str) -> float:
    """Experience (25%): перекрытие навыков и cosine similarity."""
    resume_counter = Counter(_tokenize(resume_text))
    vacancy_counter = Counter(_tokenize(vacancy_text))

    # Cosine Similarity
    common_tokens = set(resume_counter.keys()) & set(vacancy_counter.keys())

    dot_product = sum(resume_counter[t] * vacancy_counter[t] for t in common_tokens)
    norm_resume = math.sqrt(sum(c ** 2 for c in resume_counter.values()))
    norm_vacancy = math.sqrt(sum(c ** 2 for c in vacancy_counter.values()))

    if norm_resume == 0 or norm_vacancy == 0:
        return 0.0

    cosine_sim = dot_product / (norm_resume * norm_vacancy)
    return min(cosine_sim * 1.5, 1.0)  # Масштабирование


def _structure_score(resume_text: str) -> float:
    """Structure (20%): наличие обязательных секций."""
    required_sections = [
        r'опыт|experience|работа|стаж',
        r'образование|education|университет|вуз',
        r'навыки|skills|технологии|стек',
    ]
    optional_sections = [
        r'контакт|contact|телефон|email',
        r'достижени|achievement|результат',
        r'о себе|summary|профиль',
    ]

    text_lower = resume_text.lower()
    score = 0.0

    # Обязательные секции (60% от structure)
    for pattern in required_sections:
        if re.search(pattern, text_lower):
            score += 0.2

    # Опциональные секции (40% от structure)
    for pattern in optional_sections:
        if re.search(pattern, text_lower):
            score += 0.133

    return min(score, 1.0)


def _readability_score(resume_text: str) -> float:
    """Readability (15%): качество формулировок."""
    score = 0.0
    text_lower = resume_text.lower()

    # Наличие числовых метрик (важно для ATS)
    numbers = re.findall(r'\d+[%+]|\d+\s*(?:раз|%|млн|тыс|человек|проект)', text_lower)
    if len(numbers) >= 3:
        score += 0.3
    elif len(numbers) >= 1:
        score += 0.15

    # Глаголы действия
    action_verbs = [
        'реализовал', 'разработал', 'внедрил', 'оптимизировал', 'увеличил',
        'сократил', 'автоматизировал', 'управлял', 'координировал', 'обеспечил',
        'implemented', 'developed', 'optimized', 'increased', 'reduced', 'managed',
    ]
    verb_count = sum(1 for v in action_verbs if v in text_lower)
    if verb_count >= 5:
        score += 0.3
    elif verb_count >= 2:
        score += 0.15

    # Длина текста (оптимальная — 500-2000 слов)
    word_count = len(resume_text.split())
    if 500 <= word_count <= 2000:
        score += 0.2
    elif 200 <= word_count <= 3000:
        score += 0.1

    # Отсутствие спама (повторяющиеся фразы)
    sentences = re.split(r'[.!?]\s+', resume_text)
    if len(sentences) > 3 and len(set(sentences)) / len(sentences) > 0.8:
        score += 0.2

    return min(score, 1.0)

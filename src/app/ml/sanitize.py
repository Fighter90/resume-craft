"""Санитизация пользовательского ввода перед отправкой в LLM.

Защита от prompt injection: экранирование опасных конструкций,
удаление внутренних метаданных, ограничение длины.
"""

from __future__ import annotations

import re

# Максимальная длина текста для LLM (в символах)
MAX_LLM_INPUT_LENGTH = 50_000

# Паттерны prompt injection
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r'ignore\s+(previous|above|all)\s+instructions', re.IGNORECASE),
    re.compile(r'system\s*:\s*', re.IGNORECASE),
    re.compile(r'<\|?(system|assistant|user)\|?>', re.IGNORECASE),
    re.compile(r'```\s*(system|prompt)', re.IGNORECASE),
]


def sanitize_for_llm(text: str) -> str:
    """Санитизация текста перед отправкой в LLM.

    - Удаляет потенциальные prompt-injection паттерны
    - Ограничивает длину
    - Убирает управляющие символы
    - Не отправляет внутренние метаданные (UUID, пути файлов)

    Args:
        text: Исходный пользовательский текст.

    Returns:
        Очищенный текст для LLM.
    """
    if not text:
        return ''

    # Удаление управляющих символов (кроме \n, \t)
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

    # Удаление prompt-injection паттернов
    for pattern in _INJECTION_PATTERNS:
        sanitized = pattern.sub('[FILTERED]', sanitized)

    # Удаление UUID-подобных строк (защита от утечки внутренних ID)
    sanitized = re.sub(
        r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
        '[ID]',
        sanitized,
        flags=re.IGNORECASE,
    )

    # Удаление путей файловой системы
    sanitized = re.sub(r'(?:/[\w.-]+){3,}', '[PATH]', sanitized)

    # Ограничение длины
    if len(sanitized) > MAX_LLM_INPUT_LENGTH:
        sanitized = (
            sanitized[:MAX_LLM_INPUT_LENGTH] + '\n\n[Текст обрезан из-за ограничения длины]'
        )

    return sanitized.strip()

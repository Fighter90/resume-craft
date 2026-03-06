"""Санитизация пользовательского ввода перед отправкой в LLM.

Защита от prompt injection: экранирование опасных конструкций,
удаление внутренних метаданных, ограничение длины.
"""

from __future__ import annotations

import re
import unicodedata

# Максимальная длина текста для LLM (в символах)
MAX_LLM_INPUT_LENGTH = 50_000

# Паттерны prompt injection
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r'ignore\s+(previous|above|all)\s+instructions', re.IGNORECASE),
    re.compile(r'system\s*:\s*', re.IGNORECASE),
    re.compile(r'<\|?(system|assistant|user)\|?>', re.IGNORECASE),
    re.compile(r'```\s*(system|prompt)', re.IGNORECASE),
    # API-011: Расширенные паттерны prompt injection
    re.compile(r'\[INST\]', re.IGNORECASE),
    re.compile(r'\[/INST\]', re.IGNORECASE),
    re.compile(r'Human\s*:', re.IGNORECASE),
    re.compile(r'Assistant\s*:', re.IGNORECASE),
    re.compile(r'<<\s*SYS\s*>>', re.IGNORECASE),
    re.compile(r'<</\s*SYS\s*>>', re.IGNORECASE),
    re.compile(r'BEGININSTRUCTION', re.IGNORECASE),
    re.compile(r'ENDINSTRUCTION', re.IGNORECASE),
    re.compile(r'###\s*(Instruction|System|Human|Assistant)\s*:', re.IGNORECASE),
    re.compile(r'you\s+are\s+now\s+(a|an|the)\b', re.IGNORECASE),
    re.compile(r'pretend\s+(you|to\s+be)', re.IGNORECASE),
    re.compile(r'act\s+as\s+(a|an|if)\b', re.IGNORECASE),
    re.compile(r'forget\s+(everything|all|your)', re.IGNORECASE),
    re.compile(r'new\s+instructions?\s*:', re.IGNORECASE),
    re.compile(r'override\s+(previous|system|all)', re.IGNORECASE),
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

    # API-011: Unicode NFKC-нормализация (предотвращает обход через гомоглифы)
    sanitized = unicodedata.normalize('NFKC', text)

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

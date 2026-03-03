"""Генерация эмбеддингов для векторного поиска (pgvector)."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Размерность вектора (under BASELINE spec)
EMBEDDING_DIM = 1536


def generate_embedding(text: str) -> list[float]:
    """Генерация эмбеддинга текста.

    Использует sentence-transformers (Phase 1) или OpenAI embeddings (Phase 2).

    Args:
        text: Исходный текст.

    Returns:
        Вектор размерности EMBEDDING_DIM.
    """
    try:
        return _generate_with_sentence_transformers(text)
    except ImportError:
        logger.warning('sentence-transformers not available, using zero vector')
        return [0.0] * EMBEDDING_DIM


def _generate_with_sentence_transformers(text: str) -> list[float]:
    """Генерация через sentence-transformers."""
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer('all-MiniLM-L6-v2')
    embedding = model.encode(text, normalize_embeddings=True)

    # Padding или truncation до EMBEDDING_DIM
    vec = embedding.tolist()
    if len(vec) < EMBEDDING_DIM:
        vec.extend([0.0] * (EMBEDDING_DIM - len(vec)))
    elif len(vec) > EMBEDDING_DIM:
        vec = vec[:EMBEDDING_DIM]

    return vec  # type: ignore[no-any-return]

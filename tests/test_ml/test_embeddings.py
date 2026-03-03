"""Тесты ml/embeddings.py — генерация эмбеддингов."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

from app.ml.embeddings import EMBEDDING_DIM, generate_embedding


class TestGenerateEmbedding:
    """Тесты generate_embedding()."""

    @patch('app.ml.embeddings._generate_with_sentence_transformers')
    def test_success(self, mock_gen: MagicMock) -> None:
        """Успешная генерация эмбеддинга."""
        mock_gen.return_value = [0.1] * EMBEDDING_DIM
        result = generate_embedding('test text')
        assert len(result) == EMBEDDING_DIM
        assert result[0] == 0.1

    @patch('app.ml.embeddings._generate_with_sentence_transformers')
    def test_fallback_on_import_error(self, mock_gen: MagicMock) -> None:
        """ImportError → нулевой вектор."""
        mock_gen.side_effect = ImportError('no module')
        result = generate_embedding('test text')
        assert len(result) == EMBEDDING_DIM
        assert all(v == 0.0 for v in result)

    def test_embedding_dim(self) -> None:
        """Размерность вектора = 1536."""
        assert EMBEDDING_DIM == 1536


class TestGenerateWithSentenceTransformers:
    """Тесты _generate_with_sentence_transformers()."""

    def test_with_mock_model(self) -> None:
        """Генерация через мок sentence-transformers."""
        # Generate a short embedding → should be padded to EMBEDDING_DIM
        mock_embedding = MagicMock()
        mock_embedding.tolist.return_value = [0.5] * 384

        mock_model = MagicMock()
        mock_model.encode.return_value = mock_embedding

        mock_st_module = MagicMock()
        mock_st_module.SentenceTransformer.return_value = mock_model

        sys.modules['sentence_transformers'] = mock_st_module
        try:
            from app.ml.embeddings import _generate_with_sentence_transformers

            result = _generate_with_sentence_transformers('test text')
            assert len(result) == EMBEDDING_DIM
            assert result[0] == 0.5
            # Padded part should be zeros
            assert result[384] == 0.0
        finally:
            sys.modules.pop('sentence_transformers', None)

    def test_truncation(self) -> None:
        """Длинный вектор → обрезается до EMBEDDING_DIM."""
        mock_embedding = MagicMock()
        mock_embedding.tolist.return_value = [0.3] * 2000

        mock_model = MagicMock()
        mock_model.encode.return_value = mock_embedding

        mock_st_module = MagicMock()
        mock_st_module.SentenceTransformer.return_value = mock_model

        sys.modules['sentence_transformers'] = mock_st_module
        try:
            from app.ml.embeddings import _generate_with_sentence_transformers

            result = _generate_with_sentence_transformers('test text')
            assert len(result) == EMBEDDING_DIM
        finally:
            sys.modules.pop('sentence_transformers', None)

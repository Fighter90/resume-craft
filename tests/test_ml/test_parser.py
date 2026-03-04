"""Тесты ml/parser.py — парсинг PDF/DOCX."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

from app.ml.parser import detect_file_format


class TestDetectFileFormat:
    """Тесты detect_file_format()."""

    def test_pdf(self) -> None:
        assert detect_file_format(b'%PDF-1.5 content') == 'pdf'

    def test_docx(self) -> None:
        assert detect_file_format(b'PK\x03\x04 content') == 'docx'

    def test_unknown(self) -> None:
        assert detect_file_format(b'random bytes') is None

    def test_empty(self) -> None:
        assert detect_file_format(b'') is None


class TestExtractTextFromPdf:
    """Тесты extract_text_from_pdf()."""

    def test_success(self) -> None:
        """Успешное извлечение текста из PDF."""
        mock_page = MagicMock()
        mock_page.get_text.return_value = 'Page 1 text'

        mock_doc = MagicMock()
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=False)

        mock_fitz = MagicMock()
        mock_fitz.open.return_value = mock_doc

        # Install mock fitz before importing
        sys.modules['fitz'] = mock_fitz
        try:
            # Re-import to pick up mock
            from app.ml.parser import extract_text_from_pdf

            result = extract_text_from_pdf(b'%PDF-content')
            assert 'Page 1 text' in result
        finally:
            sys.modules.pop('fitz', None)

    def test_empty_text_falls_back_to_ocr(self) -> None:
        """Пустой текст → OCR fallback."""
        mock_page = MagicMock()
        mock_page.get_text.return_value = ''

        mock_doc = MagicMock()
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=False)

        mock_fitz = MagicMock()
        mock_fitz.open.return_value = mock_doc

        sys.modules['fitz'] = mock_fitz
        try:
            from app.ml.parser import extract_text_from_pdf

            with patch('app.ml.parser._ocr_from_pdf', return_value='OCR text'):
                result = extract_text_from_pdf(b'%PDF-scanned')
                assert result == 'OCR text'
        finally:
            sys.modules.pop('fitz', None)


class TestExtractTextFromDocx:
    """Тесты extract_text_from_docx()."""

    def test_success(self) -> None:
        """Успешное извлечение текста из DOCX."""
        mock_p1 = MagicMock(text='Paragraph one')
        mock_p2 = MagicMock(text='')
        mock_p3 = MagicMock(text='Paragraph three')

        mock_doc_instance = MagicMock()
        mock_doc_instance.paragraphs = [mock_p1, mock_p2, mock_p3]

        mock_document_cls = MagicMock(return_value=mock_doc_instance)

        # Mock the docx.Document at module level within parser
        mock_docx_mod = MagicMock()
        mock_docx_mod.Document = mock_document_cls
        sys.modules['docx'] = mock_docx_mod
        try:
            from app.ml.parser import extract_text_from_docx

            result = extract_text_from_docx(b'PK\x03\x04docx-content')
            assert 'Paragraph one' in result
            assert 'Paragraph three' in result
        finally:
            sys.modules.pop('docx', None)


class TestOcrFromPdf:
    """Тесты _ocr_from_pdf()."""

    def test_success(self) -> None:
        """Успешное OCR распознавание."""
        mock_pix = MagicMock(width=100, height=100, samples=b'\x00' * 30000)

        mock_page = MagicMock()
        mock_page.get_pixmap.return_value = mock_pix

        mock_doc = MagicMock()
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=False)

        mock_fitz = MagicMock()
        mock_fitz.open.return_value = mock_doc

        mock_pytesseract = MagicMock()
        mock_pytesseract.image_to_string.return_value = 'OCR recognized text'

        mock_pil_image = MagicMock()
        mock_pil_module = MagicMock()
        mock_pil_module.Image.frombytes.return_value = mock_pil_image

        sys.modules['fitz'] = mock_fitz
        sys.modules['pytesseract'] = mock_pytesseract
        sys.modules['PIL'] = mock_pil_module
        sys.modules['PIL.Image'] = mock_pil_module.Image
        try:
            from app.ml.parser import _ocr_from_pdf

            result = _ocr_from_pdf(b'%PDF-scanned')
            assert 'OCR recognized text' in result
        finally:
            sys.modules.pop('fitz', None)
            sys.modules.pop('pytesseract', None)
            sys.modules.pop('PIL', None)
            sys.modules.pop('PIL.Image', None)

    def test_import_error_fallback(self) -> None:
        """ImportError → пустая строка."""
        # Remove fitz/pytesseract/PIL from sys.modules and make import fail
        saved = {}
        for mod_name in ('fitz', 'pytesseract', 'PIL', 'PIL.Image'):
            if mod_name in sys.modules:
                saved[mod_name] = sys.modules.pop(mod_name)

        # Force ImportError by using a module that raises it
        import builtins

        real_import = builtins.__import__

        def _mock_import(name, *args, **kwargs):  # type: ignore[no-untyped-def]
            if name in ('fitz', 'pytesseract', 'PIL'):
                raise ImportError(f'No module named {name}')
            return real_import(name, *args, **kwargs)

        builtins.__import__ = _mock_import
        try:
            from app.ml.parser import _ocr_from_pdf

            result = _ocr_from_pdf(b'%PDF-scanned')
            assert result == ''
        finally:
            builtins.__import__ = real_import
            for mod_name, mod_obj in saved.items():
                sys.modules[mod_name] = mod_obj

    def test_exception_fallback(self) -> None:
        """Общая ошибка → пустая строка."""
        mock_fitz = MagicMock()
        mock_fitz.open.side_effect = RuntimeError('parsing error')

        mock_pytesseract = MagicMock()
        mock_pil_module = MagicMock()

        sys.modules['fitz'] = mock_fitz
        sys.modules['pytesseract'] = mock_pytesseract
        sys.modules['PIL'] = mock_pil_module
        sys.modules['PIL.Image'] = mock_pil_module.Image
        try:
            from app.ml.parser import _ocr_from_pdf

            result = _ocr_from_pdf(b'%PDF-corrupted')
            assert result == ''
        finally:
            sys.modules.pop('fitz', None)
            sys.modules.pop('pytesseract', None)
            sys.modules.pop('PIL', None)
            sys.modules.pop('PIL.Image', None)

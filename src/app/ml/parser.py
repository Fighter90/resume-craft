"""Парсинг документов: PDF (PyMuPDF), DOCX (python-docx), OCR fallback."""

from __future__ import annotations

import io
import logging

logger = logging.getLogger(__name__)


def extract_text_from_pdf(content: bytes) -> str:
    """Извлечение текста из PDF через PyMuPDF.

    Fallback на OCR (pytesseract) если текст пустой.
    """
    import fitz  # noqa: PLC0415

    text_parts: list[str] = []
    with fitz.open(stream=content, filetype='pdf') as doc:
        for page in doc:
            page_text = page.get_text()  # type: ignore[union-attr]
            if page_text.strip():
                text_parts.append(page_text)

    text = '\n'.join(text_parts).strip()

    # OCR fallback для сканированных PDF
    if not text:
        logger.info('PDF text is empty, attempting OCR fallback')
        text = _ocr_from_pdf(content)

    return text


def extract_text_from_docx(content: bytes) -> str:
    """Извлечение текста из DOCX через python-docx."""
    from docx import Document  # noqa: PLC0415

    doc = Document(io.BytesIO(content))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return '\n'.join(paragraphs)


def _ocr_from_pdf(content: bytes) -> str:
    """OCR fallback для сканированных PDF (pytesseract + Pillow)."""
    try:
        import fitz  # noqa: PLC0415
        import pytesseract  # noqa: PLC0415
        from PIL import Image  # noqa: PLC0415

        text_parts: list[str] = []
        with fitz.open(stream=content, filetype='pdf') as doc:
            for page in doc:
                pix = page.get_pixmap(dpi=300)  # type: ignore[union-attr]
                img = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
                page_text = pytesseract.image_to_string(img, lang='rus+eng')
                if page_text.strip():
                    text_parts.append(page_text)

        return '\n'.join(text_parts).strip()

    except ImportError:
        logger.warning('pytesseract or Pillow not installed, OCR unavailable')
        return ''
    except Exception:
        logger.exception('OCR failed')
        return ''


def detect_file_format(content: bytes) -> str | None:
    """Определение формата файла по magic bytes.

    Returns:
        'pdf', 'docx' или None.
    """
    if content.startswith(b'%PDF'):
        return 'pdf'
    if content.startswith(b'PK\x03\x04'):
        return 'docx'
    return None

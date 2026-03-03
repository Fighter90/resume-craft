"""Сервис экспорта: генерация DOCX из результатов оптимизации."""

from __future__ import annotations

import io
import logging
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

logger = logging.getLogger(__name__)


def generate_docx(rewritten_data: dict[str, Any] | None, *, raw_text: str | None = None) -> bytes:
    """Генерация DOCX-файла из результатов оптимизации.

    Args:
        rewritten_data: Структурированные данные от LLM (JSON).
        raw_text: Fallback — текстовый ответ LLM, если JSON невалиден.

    Returns:
        DOCX-файл в виде bytes.
    """
    doc = Document()

    # Стили
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)

    if rewritten_data:
        _build_structured_docx(doc, rewritten_data)
    elif raw_text:
        _build_plain_docx(doc, raw_text)
    else:
        doc.add_paragraph('Данные для экспорта отсутствуют.')

    # Сохранение в bytes
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def _build_structured_docx(doc: Document, data: dict[str, Any]) -> None:
    """Генерация структурированного DOCX из JSON-данных LLM."""
    # Профессиональное саммари
    summary = data.get('summary', '')
    if summary:
        heading = doc.add_heading('Профессиональное резюме', level=1)
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p = doc.add_paragraph(summary)
        p.paragraph_format.space_after = Pt(12)

    # Опыт работы
    experience = data.get('experience', [])
    if experience:
        doc.add_heading('Опыт работы', level=2)
        for exp in experience:
            position = exp.get('position', '')
            company = exp.get('company', '')
            period = exp.get('period', '')

            p = doc.add_paragraph()
            run = p.add_run(position)
            run.bold = True
            run.font.size = Pt(12)

            if company or period:
                p2 = doc.add_paragraph()
                if company:
                    p2.add_run(company).italic = True
                if company and period:
                    p2.add_run(f' | {period}')
                elif period:
                    p2.add_run(period)

            achievements = exp.get('achievements', [])
            for ach in achievements:
                doc.add_paragraph(ach, style='List Bullet')

            doc.add_paragraph()  # Отступ

    # Образование
    education = data.get('education', [])
    if education:
        doc.add_heading('Образование', level=2)
        for edu in education:
            institution = edu.get('institution', '')
            degree = edu.get('degree', '')
            specialization = edu.get('specialization', '')
            year = edu.get('year', '')

            p = doc.add_paragraph()
            run = p.add_run(institution)
            run.bold = True

            details = []
            if degree:
                details.append(degree)
            if specialization:
                details.append(specialization)
            if year:
                details.append(str(year))
            if details:
                doc.add_paragraph(', '.join(details))

    # Навыки
    skills = data.get('skills', [])
    if skills:
        doc.add_heading('Навыки', level=2)
        doc.add_paragraph(', '.join(skills))


def _build_plain_docx(doc: Document, text: str) -> None:
    """Генерация простого DOCX из текста."""
    heading = doc.add_heading('Оптимизированное резюме', level=1)
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for paragraph in text.split('\n'):
        stripped = paragraph.strip()
        if stripped:
            doc.add_paragraph(stripped)

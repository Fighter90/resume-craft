"""Страница 14: Экспорт оптимизированного резюме.

Прототип: 14-export.html
Выбор формата (PDF/DOCX/hh.ru), шаблона, предпросмотр, скачивание.
"""

from __future__ import annotations

import io

import streamlit as st

from streamlit_app.demo_data import DEMO_OPTIMIZED


def render() -> None:
    """Отрисовка страницы экспорта."""
    result = st.session_state.get('result', {})
    optimized = result.get('optimized', DEMO_OPTIMIZED)

    st.markdown("""
    <div class="hero-section">
        <h1>📥 Экспорт резюме</h1>
        <p>Выберите формат и шаблон для скачивания</p>
    </div>
    """, unsafe_allow_html=True)

    config_col, preview_col = st.columns([1, 2])

    with config_col:
        # ── Формат ──
        st.subheader('Формат')
        fmt = st.radio(
            'Выберите формат', ['DOCX', 'PDF', 'Текст для hh.ru'],
            label_visibility='collapsed',
        )

        # ── Шаблон ──
        st.subheader('Шаблон')
        templates = {
            'Минимальный': 'Чистый, ATS-дружественный, без графики',
            'Профессиональный': 'Структурированный, с акцентами — рекомендуем',
            'Креативный': 'Современный дизайн, для стартапов и IT',
        }
        template = st.radio(
            'Шаблон', list(templates.keys()),
            index=1,
            label_visibility='collapsed',
        )
        st.caption(templates[template])

        # ── Параметры ──
        st.subheader('Параметры')
        st.checkbox('Включить фото', value=False)
        st.checkbox('Включить контакты', value=True)
        st.checkbox('Включить Match Score', value=False)
        st.selectbox('Формат страницы', ['A4', 'Letter'])

        st.divider()

        # ── Скачивание ──
        if fmt == 'DOCX':
            docx_bytes = _generate_demo_docx(optimized)
            if docx_bytes:
                st.download_button(
                    '📥 Скачать DOCX',
                    data=docx_bytes,
                    file_name='resume_optimized.docx',
                    mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    type='primary',
                    use_container_width=True,
                )
        elif fmt == 'PDF':
            st.button(
                '📥 Скачать PDF',
                type='primary',
                use_container_width=True,
                disabled=True,
            )
            st.caption('PDF-экспорт доступен в тарифе Standard+')
        else:
            st.button(
                '📋 Скопировать для hh.ru',
                type='primary',
                use_container_width=True,
            )
            st.caption('Текст скопирован в буфер обмена')

        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            if st.button('✏️ Редактировать', use_container_width=True):
                st.session_state.page = 'editor'
                st.rerun()
        with c2:
            if st.button('← Результаты', use_container_width=True):
                st.session_state.page = 'wizard'
                st.session_state.step = 4
                st.rerun()

    with preview_col:
        st.subheader(f'Предпросмотр ({template})')

        # ── Preview ──
        summary = optimized.get('summary', '')
        experience = optimized.get('experience', [])
        education = optimized.get('education', [])
        skills = optimized.get('skills', [])

        # Build preview HTML
        exp_html = ''
        for exp in experience:
            achievements = ''.join(f'<li>{a}</li>' for a in exp.get('achievements', []))
            exp_html += f"""
            <div style="margin-bottom: 1rem;">
                <strong>{exp.get('position', '')}</strong> — {exp.get('company', '')}
                <span style="color: #6B7280;">({exp.get('period', '')})</span>
                <ul style="padding-left: 1.25rem; margin: 0.25rem 0;">{achievements}</ul>
            </div>
            """

        edu_html = ''
        for edu in education:
            edu_html += (
                f"<p>{edu.get('institution', '')}, "
                f"{edu.get('specialization', '')} ({edu.get('year', '')})</p>"
            )

        skills_html = ', '.join(skills)

        border_color = '#565ADD' if template == 'Профессиональный' else (
            '#10B981' if template == 'Креативный' else '#E5E7EB'
        )

        st.markdown(f"""
        <div style="background: white; border-radius: 12px; padding: 2rem;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    border-top: 4px solid {border_color};
                    max-height: 600px; overflow-y: auto;">
            <h2 style="margin: 0 0 0.25rem 0;">Иванов Александр Сергеевич</h2>
            <p style="color: #6B7280; margin: 0 0 1rem 0;">Senior Product Manager</p>

            <h3 style="color: {border_color};">О себе</h3>
            <p>{summary}</p>

            <h3 style="color: {border_color};">Опыт работы</h3>
            {exp_html}

            <h3 style="color: {border_color};">Образование</h3>
            {edu_html}

            <h3 style="color: {border_color};">Навыки</h3>
            <p>{skills_html}</p>
        </div>
        """, unsafe_allow_html=True)


def _generate_demo_docx(optimized: dict) -> bytes | None:
    """Генерация DOCX из демо-данных."""
    try:
        from docx import Document
        from docx.shared import Pt

        doc = Document()
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Calibri'
        font.size = Pt(11)

        doc.add_heading('Иванов Александр Сергеевич', level=1)
        doc.add_paragraph(optimized.get('summary', ''))

        doc.add_heading('Опыт работы', level=2)
        for exp in optimized.get('experience', []):
            doc.add_heading(
                f"{exp.get('position', '')} — {exp.get('company', '')} ({exp.get('period', '')})",
                level=3,
            )
            for ach in exp.get('achievements', []):
                doc.add_paragraph(f'• {ach}')

        doc.add_heading('Образование', level=2)
        for edu in optimized.get('education', []):
            inst = edu.get('institution', '')
            spec = edu.get('specialization', '')
            year = edu.get('year', '')
            doc.add_paragraph(f'{inst}, {spec} ({year})')

        doc.add_heading('Навыки', level=2)
        doc.add_paragraph(', '.join(optimized.get('skills', [])))

        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        return buf.getvalue()

    except ImportError:
        st.warning('python-docx не установлен. DOCX-экспорт недоступен.')
        return None

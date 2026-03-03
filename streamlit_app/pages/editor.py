"""Страница 13: Редактор оптимизированного резюме.

Прототип: 13-editor.html
5 секций (header, about, experience, education, skills), AI-подсказки.
"""

from __future__ import annotations

import streamlit as st

from streamlit_app.demo_data import DEMO_OPTIMIZED


def render() -> None:
    """Отрисовка редактора резюме."""
    result = st.session_state.get('result', {})
    optimized = result.get('optimized', DEMO_OPTIMIZED)

    st.markdown("""
    <div class="hero-section">
        <h1>✏️ Редактор резюме</h1>
        <p>Отредактируйте каждую секцию перед экспортом</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Toolbar ──
    t1, t2, t3, t4 = st.columns(4)
    with t1:
        if st.button('💾 Сохранить', use_container_width=True):
            st.toast('Изменения сохранены')
    with t2:
        if st.button('↩️ Отменить', use_container_width=True):
            st.toast('Отменено')
    with t3:
        if st.button('📥 Экспорт', type='primary', use_container_width=True):
            st.session_state.page = 'export'
            st.rerun()
    with t4:
        if st.button('← К результатам', use_container_width=True):
            st.session_state.page = 'wizard'
            st.session_state.step = 4
            st.rerun()

    st.divider()

    # ── Editor + AI Suggestions layout ──
    editor_col, ai_col = st.columns([3, 1])

    with editor_col:
        # Секция 1: Заголовок
        with st.expander('👤 Заголовок / ФИО', expanded=True):
            st.text_input('ФИО', value='Иванов Александр Сергеевич', key='ed_name')
            st.text_input('Должность', value='Senior Product Manager', key='ed_position')
            c1, c2 = st.columns(2)
            with c1:
                st.text_input('Email', value='a.ivanov@email.com', key='ed_email')
            with c2:
                st.text_input('Телефон', value='+7 (999) 123-45-67', key='ed_phone')
            c3, c4 = st.columns(2)
            with c3:
                st.text_input('Город', value='Москва', key='ed_city')
            with c4:
                st.text_input('Telegram', value='@aivanov', key='ed_tg')

        # Секция 2: О себе
        with st.expander('📝 Профессиональное саммари', expanded=True):
            st.text_area(
                'О себе',
                value=optimized.get('summary', ''),
                height=120,
                key='ed_summary',
            )

        # Секция 3: Опыт работы
        with st.expander('💼 Опыт работы', expanded=True):
            for i, exp in enumerate(optimized.get('experience', [])):
                st.markdown(f"**{exp.get('position', '')} — {exp.get('company', '')}**")
                st.caption(exp.get('period', ''))
                for j, ach in enumerate(exp.get('achievements', [])):
                    st.text_input(
                        f'Достижение {j + 1}',
                        value=ach,
                        key=f'ed_ach_{i}_{j}',
                        label_visibility='collapsed',
                    )
                if st.button('+ Добавить достижение', key=f'add_ach_{i}'):
                    st.toast('Будет доступно в Phase 2')
                st.divider()
            if st.button('+ Добавить место работы'):
                st.toast('Будет доступно в Phase 2')

        # Секция 4: Образование
        with st.expander('🎓 Образование', expanded=False):
            for i, edu in enumerate(optimized.get('education', [])):
                c1, c2 = st.columns(2)
                with c1:
                    st.text_input(
                        'Учебное заведение',
                        value=edu.get('institution', ''),
                        key=f'ed_inst_{i}',
                    )
                with c2:
                    st.text_input(
                        'Специализация',
                        value=edu.get('specialization', ''),
                        key=f'ed_spec_{i}',
                    )
                c3, c4 = st.columns(2)
                with c3:
                    st.text_input(
                        'Степень',
                        value=edu.get('degree', ''),
                        key=f'ed_deg_{i}',
                    )
                with c4:
                    st.number_input(
                        'Год',
                        value=edu.get('year', 2019),
                        min_value=1970,
                        max_value=2030,
                        key=f'ed_year_{i}',
                    )

        # Секция 5: Навыки
        with st.expander('🛠️ Навыки', expanded=False):
            skills = optimized.get('skills', [])
            skills_str = ', '.join(skills)
            edited_skills = st.text_area(
                'Навыки (через запятую)',
                value=skills_str,
                height=100,
                key='ed_skills',
            )
            if edited_skills:
                parsed = [s.strip() for s in edited_skills.split(',') if s.strip()]
                st.write(f'Навыков: {len(parsed)}')
                pills_html = ''.join(
                    f'<span class="keyword-pill">{s}</span>' for s in parsed
                )
                st.markdown(f'<div>{pills_html}</div>', unsafe_allow_html=True)

    with ai_col:
        st.markdown('### 🤖 AI-подсказки')

        st.markdown("""
        <div class="feature-card" style="border-left: 3px solid #10B981;">
            <strong>Саммари</strong>
            <p style="font-size: 0.85rem; color: #6B7280;">
            Добавьте конкретные метрики: MAU, конверсия, выручка.
            Формула: Действие + Результат + Метрика.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="feature-card" style="border-left: 3px solid #F59E0B;">
            <strong>Ключевые слова</strong>
            <p style="font-size: 0.85rem; color: #6B7280;">
            Добавьте: Unit Economics, Retention, LTV/CAC — частые в вакансиях PM.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="feature-card" style="border-left: 3px solid #565ADD;">
            <strong>Структура</strong>
            <p style="font-size: 0.85rem; color: #6B7280;">
            Ключевые достижения — в начало каждого блока.
            3-5 буллетов на место работы.
            </p>
        </div>
        """, unsafe_allow_html=True)

        if st.button('🔄 Обновить подсказки', use_container_width=True):
            st.toast('AI-подсказки обновлены (демо)')

        st.divider()

        # Match Score preview
        result_data = st.session_state.get('result', {})
        score = result_data.get('match_score_after', 87)
        st.metric('Match Score', f'{score}%')
        st.progress(score / 100)

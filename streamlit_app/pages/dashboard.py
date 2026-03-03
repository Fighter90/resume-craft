"""Страница 06: Дашборд (главная для авторизованных).

Прототип: 06-dashboard.html
Статистические карточки, последние резюме, быстрые действия.
"""

from __future__ import annotations

import streamlit as st

from streamlit_app.demo_data import DEMO_RESUMES_LIST


def render() -> None:
    """Отрисовка дашборда."""
    user = st.session_state.get('user_email', 'Пользователь')
    st.title(f'Добро пожаловать, {user.split("@")[0]}!')
    st.write('Ваша панель управления ResumeCraft')

    # ── Статистика ──
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-value">3</div>
            <div class="stat-label">Загружено резюме</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-value">2</div>
            <div class="stat-label">Оптимизаций выполнено</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-value" style="color: #10B981;">78%</div>
            <div class="stat-label">Средний Match Score</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Лимит тарифа ──
    st.markdown('<br>', unsafe_allow_html=True)
    plan = st.session_state.get('user_plan', 'Free')
    used = 2
    total = 5 if plan == 'Free' else 30
    st.write(f'**Тариф:** {plan} · Использовано {used}/{total} оптимизаций')
    st.progress(used / total)

    # ── Быстрые действия ──
    st.markdown('<br>', unsafe_allow_html=True)
    st.subheader('Быстрые действия')
    a1, a2, a3 = st.columns(3)
    with a1:
        if st.button('📄 Загрузить резюме', use_container_width=True, type='primary'):
            st.session_state.page = 'wizard'
            st.session_state.step = 0
            st.rerun()
    with a2:
        if st.button('📋 Мои резюме', use_container_width=True):
            st.session_state.page = 'resumes'
            st.rerun()
    with a3:
        if st.button('📊 История', use_container_width=True):
            st.session_state.page = 'history'
            st.rerun()

    # ── Последние резюме ──
    st.markdown('<br>', unsafe_allow_html=True)
    st.subheader('Последние резюме')

    if not DEMO_RESUMES_LIST:
        st.info('У вас пока нет резюме. Загрузите первое!')
        return

    for resume in DEMO_RESUMES_LIST[:3]:
        status_colors = {
            'Оптимизировано': '🟢',
            'Черновик': '🔵',
            'В обработке': '🟡',
            'Ошибка': '🔴',
        }
        status_ru = {
            'optimized': 'Оптимизировано',
            'draft': 'Черновик',
            'processing': 'В обработке',
            'error': 'Ошибка',
        }
        display_status = status_ru.get(resume['status'], resume['status'])
        icon = status_colors.get(display_status, '⚪')

        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
        with col1:
            st.write(f"**{resume['title']}**")
        with col2:
            st.write(f"{icon} {display_status}")
        with col3:
            if resume.get('match_score'):
                st.write(f"Match: {resume['match_score']}%")
            else:
                st.write('—')
        with col4:
            st.write(resume.get('date', ''))

    st.divider()
    if st.button('Все резюме →'):
        st.session_state.page = 'resumes'
        st.rerun()

"""Страница 20: Ошибка 404.

Прототип: 20-error-404.html
Страница «не найдено» с навигацией.
"""

from __future__ import annotations

import streamlit as st


def render() -> None:
    """Отрисовка страницы 404."""
    st.markdown("""
    <div style="text-align: center; padding: 4rem 2rem;">
        <div style="font-size: 8rem; font-weight: 700; color: #E5E7EB;">404</div>
        <h2 style="color: #374151; margin: 1rem 0;">Страница не найдена</h2>
        <p style="color: #6B7280; max-width: 400px; margin: 0 auto;">
            Запрошенная страница не существует или была перемещена.
            Вернитесь на главную страницу.
        </p>
    </div>
    """, unsafe_allow_html=True)

    _c1, c2, _c3 = st.columns([1, 2, 1])
    with c2:
        if st.button('🏠 На главную', type='primary', use_container_width=True):
            if st.session_state.get('authenticated'):
                st.session_state.page = 'dashboard'
            else:
                st.session_state.page = 'landing'
            st.rerun()

        st.markdown('<br>', unsafe_allow_html=True)

        st.markdown('**Полезные ссылки:**')
        links = [
            ('📄 Мои резюме', 'resumes'),
            ('🤖 Новая оптимизация', 'wizard'),
            ('📊 История', 'history'),
            ('⚙️ Настройки', 'settings'),
        ]
        for label, page in links:
            if st.button(label, key=f'err_{page}', use_container_width=True):
                st.session_state.page = page
                st.rerun()

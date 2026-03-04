"""Страница 05: Тарифы (подробное сравнение).

Прототип: 05-pricing.html
Три плана: Free / Standard / Pro — с таблицей сравнения функциональности.
"""

from __future__ import annotations

import streamlit as st

from streamlit_app.styles import render_top_navbar


def render() -> None:
    """Отрисовка страницы тарифов."""
    # Top navbar для публичной страницы
    if not st.session_state.get('authenticated'):
        render_top_navbar()
    st.title('Тарифные планы')
    st.write('Выберите план, который подходит вам. Начните бесплатно.')

    # ── 3 карточки ──
    t1, t2, t3 = st.columns(3)
    with t1:
        st.markdown("""
        <div class="plan-card">
            <div class="badge badge-gray">Free</div>
            <div style="font-size: 2.5rem; font-weight: 700; margin: 0.5rem 0;">0 &#8381;</div>
            <div style="color: #9CA3AF;">навсегда</div>
            <hr>
            <ul style="list-style: none; padding: 0; text-align: left;">
                <li>✅ 5 оптимизаций/мес</li>
                <li>✅ Llama 3 (Groq)</li>
                <li>✅ Экспорт DOCX</li>
                <li>✅ Match Score</li>
                <li>❌ GigaChat Pro</li>
                <li>❌ Экспорт PDF</li>
                <li>❌ Поиск hh.ru</li>
                <li>❌ Приоритетная поддержка</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button('Текущий план', use_container_width=True, disabled=True):
            pass

    with t2:
        st.markdown("""
        <div class="plan-card popular">
            <div class="badge badge-indigo">Standard &mdash; Популярный</div>
            <div style="font-size: 2.5rem; font-weight: 700; margin: 0.5rem 0;">490 &#8381;</div>
            <div style="color: #9CA3AF;">в месяц</div>
            <hr>
            <ul style="list-style: none; padding: 0; text-align: left;">
                <li>✅ 30 оптимизаций/мес</li>
                <li>✅ GigaChat Pro + Llama 3</li>
                <li>✅ Экспорт DOCX + PDF</li>
                <li>✅ Match Score + ATS</li>
                <li>✅ Встроенный редактор</li>
                <li>✅ Поиск hh.ru</li>
                <li>❌ GPT-4o</li>
                <li>❌ Приоритетная поддержка</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button('Выбрать Standard', type='primary', use_container_width=True):
            st.toast('Оплата тарифов будет доступна в ближайшем обновлении')

    with t3:
        st.markdown("""
        <div class="plan-card">
            <div class="badge badge-green">Pro</div>
            <div style="font-size: 2.5rem; font-weight: 700; margin: 0.5rem 0;">1 490 &#8381;</div>
            <div style="color: #9CA3AF;">в месяц</div>
            <hr>
            <ul style="list-style: none; padding: 0; text-align: left;">
                <li>✅ Безлимит оптимизаций</li>
                <li>✅ Все AI-модели</li>
                <li>✅ Все форматы экспорта</li>
                <li>✅ Match Score + ATS</li>
                <li>✅ Встроенный редактор</li>
                <li>✅ Поиск hh.ru</li>
                <li>✅ GPT-4o</li>
                <li>✅ Приоритетная поддержка</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button('Выбрать Pro', use_container_width=True):
            st.toast('Оплата тарифов будет доступна в ближайшем обновлении')

    # ── Таблица сравнения ──
    st.markdown('<br>', unsafe_allow_html=True)
    st.subheader('Сравнение планов')
    comparison = {
        'Функция': [
            'Оптимизаций/мес', 'GigaChat Pro', 'Llama 3 (Groq)', 'GPT-4o',
            'Экспорт DOCX', 'Экспорт PDF', 'Match Score', 'ATS-рейтинг',
            'Редактор', 'Поиск hh.ru', 'Шаблоны', 'Приоритетная поддержка',
        ],
        'Free': [
            '5', '—', '✅', '—',
            '✅', '—', '✅', '—',
            '—', '—', '1', '—',
        ],
        'Standard (490 ₽)': [
            '30', '✅', '✅', '—',
            '✅', '✅', '✅', '✅',
            '✅', '✅', '3', '—',
        ],
        'Pro (1 490 ₽)': [
            '∞', '✅', '✅', '✅',
            '✅', '✅', '✅', '✅',
            '✅', '✅', '3+', '✅',
        ],
    }
    st.table(comparison)

    # ── FAQ ──
    st.markdown('<br>', unsafe_allow_html=True)
    st.subheader('Частые вопросы о тарифах')
    with st.expander('Можно ли попробовать бесплатно?'):
        st.write('Да, план Free — навсегда бесплатный, 5 оптимизаций в месяц.')
    with st.expander('Как происходит оплата?'):
        st.write('Ежемесячная подписка. Оплата банковской картой, СБП или ЮKassa.')
    with st.expander('Можно ли отменить подписку?'):
        st.write('Да, отмена в любой момент. Доступ сохраняется до конца оплаченного периода.')
    with st.expander('Что если лимит исчерпан?'):
        st.write(
            'Вы можете перейти на более высокий план '
            'или дождаться обновления лимита 1-го числа.',
        )

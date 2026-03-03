"""Страница 15: История активности.

Прототип: 15-history.html
Timeline сгруппированная по дням, типы событий (оптимизация/загрузка/экспорт/аккаунт).
"""

from __future__ import annotations

import streamlit as st

from streamlit_app.demo_data import DEMO_HISTORY


def render() -> None:
    """Отрисовка страницы истории."""
    st.title('История активности')
    st.write('Все ваши действия в хронологическом порядке')

    # ── Фильтры ──
    f1, f2 = st.columns(2)
    with f1:
        event_filter = st.selectbox(
            'Тип события',
            ['Все', 'Оптимизация', 'Загрузка', 'Экспорт', 'Аккаунт'],
        )
    with f2:
        _period_filter = st.selectbox(
            'Период', ['За всё время', 'Сегодня', 'Неделя', 'Месяц'],
        )

    st.divider()

    # ── Timeline ──
    event_icons = {
        'optimization': ('🤖', 'badge-green'),
        'upload': ('📄', 'badge-indigo'),
        'export': ('📥', 'badge-gray'),
        'account': ('👤', 'badge-yellow'),
    }

    for day_group in DEMO_HISTORY:
        date_str = day_group['date']
        events = day_group['events']

        # Filter
        if event_filter != 'Все':
            type_map = {
                'Оптимизация': 'optimization',
                'Загрузка': 'upload',
                'Экспорт': 'export',
                'Аккаунт': 'account',
            }
            target = type_map.get(event_filter, '')
            events = [e for e in events if e.get('type') == target]

        if not events:
            continue

        st.subheader(date_str)

        for event in events:
            icon, _badge_cls = event_icons.get(event.get('type', 'account'), ('⚪', 'badge-gray'))
            time_str = event.get('time', '')
            title = event.get('title', '')
            description = event.get('detail', '')
            score = event.get('score')

            score_html = ''
            if score:
                score_html = f'<span class="badge badge-green">Match: {score}%</span>'

            st.markdown(f"""
            <div class="timeline-item">
                <div style="display: flex; align-items: flex-start; gap: 1rem;">
                    <div style="font-size: 1.5rem; min-width: 2rem; text-align: center;">
                        {icon}
                    </div>
                    <div style="flex: 1;">
                        <div style="display: flex; justify-content: space-between;
                                    align-items: center;">
                            <strong>{title}</strong>
                            <span style="color: #9CA3AF; font-size: 0.85rem;">{time_str}</span>
                        </div>
                        <p style="color: #6B7280; margin: 0.25rem 0; font-size: 0.9rem;">
                            {description}
                        </p>
                        {score_html}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Пусто ──
    if not DEMO_HISTORY:
        st.info('История пуста. Начните с загрузки резюме!')

    st.divider()
    st.caption(f'Всего событий: {sum(len(g["events"]) for g in DEMO_HISTORY)}')

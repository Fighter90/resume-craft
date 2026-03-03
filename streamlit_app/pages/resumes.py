"""Страница 07: Мои резюме (список с поиском, фильтрацией, пагинацией).

Прототип: 07-resumes.html
Таблица/грид резюме, фильтры по статусу, сортировка, удаление.
"""

from __future__ import annotations

import streamlit as st

from streamlit_app.demo_data import DEMO_RESUMES_LIST


def render() -> None:
    """Отрисовка списка резюме пользователя."""
    st.title('Мои резюме')

    # ── Панель действий ──
    a1, a2 = st.columns([3, 1])
    with a1:
        search = st.text_input(
            'Поиск', placeholder='Название резюме...', label_visibility='collapsed',
        )
    with a2:
        if st.button('📄 Загрузить новое', type='primary', use_container_width=True):
            st.session_state.page = 'wizard'
            st.session_state.step = 0
            st.rerun()

    # ── Фильтры ──
    f1, f2 = st.columns(2)
    with f1:
        status_filter = st.selectbox(
            'Статус', ['Все', 'Оптимизировано', 'Черновик', 'В обработке', 'Ошибка'],
        )
    with f2:
        sort_by = st.selectbox('Сортировка', ['Дата (новые)', 'Дата (старые)', 'Название А-Я'])

    # ── Фильтрация данных ──
    resumes = list(DEMO_RESUMES_LIST)

    if search:
        resumes = [r for r in resumes if search.lower() in r['title'].lower()]

    if status_filter != 'Все':
        resumes = [r for r in resumes if r['status'] == status_filter]

    if sort_by == 'Дата (старые)':
        resumes.reverse()
    elif sort_by == 'Название А-Я':
        resumes.sort(key=lambda r: r['title'])

    # ── Счётчик ──
    st.write(f'Найдено: {len(resumes)}')

    # ── Карточки ──
    if not resumes:
        st.info('Нет резюме, соответствующих фильтрам.')
        return

    for i, resume in enumerate(resumes):
        status_badge = {
            'Оптимизировано': ('badge-green', '✅'),
            'Черновик': ('badge-gray', '📝'),
            'В обработке': ('badge-indigo', '⏳'),
            'Ошибка': ('badge-red', '❌'),
        }
        badge_cls, badge_icon = status_badge.get(resume['status'], ('badge-gray', '⚪'))

        with st.container():
            c1, c2, c3, c4, c5 = st.columns([3, 2, 1.5, 1.5, 1])
            with c1:
                st.markdown(f"**{resume['title']}**")
                st.caption(f"{resume.get('format', 'PDF').upper()} · {resume.get('date', '')}")
            with c2:
                st.markdown(
                    f'<span class="badge {badge_cls}">{badge_icon} {resume["status"]}</span>',
                    unsafe_allow_html=True,
                )
            with c3:
                score = resume.get('score')
                if score:
                    st.metric('Match', f'{score}%')
                else:
                    st.write('—')
            with c4:
                st.write(resume.get('model', '—'))
            with c5:
                actions_col = st.columns(2)
                with actions_col[0]:
                    if (
                        resume['status'] == 'Оптимизировано'
                        and st.button('📝', key=f'edit_{i}', help='Редактировать')
                    ):
                        st.session_state.page = 'editor'
                        st.rerun()
                with actions_col[1]:
                    if st.button('🗑️', key=f'del_{i}', help='Удалить'):
                        st.toast(f'Резюме «{resume["title"]}» удалено (демо)')
        st.divider()

    # ── Пагинация ──
    page_num = st.session_state.get('resumes_page', 1)
    pag1, p2, pag3 = st.columns([1, 2, 1])
    with pag1:
        if page_num > 1 and st.button('← Назад'):
            st.session_state.resumes_page = page_num - 1
            st.rerun()
    with p2:
        st.write(f'Страница {page_num}')
    with pag3:
        pass  # В демо только одна страница

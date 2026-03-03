"""ResumeCraft Streamlit Demo UI — для защиты ВКР (Phase 1).

Демонстрирует полный pipeline:
Upload (PDF/DOCX) → Parse → Match with Vacancy → AI Rewrite → Score → Export (DOCX)

Полное покрытие всех 20 прототипов:
  01 — Лендинг
  02-04 — Авторизация / Восстановление / Подтверждение email
  05 — Тарифы
  06 — Дашборд
  07 — Мои резюме
  08-12 — Wizard: загрузка → вакансия → модель → обработка → результаты
  13 — Редактор
  14 — Экспорт
  15 — История
  16-19 — Настройки (профиль, AI, подписка, безопасность)
  20 — Ошибка 404

Запуск:
    streamlit run streamlit_app/app.py
"""

from __future__ import annotations

import streamlit as st

from streamlit_app.pages import (
    auth,
    dashboard,
    editor,
    error,
    export,
    history,
    landing,
    pricing,
    resumes,
    settings,
    wizard,
)
from streamlit_app.styles import inject_css, render_logo

# ── Состояние сессии ────────────────────────────────────────────────────────

def _init_session_state() -> None:
    """Инициализация session_state для всех страниц."""
    defaults: dict[str, object] = {
        # Навигация
        'page': 'landing',
        'step': 0,               # Wizard step (0-4)
        'authenticated': False,
        # Пользователь
        'token': None,
        'user_email': None,
        'user_plan': 'Free',
        # Wizard данные
        'resume_id': None,
        'resume_text': None,
        'resume_filename': None,
        'vacancy_id': None,
        'vacancy_title': None,
        'vacancy_company': None,
        'vacancy_description': None,
        'model_name': 'gigachat-pro',
        'task_id': None,
        'result': None,
        # Режим
        'demo_mode': True,
        # Auth sub-views
        'auth_view': 'login',
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ── Боковое меню ────────────────────────────────────────────────────────────

def _render_sidebar() -> None:
    """Боковая панель навигации (зависит от auth-статуса)."""
    with st.sidebar:
        render_logo()
        st.caption('AI-реврайтер резюме')
        st.divider()

        if st.session_state.authenticated:
            _render_authenticated_nav()
        else:
            _render_guest_nav()

        st.divider()

        # Режим работы
        demo = st.toggle('Демо-режим', value=st.session_state.demo_mode)
        st.session_state.demo_mode = demo
        if demo:
            st.info('Работа без бэкенда — демо-данные', icon='ℹ️')


def _render_guest_nav() -> None:
    """Навигация для неавторизованных."""
    if st.button('🏠 Главная', use_container_width=True):
        st.session_state.page = 'landing'
        st.rerun()
    if st.button('💰 Тарифы', use_container_width=True):
        st.session_state.page = 'pricing'
        st.rerun()
    if st.button('🔑 Войти / Регистрация', use_container_width=True, type='primary'):
        st.session_state.page = 'auth'
        st.rerun()

    # Quick demo access
    st.divider()
    st.caption('Быстрый старт')
    if st.button('🎬 Демо (без входа)', use_container_width=True):
        st.session_state.authenticated = True
        st.session_state.user_email = 'demo@resumecraft.ru'
        st.session_state.page = 'dashboard'
        st.rerun()


def _render_authenticated_nav() -> None:
    """Навигация для авторизованных."""
    email = st.session_state.get('user_email', 'user')
    plan = st.session_state.get('user_plan', 'Free')
    st.markdown(f'**{email}**')
    st.caption(f'Тариф: {plan}')
    st.divider()

    nav_items = [
        ('📊', 'Дашборд', 'dashboard'),
        ('📄', 'Мои резюме', 'resumes'),
        ('🚀', 'Новая оптимизация', 'wizard'),
        ('📈', 'История', 'history'),
        ('💰', 'Тарифы', 'pricing'),
        ('⚙️', 'Настройки', 'settings'),
    ]

    current_page = st.session_state.get('page', 'dashboard')

    for icon, label, page_key in nav_items:
        btn_type = 'primary' if current_page == page_key else 'secondary'
        if st.button(f'{icon} {label}', key=f'nav_{page_key}',
                     use_container_width=True, type=btn_type):
            st.session_state.page = page_key
            if page_key == 'wizard':
                st.session_state.step = 0
            st.rerun()

    st.divider()
    if st.button('🚪 Выйти', use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.token = None
        st.session_state.user_email = None
        st.session_state.page = 'landing'
        st.rerun()


# ── Маршрутизация ───────────────────────────────────────────────────────────

_PAGE_MAP: dict[str, object] = {
    'landing': landing,
    'auth': auth,
    'pricing': pricing,
    'dashboard': dashboard,
    'resumes': resumes,
    'wizard': wizard,
    'editor': editor,
    'export': export,
    'history': history,
    'settings': settings,
    'error': error,
}


def _route() -> None:
    """Маршрутизация по session_state.page."""
    page_key = st.session_state.get('page', 'landing')

    # Redirect non-auth users from protected pages
    protected = {'dashboard', 'resumes', 'wizard', 'editor', 'export', 'history', 'settings'}
    if page_key in protected and not st.session_state.get('authenticated'):
        page_key = 'auth'
        st.session_state.page = 'auth'

    module = _PAGE_MAP.get(page_key)
    if module and hasattr(module, 'render'):
        module.render()  # type: ignore[union-attr]
    else:
        error.render()


# ── Main ────────────────────────────────────────────────────────────────────

def main() -> None:
    """Точка входа Streamlit-приложения."""
    st.set_page_config(
        page_title='ResumeCraft — AI-реврайтер резюме',
        page_icon='📄',
        layout='wide',
        initial_sidebar_state='expanded',
    )

    _init_session_state()
    inject_css()
    _render_sidebar()
    _route()


if __name__ == '__main__':
    main()

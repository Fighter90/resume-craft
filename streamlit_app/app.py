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
from streamlit_app.styles import inject_css

# ── Публичные / защищённые страницы ─────────────────────────────────────────

_PUBLIC_PAGES: frozenset[str] = frozenset({
    'landing', 'auth', 'pricing', 'error',
})

_PROTECTED_PAGES: frozenset[str] = frozenset({
    'dashboard', 'resumes', 'wizard', 'editor',
    'export', 'history', 'settings',
})


# ── Состояние сессии ────────────────────────────────────────────────────────

def _init_session_state() -> None:
    """Инициализация session_state для всех страниц."""
    defaults: dict[str, object] = {
        # Навигация
        'page': 'landing',
        'step': 0,
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


# ── Sidebar (только для авторизованных app-страниц) ─────────────────────────

def _render_app_sidebar() -> None:
    """Sidebar как в прототипе: 4 пункта + план + профиль пользователя."""
    with st.sidebar:
        # ── Логотип ──
        st.markdown("""
        <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:1.5rem;">
            <div style="width:36px;height:36px;background:linear-gradient(135deg,#4F46E5,#7C3AED);
                        border-radius:10px;display:flex;align-items:center;justify-content:center;">
                <span style="color:white;font-weight:700;font-size:1.1rem;">R</span>
            </div>
            <span style="font-weight:700;font-size:1.25rem;color:#111827;">ResumeCraft</span>
        </div>
        """, unsafe_allow_html=True)

        # ── Навигация (4 пункта как в прототипе) ──
        nav_items: list[tuple[str, str, str]] = [
            ('📊', 'Дашборд', 'dashboard'),
            ('📄', 'Мои резюме', 'resumes'),
            ('🕐', 'История', 'history'),
            ('⚙️', 'Настройки', 'settings'),
        ]

        current = st.session_state.get('page', 'dashboard')

        for icon, label, page_key in nav_items:
            is_active = current == page_key or (
                page_key == 'settings' and current == 'settings'
            )
            btn_type = 'primary' if is_active else 'secondary'
            if st.button(
                f'{icon} {label}',
                key=f'nav_{page_key}',
                use_container_width=True,
                type=btn_type,
            ):
                st.session_state.page = page_key
                st.rerun()

        st.divider()

        # ── Информация о тарифе (как plan-widget в прототипе) ──
        plan = st.session_state.get('user_plan', 'Free')
        used = 2
        total = 5 if plan == 'Free' else (30 if plan == 'Standard' else 999)
        plan_label = {
            'Free': 'Бесплатный план',
            'Standard': 'Standard план',
            'Pro': 'Pro план',
        }.get(plan, plan)
        st.caption(plan_label)
        st.progress(min(used / total, 1.0))
        st.caption(f'{used} / {total} оптимизаций')
        if plan == 'Free':
            if st.button('Обновить до Pro →', key='sidebar_upgrade',
                         use_container_width=True):
                st.session_state.page = 'settings'
                st.rerun()

        st.divider()

        # ── Профиль пользователя + выход ──
        email = st.session_state.get('user_email', 'user@example.com')
        name = email.split('@')[0].replace('.', ' ').title() if email else 'Пользователь'
        initials = ''.join(w[0].upper() for w in name.split()[:2])

        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.5rem;">
            <div style="width:36px;height:36px;background:linear-gradient(135deg,#4F46E5,#7C3AED);
                        border-radius:50%;display:flex;align-items:center;justify-content:center;
                        color:white;font-weight:600;font-size:0.85rem;">{initials}</div>
            <div>
                <div style="font-weight:600;font-size:0.9rem;color:#111827;">{name}</div>
                <div style="font-size:0.75rem;color:#6B7280;">{email}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button('🚪 Выйти', key='sidebar_logout', use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.token = None
            st.session_state.user_email = None
            st.session_state.page = 'landing'
            st.rerun()

        # ── Демо-режим ──
        st.divider()
        demo = st.toggle('Демо-режим', value=st.session_state.demo_mode,
                         key='sidebar_demo')
        st.session_state.demo_mode = demo
        if demo:
            st.info('Работа без бэкенда', icon='ℹ️')


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

    # Редирект неавторизованных с защищённых страниц
    if page_key in _PROTECTED_PAGES and not st.session_state.get('authenticated'):
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
        initial_sidebar_state='collapsed',
    )

    _init_session_state()
    inject_css()

    page_key = st.session_state.get('page', 'landing')

    # Sidebar только для авторизованных на app-страницах
    if st.session_state.get('authenticated') and page_key not in _PUBLIC_PAGES:
        _render_app_sidebar()

    _route()


if __name__ == '__main__':
    main()

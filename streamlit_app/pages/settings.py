"""Страницы 16-19: Настройки (Профиль, AI, Подписка, Безопасность).

Прототипы: 16-settings-profile.html, 17-settings-ai.html,
           18-settings-subscription.html, 19-settings-security.html
"""

from __future__ import annotations

import streamlit as st

from streamlit_app.demo_data import DEMO_PAYMENTS, DEMO_SESSIONS


def render() -> None:
    """Отрисовка страницы настроек с 4 табами."""
    st.title('Настройки')

    tab1, tab2, tab3, tab4 = st.tabs([
        '👤 Профиль', '🤖 AI-модели', '💳 Подписка', '🔒 Безопасность',
    ])

    with tab1:
        _render_profile()
    with tab2:
        _render_ai()
    with tab3:
        _render_subscription()
    with tab4:
        _render_security()


# ── Профиль (Prototype 16) ──

def _render_profile() -> None:
    """Настройки профиля."""
    st.subheader('Личная информация')

    with st.form('profile_form'):
        c1, c2 = st.columns(2)
        with c1:
            st.text_input('Имя', value='Александр', key='prof_name')
            st.text_input(
                'Email',
                value=st.session_state.get('user_email', 'a.ivanov@email.com'),
                key='prof_email',
            )
            st.text_input('Город', value='Москва', key='prof_city')
        with c2:
            st.text_input('Фамилия', value='Иванов', key='prof_lastname')
            st.text_input('Телефон', value='+7 (999) 123-45-67', key='prof_phone')
            st.selectbox(
                'Часовой пояс',
                ['Europe/Moscow', 'Europe/Kaliningrad', 'Asia/Yekaterinburg',
                 'Asia/Novosibirsk', 'Asia/Vladivostok'],
                key='prof_tz',
            )

        st.text_area(
            'О себе (краткое описание)',
            value='Product Manager с 5+ лет опыта',
            height=80,
            key='prof_about',
        )

        c_avatar, c_upload = st.columns([1, 3])
        with c_avatar:
            st.markdown("""
            <div style="width: 80px; height: 80px;
                        background: linear-gradient(
                        135deg, #4F46E5, #7C3AED);
                        border-radius: 50%; display: flex;
                        align-items: center;
                        justify-content: center;">
                <span style="color: white; font-size: 2rem; font-weight: 700;">А</span>
            </div>
            """, unsafe_allow_html=True)
        with c_upload:
            st.file_uploader('Загрузить фото', type=['jpg', 'png'], key='prof_avatar')

        if st.form_submit_button('Сохранить изменения', type='primary', use_container_width=True):
            st.success('Профиль обновлён (демо)')


# ── AI-модели (Prototype 17) ──

def _render_ai() -> None:
    """Настройки AI-моделей."""
    st.subheader('Параметры AI-оптимизации')

    # Модель по умолчанию
    st.selectbox(
        'AI-модель по умолчанию',
        ['GigaChat Pro (рекомендуем)', 'Llama 3.3 70B (Groq)', 'GPT-4o mini'],
        key='ai_default_model',
    )

    st.divider()
    st.subheader('Параметры оптимизации')

    toggles = [
        ('Добавлять ключевые слова', True, 'Автоматически добавлять ключевые слова из вакансии'),
        ('Адаптация для ATS', True, 'Оптимизировать структуру для ATS-систем'),
        ('Формула достижений', True, 'Использовать формулу Действие + Результат + Метрика'),
        ('Сохранять факты', True, 'Не выдумывать факты и достижения (рекомендуем)'),
        ('Краткое саммари', False, 'Добавить профессиональное саммари в начало'),
    ]

    for label, default, help_text in toggles:
        st.toggle(label, value=default, help=help_text, key=f'ai_{label}')

    st.divider()
    st.subheader('Расширенные настройки')

    c1, c2 = st.columns(2)
    with c1:
        st.slider(
            'Температура (креативность)', 0.0, 1.0, 0.3, 0.1,
            help='Низкая = точнее, высокая = креативнее',
            key='ai_temperature',
        )
    with c2:
        st.slider(
            'Макс. длина (токены)', 500, 4000, 2000, 100,
            key='ai_max_tokens',
        )

    st.selectbox(
        'Язык резюме',
        ['Русский', 'Английский', 'Авто-определение'],
        key='ai_language',
    )

    if st.button('Сохранить настройки AI', type='primary', use_container_width=True):
        st.success('Настройки AI сохранены (демо)')


# ── Подписка (Prototype 18) ──

def _render_subscription() -> None:
    """Настройки подписки и тарифа."""
    st.subheader('Текущий план')

    plan = st.session_state.get('user_plan', 'Free')
    used = 2
    total = 5 if plan == 'Free' else (30 if plan == 'Standard' else 999)

    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value" style="font-size: 1.5rem;">{plan}</div>
        <div class="stat-label">Текущий тариф</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<br>', unsafe_allow_html=True)

    # Usage
    st.write(f'**Использование:** {used}/{total} оптимизаций')
    st.progress(used / total if total > 0 else 0)
    st.caption('Обновление лимита: 1 апреля 2026')

    st.divider()

    # Plan comparison
    st.subheader('Сравнение планов')
    t1, t2, t3 = st.columns(3)
    plans = [
        ('Free', '0 ₽', '5 оптимизаций', plan == 'Free'),
        ('Standard', '490 ₽/мес', '30 оптимизаций', plan == 'Standard'),
        ('Pro', '1 490 ₽/мес', 'Безлимит', plan == 'Pro'),
    ]
    for col, (name, price, limit, is_current) in zip(
        [t1, t2, t3], plans, strict=True,
    ):
        with col:
            border = 'border: 2px solid #565ADD;' if is_current else ''
            badge = '<span class="badge badge-green">Текущий</span>' if is_current else ''
            st.markdown(f"""
            <div class="plan-card" style="{border}">
                {badge}
                <div style="font-weight: 700; font-size: 1.2rem;">{name}</div>
                <div style="font-size: 1.5rem; font-weight: 700;">{price}</div>
                <div style="color: #6B7280;">{limit}</div>
            </div>
            """, unsafe_allow_html=True)
            if not is_current:
                if st.button(f'Перейти на {name}', key=f'plan_{name}', use_container_width=True):
                    st.toast(f'Оплата тарифа {name} будет доступна в обновлении')
            else:
                st.button('Текущий план', disabled=True, key=f'plan_{name}',
                           use_container_width=True)

    # Payment history
    st.divider()
    st.subheader('История платежей')
    if DEMO_PAYMENTS:
        for payment in DEMO_PAYMENTS:
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                st.write(payment['description'])
            with c2:
                st.write(payment['date'])
            with c3:
                st.write(payment['amount'])
    else:
        st.info('Платежей пока нет')


# ── Безопасность (Prototype 19) ──

def _render_security() -> None:
    """Настройки безопасности."""
    # Change password
    st.subheader('Изменить пароль')
    with st.form('password_form'):
        st.text_input('Текущий пароль', type='password', key='sec_old_pass')
        st.text_input('Новый пароль', type='password', key='sec_new_pass')
        st.text_input('Подтвердите новый пароль', type='password', key='sec_confirm_pass')
        if st.form_submit_button('Обновить пароль', type='primary', use_container_width=True):
            st.success('Пароль обновлён (демо)')

    st.divider()

    # 2FA
    st.subheader('Двухфакторная аутентификация')
    twofa = st.toggle(
        'Включить 2FA',
        value=False,
        help='Дополнительная защита через SMS или TOTP-приложение',
        key='sec_2fa',
    )
    if twofa:
        st.info(
            'Настройка 2FA: отсканируйте QR-код '
            'в приложении (Google Authenticator, Яндекс.Ключ)',
        )
        st.markdown("""
        <div style="width: 150px; height: 150px; background: #F3F4F6; border-radius: 8px;
                    display: flex; align-items: center; justify-content: center;
                    color: #9CA3AF;">QR-код</div>
        """, unsafe_allow_html=True)

    st.divider()

    # Active sessions
    st.subheader('Активные сессии')
    for session in DEMO_SESSIONS:
        c1, c2, c3 = st.columns([3, 2, 1])
        with c1:
            icon = '💻' if 'macOS' in session.get('device', '') else (
                '📱' if 'iPhone' in session.get('device', '') else '🖥️'
            )
            current = ' (текущая)' if session.get('current') else ''
            st.write(f"{icon} **{session['device']}**{current}")
            st.caption(session.get('browser', ''))
        with c2:
            st.write(session.get('location', ''))
            st.caption(session.get('last_active', ''))
        with c3:
            if not session.get('current'):
                if st.button('Завершить', key=f"sess_{session.get('device', '')}"):
                    st.toast('Сессия завершена (демо)')
            else:
                st.write('✅')

    st.divider()

    # Danger zone
    st.subheader('Опасная зона')
    st.warning('Удаление аккаунта необратимо. Все данные, резюме и история будут удалены.')
    if st.button('🗑️ Удалить аккаунт', type='secondary'):
        st.session_state.show_delete_confirm = True

    if st.session_state.get('show_delete_confirm'):
        st.error('Вы уверены? Введите "УДАЛИТЬ" для подтверждения.')
        confirm = st.text_input('Подтверждение', key='delete_confirm_input')
        if confirm == 'УДАЛИТЬ' and st.button(
            'Подтвердить удаление', type='primary',
        ):
            st.session_state.authenticated = False
            st.session_state.page = 'landing'
            st.toast('Аккаунт удалён (демо)')
            st.rerun()

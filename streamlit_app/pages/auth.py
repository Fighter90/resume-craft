"""Страницы 02-04: Авторизация, восстановление пароля, подтверждение email.

Прототипы: 02-auth.html, 03-password-recovery.html, 04-email-verify.html.
"""

from __future__ import annotations

import streamlit as st

from streamlit_app.styles import render_top_navbar


def render() -> None:
    """Отрисовка страницы авторизации (login / register / recovery / verify)."""
    render_top_navbar()
    auth_view = st.session_state.get('auth_view', 'login')

    st.markdown("""
    <div style="max-width: 480px; margin: 0 auto;">
    """, unsafe_allow_html=True)

    if auth_view == 'recovery':
        _render_recovery()
    elif auth_view == 'verify':
        _render_verify()
    else:
        _render_login_register()

    st.markdown('</div>', unsafe_allow_html=True)


def _render_login_register() -> None:
    """Табы «Вход» / «Регистрация»."""
    st.markdown("""
    <div class="hero-section" style="padding: 2rem;">
        <h2>Добро пожаловать в ResumeCraft</h2>
        <p>Оптимизируйте резюме с помощью ИИ</p>
    </div>
    """, unsafe_allow_html=True)

    login_tab, register_tab = st.tabs(['Вход', 'Регистрация'])

    with login_tab:
        with st.form('login_form'):
            email = st.text_input('Email', placeholder='name@example.com')
            password = st.text_input('Пароль', type='password', placeholder='Минимум 8 символов')
            remember = st.checkbox('Запомнить меня')

            submitted = st.form_submit_button('Войти', type='primary', use_container_width=True)
            if submitted and email and password:
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.session_state.remember_me = remember
                st.session_state.page = 'dashboard'
                st.rerun()

        cols = st.columns(2)
        with cols[0]:
            if st.button('Забыли пароль?', use_container_width=True):
                st.session_state.auth_view = 'recovery'
                st.rerun()
        with cols[1]:
            pass  # Placeholder for social login

        st.divider()
        st.caption('Или войдите через')
        s1, s2 = st.columns(2)
        with s1:
            st.button('📧 Яндекс ID', use_container_width=True, disabled=True)
        with s2:
            st.button('💬 VK ID', use_container_width=True, disabled=True)

    with register_tab:
        with st.form('register_form'):
            full_name = st.text_input('Полное имя', placeholder='Иван Иванов')
            reg_email = st.text_input(
                'Email', placeholder='name@example.com', key='reg_email',
            )
            reg_password = st.text_input(
                'Пароль', type='password', placeholder='Минимум 8 символов', key='reg_pass',
            )
            reg_password2 = st.text_input(
                'Подтвердите пароль', type='password',
                placeholder='Повторите пароль', key='reg_pass2',
            )
            agree = st.checkbox(
                'Я соглашаюсь с [Условиями использования](/) '
                'и [Политикой конфиденциальности](/)',
            )
            submitted = st.form_submit_button(
                'Создать аккаунт', type='primary', use_container_width=True,
            )
            if submitted:
                errors: list[str] = []
                if not full_name:
                    errors.append('Укажите имя')
                if not reg_email:
                    errors.append('Укажите email')
                if len(reg_password) < 8:
                    errors.append('Пароль — минимум 8 символов')
                if reg_password != reg_password2:
                    errors.append('Пароли не совпадают')
                if not agree:
                    errors.append('Примите условия использования')
                if errors:
                    for e in errors:
                        st.error(e)
                else:
                    st.session_state.auth_view = 'verify'
                    st.session_state.verify_email = reg_email
                    st.rerun()

        st.divider()
        st.caption('Или зарегистрируйтесь через')
        s1, s2 = st.columns(2)
        with s1:
            st.button('📧 Яндекс ID', use_container_width=True, disabled=True, key='ya_reg')
        with s2:
            st.button('💬 VK ID', use_container_width=True, disabled=True, key='vk_reg')


def _render_recovery() -> None:
    """Восстановление пароля (Prototype 03)."""
    st.subheader('Восстановление пароля')
    st.write('Введите email, указанный при регистрации. Мы отправим ссылку.')

    with st.form('recovery_form'):
        email = st.text_input('Email', placeholder='name@example.com')
        submitted = st.form_submit_button(
            'Отправить ссылку', type='primary', use_container_width=True,
        )
        if submitted and email:
            st.success(f'Ссылка для сброса пароля отправлена на {email}')

    if st.button('← Вернуться к входу'):
        st.session_state.auth_view = 'login'
        st.rerun()


def _render_verify() -> None:
    """Подтверждение email после регистрации (Prototype 04)."""
    email = st.session_state.get('verify_email', 'user@example.com')

    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <div style="font-size: 4rem;">📧</div>
    </div>
    """, unsafe_allow_html=True)

    st.subheader('Проверьте почту')
    st.write(f'Мы отправили письмо для подтверждения на **{email}**')
    st.write('Нажмите на ссылку в письме, чтобы активировать аккаунт.')

    st.info('Если письмо не пришло, проверьте папку «Спам» или запросите повторную отправку.')

    c1, c2 = st.columns(2)
    with c1:
        if st.button('Отправить повторно', use_container_width=True):
            st.success('Письмо отправлено повторно')
    with c2:
        if st.button('Войти в аккаунт', type='primary', use_container_width=True):
            st.session_state.authenticated = True
            st.session_state.user_email = email
            st.session_state.auth_view = 'login'
            st.session_state.page = 'dashboard'
            st.rerun()

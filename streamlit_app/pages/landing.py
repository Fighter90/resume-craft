"""Страница 01: Лендинг (для неавторизованных пользователей).

Прототип: 01-landing.html
Hero-секция, возможности, как работает, тарифы, FAQ, CTA.
"""

from __future__ import annotations

import streamlit as st


def render() -> None:
    """Отрисовка лендинга."""
    # ── Hero ──
    st.markdown("""
    <div class="hero-section">
        <h1>Ваше резюме. Усиленное ИИ.</h1>
        <p>Оптимизируйте резюме под вакансию за 30 секунд.<br>
        AI анализирует требования и адаптирует контент для прохождения ATS-фильтров.</p>
        <div style="margin-top: 1.5rem; display: flex; gap: 1rem;
                    justify-content: center; flex-wrap: wrap;">
            <span style="background: rgba(255,255,255,0.15); padding: 0.5rem 1rem;
                        border-radius: 9999px; font-size: 0.9rem;">93 млн резюме на hh.ru</span>
            <span style="background: rgba(255,255,255,0.15); padding: 0.5rem 1rem;
                        border-radius: 9999px; font-size: 0.9rem;">Рейтинг 4.9/5</span>
            <span style="background: rgba(255,255,255,0.15); padding: 0.5rem 1rem;
                        border-radius: 9999px; font-size: 0.9rem;">30 сек оптимизация</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button('Оптимизировать резюме бесплатно', type='primary', use_container_width=True):
            st.session_state.page = 'auth'
            st.rerun()
    with c2:
        if st.button('Узнать подробнее', use_container_width=True):
            pass  # Scroll effect in HTML, skip in Streamlit

    # ── Проблема ──
    st.markdown('<br>', unsafe_allow_html=True)
    st.subheader('Почему резюме отклоняют?')
    p1, p2 = st.columns(2)
    with p1:
        st.markdown("""
        <div class="stat-card" style="text-align: center;">
            <div class="stat-value" style="color: #EF4444;">75%</div>
            <div class="stat-label">резюме отсеиваются ATS до HR</div>
        </div>
        """, unsafe_allow_html=True)
    with p2:
        st.markdown("""
        <div class="stat-card" style="text-align: center;">
            <div class="stat-value" style="color: #F59E0B;">5.9</div>
            <div class="stat-label">конкурентов на каждую вакансию</div>
        </div>
        """, unsafe_allow_html=True)

    st.info(
        'ATS-платформы (Huntflow, Потоk, Талантикс, Skillaz) автоматически '
        'фильтруют резюме по ключевым словам. Без правильных формулировок '
        'ваше резюме может не дойти до рекрутера.'
    )

    # ── Как это работает ──
    st.markdown('<br>', unsafe_allow_html=True)
    st.subheader('Как это работает')
    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown("""
        <div class="feature-card" style="text-align: center;">
            <div style="font-size: 2rem;">📄</div>
            <h3>1. Загрузите резюме</h3>
            <p>PDF или DOCX до 10 МБ, включая сканы с OCR</p>
        </div>
        """, unsafe_allow_html=True)
    with s2:
        st.markdown("""
        <div class="feature-card" style="text-align: center;">
            <div style="font-size: 2rem;">🎯</div>
            <h3>2. Выберите вакансию</h3>
            <p>Поиск hh.ru, вставка ссылки или ручной ввод</p>
        </div>
        """, unsafe_allow_html=True)
    with s3:
        st.markdown("""
        <div class="feature-card" style="text-align: center;">
            <div style="font-size: 2rem;">🚀</div>
            <h3>3. Получите результат</h3>
            <p>10-30 сек, сравнение до/после, экспорт DOCX/PDF</p>
        </div>
        """, unsafe_allow_html=True)

    # ── Возможности ──
    st.markdown('<br>', unsafe_allow_html=True)
    st.subheader('Возможности')
    features = [
        ('🤖', 'AI-рерайтинг',
         'Переформулировка с метриками: '
         'Действие + Результат + Метрика'),
        ('🔍', 'Интеграция с hh.ru',
         'Поиск вакансий, Match Score, вставка ссылки'),
        ('📊', 'Match Score',
         'Оценка 0-100%: Keywords 40%, Experience 25%, '
         'Structure 20%, Readability 15%'),
        ('🎯', 'ATS-оптимизация',
         'Адаптация для российских ATS: '
         'Huntflow, Потоk, Талантикс, Skillaz'),
        ('📁', 'Мультиформат',
         'PDF/DOCX/OCR на входе, PDF/DOCX на выходе; '
         '3 шаблона'),
        ('⚡', 'Выбор AI-модели',
         'GigaChat Pro, GPT-4o, Llama 3 + настройка'),
    ]
    f_cols = st.columns(3)
    for i, (icon, title, desc) in enumerate(features):
        with f_cols[i % 3]:
            st.markdown(f"""
            <div class="feature-card">
                <div style="font-size: 1.5rem;">{icon}</div>
                <h3>{title}</h3>
                <p>{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    # ── Для кого ──
    st.markdown('<br>', unsafe_allow_html=True)
    st.subheader('Для кого ResumeCraft')
    audiences = [
        ('🎓', 'Начинающие специалисты', 'Студенты и недавние выпускники'),
        ('💼', 'Опытные специалисты', 'Профессионалы с 5+ лет опыта'),
        ('🔄', 'Карьерные переходы', 'Смена отрасли или специализации'),
        ('💻', 'IT-специалисты', 'Разработчики, аналитики, менеджеры'),
    ]
    a_cols = st.columns(4)
    for i, (icon, title, desc) in enumerate(audiences):
        with a_cols[i]:
            st.markdown(f"""
            <div class="feature-card" style="text-align: center;">
                <div style="font-size: 2rem;">{icon}</div>
                <h3>{title}</h3>
                <p>{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    # ── Почему мы ──
    st.markdown('<br>', unsafe_allow_html=True)
    st.subheader('Почему ResumeCraft')
    usps = [
        ('🇷🇺', 'Русскоязычный AI', 'GigaChat #1 MERA'),
        ('🌐', 'Работает без VPN', 'Все серверы в РФ'),
        ('🔒', 'Данные в России', 'ФЗ-152 совместимость'),
        ('⚡', 'Результат за 10-30 сек', 'Мгновенная оптимизация'),
        ('✅', 'Гарантия достоверности', 'AI не выдумывает факты'),
        ('🔗', 'Интеграция с hh.ru', 'Единственный сервис с API'),
    ]
    u_cols = st.columns(3)
    for i, (icon, title, desc) in enumerate(usps):
        with u_cols[i % 3]:
            st.markdown(f"""
            <div class="feature-card" style="text-align: center;">
                <div style="font-size: 1.5rem;">{icon}</div>
                <h3>{title}</h3>
                <p>{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    # ── Тарифы (краткие) ──
    st.markdown('<br>', unsafe_allow_html=True)
    st.subheader('Тарифы')
    t1, t2, t3 = st.columns(3)
    with t1:
        st.markdown("""
        <div class="plan-card">
            <div class="badge badge-gray">Free</div>
            <div style="font-size: 2rem; font-weight: 700; margin: 0.5rem 0;">0 &#8381;</div>
            <div style="color: #6B7280;">5 оптимизаций/мес</div>
            <div style="color: #6B7280; font-size: 0.9rem;">Llama 3, DOCX</div>
        </div>
        """, unsafe_allow_html=True)
    with t2:
        st.markdown("""
        <div class="plan-card popular">
            <div class="badge badge-indigo">Standard &mdash; Популярный</div>
            <div style="font-size: 2rem; font-weight: 700;
                        margin: 0.5rem 0;">490 &#8381;/мес</div>
            <div style="color: #6B7280;">30 оптимизаций/мес</div>
            <div style="color: #6B7280; font-size: 0.9rem;">
                GigaChat Pro + Llama 3, PDF + DOCX</div>
        </div>
        """, unsafe_allow_html=True)
    with t3:
        st.markdown("""
        <div class="plan-card">
            <div class="badge badge-green">Pro</div>
            <div style="font-size: 2rem; font-weight: 700;
                        margin: 0.5rem 0;">1 490 &#8381;/мес</div>
            <div style="color: #6B7280;">Безлимит</div>
            <div style="color: #6B7280; font-size: 0.9rem;">
                Все модели, все форматы + hh.ru</div>
        </div>
        """, unsafe_allow_html=True)

    if st.button('Подробное сравнение тарифов', use_container_width=True):
        st.session_state.page = 'pricing'
        st.rerun()

    # ── FAQ ──
    st.markdown('<br>', unsafe_allow_html=True)
    st.subheader('Частые вопросы')
    with st.expander('Может ли AI добавить ложную информацию?'):
        st.write(
            'Нет. ResumeCraft перефразирует существующий опыт, '
            'но не выдумывает факты и достижения. '
            'Все данные основаны на вашем оригинальном резюме.'
        )
    with st.expander('Какие форматы файлов поддерживаются?'):
        st.write('На входе: PDF (включая сканы с OCR) и DOCX до 10 МБ. На выходе: DOCX и PDF.')
    with st.expander('В чём разница между AI-моделями?'):
        st.write(
            'GigaChat Pro (#1 для русского) — лучшее качество. '
            'Llama 3 (Groq) — быстрая и бесплатная. GPT-4o — резервная для англоязычного контента.'
        )
    with st.expander('Безопасность данных?'):
        st.write(
            'Данные хранятся в России (ФЗ-152). GigaChat обрабатывает данные в периметре Сбера. '
            'Вы можете удалить аккаунт и все данные в любой момент.'
        )
    with st.expander('Можно ли редактировать результат?'):
        st.write('Да, встроенный редактор позволяет изменить любую секцию перед экспортом.')
    with st.expander('Что такое Match Score?'):
        st.write(
            'Оценка соответствия резюме вакансии (0-100%): '
            'Keywords 40%, Experience 25%, Structure 20%, Readability 15%.'
        )

    # ── Финальный CTA ──
    st.markdown('<br>', unsafe_allow_html=True)
    st.markdown("""
    <div class="hero-section">
        <h1>Готовы получить работу мечты?</h1>
        <p>Оптимизируйте резюме бесплатно прямо сейчас</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button(
        'Начать бесплатно',
        type='primary',
        use_container_width=True,
        key='final_cta',
    ):
        st.session_state.page = 'auth'
        st.rerun()

    # ── Footer ──
    st.markdown('<br>', unsafe_allow_html=True)
    st.divider()
    st.caption(
        'ResumeCraft 2026. Данные хранятся в РФ (ФЗ-152). '
        'Поддержка: support@resumecraft.ru | Telegram: @resumecraft_support'
    )

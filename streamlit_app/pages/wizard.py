"""Страницы 08-12: Wizard — загрузка, вакансия, модель, обработка, результаты.

Прототипы: 08-upload.html, 09-vacancy.html, 10-models.html, 11-processing.html, 12-results.html
Рефакторинг существующего 5-шагового wizard из app.py с расширениями.
"""

from __future__ import annotations

import time
from uuid import uuid4

import streamlit as st

from streamlit_app.api_client import api_request
from streamlit_app.demo_data import (
    DEMO_OPTIMIZED,
    DEMO_RESUME_TEXT,
    DEMO_SCORES,
    DEMO_VACANCY,
)
from streamlit_app.styles import get_ats_color, get_badge_class, get_score_color


def render() -> None:
    """Отрисовка текущего шага wizard."""
    step = st.session_state.get('step', 0)
    steps_map = [
        _render_upload, _render_vacancy, _render_model,
        _render_processing, _render_results,
    ]
    if 0 <= step < len(steps_map):
        steps_map[step]()
    else:
        _render_upload()


def _render_wizard_sidebar() -> None:
    """Прогресс wizard в основной области (horizontal)."""
    step = st.session_state.get('step', 0)
    labels = ['📄 Загрузка', '🎯 Вакансия', '🤖 Модель', '⚡ Оптимизация', '📊 Результаты']
    cols = st.columns(len(labels))
    for i, (col, label) in enumerate(
        zip(cols, labels, strict=True),
    ):
        with col:
            if i < step:
                st.markdown(f'✅ ~~{label}~~')
            elif i == step:
                st.markdown(f'**{label}**')
            else:
                st.markdown(f'⬜ {label}')
    st.divider()


# ── Шаг 1: Загрузка ──

def _render_upload() -> None:
    """Шаг 1: Upload (Prototype 08)."""
    _render_wizard_sidebar()

    st.markdown("""
    <div class="hero-section">
        <h1>📄 Загрузите ваше резюме</h1>
        <p>Мы поддерживаем форматы PDF и DOCX до 10 МБ</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded = st.file_uploader(
            'Выберите файл резюме',
            type=['pdf', 'docx'],
            help='PDF, DOCX. Максимум 10 МБ. Сканы обрабатываются через OCR.',
        )

        if uploaded:
            st.session_state.resume_filename = uploaded.name
            file_size_mb = len(uploaded.getvalue()) / (1024 * 1024)
            ext = uploaded.name.rsplit('.', 1)[-1].upper()
            st.success(
                f'Файл загружен: **{uploaded.name}** '
                f'({file_size_mb:.1f} МБ, {ext})',
                icon='✅',
            )

            if st.session_state.get('demo_mode', True):
                st.session_state.resume_text = DEMO_RESUME_TEXT
                st.session_state.resume_id = str(uuid4())
            else:
                data = api_request('POST', '/resumes/upload', files={
                    'file': (uploaded.name, uploaded.getvalue(), uploaded.type),
                })
                if data:
                    st.session_state.resume_id = data['id']
                    st.session_state.resume_text = data.get('raw_text', '')

            if st.session_state.get('resume_id') and st.button(
                'Далее → Выбор вакансии',
                type='primary', use_container_width=True,
            ):
                st.session_state.step = 1
                st.rerun()

        st.divider()
        if st.button('🎬 Загрузить демо-резюме', use_container_width=True):
            st.session_state.resume_text = DEMO_RESUME_TEXT
            st.session_state.resume_id = str(uuid4())
            st.session_state.resume_filename = 'demo_resume.pdf'
            st.session_state.step = 1
            st.rerun()

    with col2:
        st.markdown('### 💡 Советы')
        st.markdown("""
        - Используйте **актуальное** резюме
        - PDF с текстовым слоем — лучший результат
        - Сканы обрабатываются OCR (качество ниже)
        - Максимум: 10 МБ
        """)

        st.markdown('### 📊 Поддерживаемые форматы')
        st.markdown("""
        | Формат | Тип |
        |--------|-----|
        | PDF | Текст + OCR |
        | DOCX | Полный текст |
        """)


# ── Шаг 2: Вакансия ──

def _render_vacancy() -> None:
    """Шаг 2: Vacancy (Prototype 09)."""
    _render_wizard_sidebar()

    st.markdown("""
    <div class="hero-section">
        <h1>🎯 Выберите целевую вакансию</h1>
        <p>Укажите вакансию для оптимизации резюме</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(['🔍 Поиск hh.ru', '🔗 Вставить URL', '✏️ Ввести вручную'])

    with tab1:
        if st.session_state.get('demo_mode', True):
            st.info('В демо-режиме поиск hh.ru недоступен. Используйте демо-вакансию.')
            if st.button(
                '📋 Демо-вакансия: Senior PM @ Яндекс',
                use_container_width=True,
            ):
                _set_demo_vacancy()
                st.session_state.step = 2
                st.rerun()
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                search_text = st.text_input('Должность', placeholder='Product Manager')
            with c2:
                _city = st.selectbox(
                    'Город',
                    ['Москва', 'Санкт-Петербург', 'Удалённо', 'Другой'],
                )
            with c3:
                _experience = st.selectbox(
                    'Опыт', ['Любой', 'Нет опыта', '1-3 года', '3-6 лет', '6+ лет'],
                )

            fc1, fc2 = st.columns(2)
            with fc1:
                _salary_from = st.number_input(
                    'Зарплата от', min_value=0, step=10000, value=0,
                )
            with fc2:
                _salary_to = st.number_input(
                    'Зарплата до', min_value=0, step=10000, value=0,
                )

            if st.button('Найти', type='primary'):
                data = api_request('GET', '/vacancies/search', json_data={
                    'text': search_text,
                })
                if data and data.get('items'):
                    for item in data['items'][:6]:
                        with st.container():
                            st.markdown(f"**{item['title']}** @ {item.get('company', 'N/A')}")
                            if st.button('Выбрать', key=f"vac_{item.get('id', '')}"):
                                st.session_state.vacancy_id = item['id']
                                st.session_state.vacancy_title = item['title']
                                st.session_state.step = 2
                                st.rerun()

    with tab2:
        url = st.text_input(
            'Ссылка на вакансию hh.ru', placeholder='https://hh.ru/vacancy/12345678',
        )
        if url and st.button('Загрузить вакансию', type='primary'):
            if st.session_state.get('demo_mode', True):
                _set_demo_vacancy()
                st.session_state.step = 2
                st.rerun()
            else:
                data = api_request('POST', '/vacancies/from-url', json_data={'url': url})
                if data:
                    st.session_state.vacancy_id = data['id']
                    st.session_state.vacancy_title = data['title']
                    st.session_state.step = 2
                    st.rerun()

    with tab3, st.form('manual_vacancy'):
        title = st.text_input('Название должности *', placeholder='Senior Product Manager')
        company = st.text_input('Компания', placeholder='Яндекс')
        description = st.text_area(
            'Описание и требования *', height=200,
            placeholder='Опишите требования, навыки, обязанности...',
        )
        skills = st.text_input(
            'Ключевые навыки (через запятую)',
            placeholder='Product Strategy, A/B Testing, SQL, Agile',
        )

        if st.form_submit_button(
            'Далее → Выбор модели', type='primary', use_container_width=True,
        ):
            if not title or not description:
                st.error('Заполните обязательные поля')
            else:
                if st.session_state.get('demo_mode', True):
                    st.session_state.vacancy_id = str(uuid4())
                else:
                    data = api_request('POST', '/vacancies/manual', json_data={
                        'title': title,
                        'company': company,
                        'description': description,
                        'key_skills': (
                            [s.strip() for s in skills.split(',') if s.strip()] if skills else []
                        ),
                    })
                    if data:
                        st.session_state.vacancy_id = data['id']

                st.session_state.vacancy_title = title
                st.session_state.vacancy_company = company
                st.session_state.vacancy_description = description
                st.session_state.step = 2
                st.rerun()

    st.divider()
    if st.button('← Назад к загрузке'):
        st.session_state.step = 0
        st.rerun()


def _set_demo_vacancy() -> None:
    """Установить демо-вакансию в session_state."""
    st.session_state.vacancy_title = DEMO_VACANCY['title']
    st.session_state.vacancy_company = DEMO_VACANCY['company']
    st.session_state.vacancy_description = DEMO_VACANCY['description']
    st.session_state.vacancy_id = str(uuid4())


# ── Шаг 3: Модель ──

def _render_model() -> None:
    """Шаг 3: Model selection (Prototype 10)."""
    _render_wizard_sidebar()

    st.markdown("""
    <div class="hero-section">
        <h1>🤖 Выберите AI-модель</h1>
        <p>Различные модели подходят для разных задач</p>
    </div>
    """, unsafe_allow_html=True)

    models = [
        {
            'name': 'gigachat-pro',
            'display': 'GigaChat Pro',
            'provider': 'Сбер',
            'description': '#1 MERA для русского языка. Лучшее качество.',
            'speed': '10–20 сек',
            'quality': 95,
            'icon': '🇷🇺',
            'recommended': True,
            'plan': 'Standard+',
        },
        {
            'name': 'groq',
            'display': 'Llama 3.3 70B (Groq)',
            'provider': 'Meta / Groq',
            'description': 'Быстрая бесплатная модель. IT-резюме.',
            'speed': '5–10 сек',
            'quality': 80,
            'icon': '🦙',
            'recommended': False,
            'plan': 'Free',
        },
        {
            'name': 'openai',
            'display': 'GPT-4o mini',
            'provider': 'OpenAI',
            'description': 'Резервная. Хороша для английского.',
            'speed': '10–15 сек',
            'quality': 85,
            'icon': '🧠',
            'recommended': False,
            'plan': 'Pro',
        },
    ]

    cols = st.columns(len(models))
    for col, model in zip(cols, models, strict=True):
        with col:
            badge = ' 🏆' if model['recommended'] else ''
            plan_badge = f'<span class="badge badge-indigo">{model["plan"]}</span>'

            st.markdown(f"""
            <div class="feature-card" style="text-align: left; position: relative;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 2rem;">{model['icon']}</span>
                    {plan_badge}
                </div>
                <div style="font-weight: 700; font-size: 1.1rem; margin: 0.5rem 0;">
                    {model['display']}{badge}
                </div>
                <div style="color: #6B7280; font-size: 0.85rem; margin-bottom: 0.5rem;">
                    {model['provider']}
                </div>
                <div style="font-size: 0.9rem; margin-bottom: 0.75rem;">
                    {model['description']}
                </div>
                <div style="font-size: 0.85rem; margin-bottom: 0.5rem;">
                    ⚡ {model['speed']}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Quality progress bar
            st.caption(f"Качество: {model['quality']}%")
            st.progress(model['quality'] / 100)

            btn_type = 'primary' if model['recommended'] else 'secondary'
            btn_label = '✓ Выбрать (рекомендуем)' if model['recommended'] else 'Выбрать'
            if st.button(btn_label, key=f"model_{model['name']}", type=btn_type,
                         use_container_width=True):
                st.session_state.model_name = model['name']
                st.session_state.step = 3
                st.rerun()

    st.divider()
    if st.button('← Назад к вакансии'):
        st.session_state.step = 1
        st.rerun()


# ── Шаг 4: Обработка ──

def _render_processing() -> None:
    """Шаг 4: Processing (Prototype 11) — 8-step pipeline."""
    _render_wizard_sidebar()

    model_display = st.session_state.get('model_name', 'gigachat-pro').replace('-', ' ').title()

    st.markdown(f"""
    <div class="hero-section" style="text-align: center;">
        <h1>⚡ Оптимизируем ваше резюме...</h1>
        <p>{model_display} анализирует и адаптирует контент</p>
    </div>
    """, unsafe_allow_html=True)

    # 8-step pipeline (Prototype 11)
    pipeline_steps = [
        ('📄', 'Извлечение текста', 'Парсинг PDF/DOCX'),
        ('🔍', 'Анализ вакансии', 'Извлечение ключевых требований'),
        ('📊', 'Gap-анализ', 'Сравнение навыков и требований'),
        ('📋', 'Стратегия', 'Планирование оптимизации'),
        ('🤖', 'AI-рерайтинг', f'{model_display} адаптирует контент'),
        ('✅', 'Валидация', 'Проверка достоверности и ATS'),
        ('📈', 'Скоринг', 'Расчёт Match Score'),
        ('🏁', 'Финализация', 'Форматирование и проверка'),
    ]

    progress_bar = st.progress(0)
    step_list = st.empty()

    if st.session_state.get('demo_mode', True):
        for i, (_icon, _title, _desc) in enumerate(pipeline_steps):
            pct = int((i + 1) / len(pipeline_steps) * 100)
            progress_bar.progress(pct)

            steps_html = ''
            for j, (_s_icon, s_title, s_desc) in enumerate(pipeline_steps):
                if j < i:
                    steps_html += f'<div class="step-done">✅ {s_title} — {s_desc}</div>'
                elif j == i:
                    steps_html += f'<div class="step-active">⏳ {s_title} — {s_desc}</div>'
                else:
                    steps_html += f'<div class="step-pending">⬜ {s_title}</div>'

            step_list.markdown(f"""
            <div class="progress-section">
                <div style="margin-bottom: 0.5rem; color: #6B7280; font-size: 0.85rem;">
                    Шаг {i + 1} из {len(pipeline_steps)}
                    · ETA ~{max(1, (len(pipeline_steps) - i - 1) * 2)} сек
                </div>
                {steps_html}
            </div>
            """, unsafe_allow_html=True)

            time.sleep(1.0)

        progress_bar.progress(100)
        st.session_state.result = {**DEMO_SCORES, 'optimized': DEMO_OPTIMIZED}
        st.balloons()
        time.sleep(0.5)
        st.session_state.step = 4
        st.rerun()
    else:
        data = api_request('POST', '/rewrite', json_data={
            'resume_id': st.session_state.get('resume_id'),
            'vacancy_id': st.session_state.get('vacancy_id'),
            'model': st.session_state.get('model_name'),
        })
        if data:
            task_id = data['task_id']
            while True:
                status = api_request('GET', f'/rewrite/{task_id}/status')
                if not status:
                    break
                progress_bar.progress(status.get('progress', 0))
                if status.get('status') in ('completed', 'failed'):
                    break
                time.sleep(2)

            result = api_request('GET', f'/rewrite/{task_id}/result')
            if result:
                st.session_state.result = result
                st.session_state.step = 4
                st.rerun()


# ── Шаг 5: Результаты ──

def _render_results() -> None:
    """Шаг 5: Results (Prototype 12)."""
    _render_wizard_sidebar()

    result = st.session_state.get('result')
    if not result:
        st.error('Результаты не найдены')
        return

    vacancy = st.session_state.get('vacancy_title', 'Вакансия')
    company = st.session_state.get('vacancy_company', '')
    company_str = f' @ {company}' if company else ''

    st.markdown(f"""
    <div class="hero-section">
        <h1>📊 Результаты оптимизации</h1>
        <p>{vacancy}{company_str}</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Score карточки ──
    score_before = result.get('match_score_before', 53)
    score_after = result.get('match_score_after', 87)
    improvement = score_after - score_before
    ats = result.get('ats_rating', 'A+')
    keywords_added = result.get('optimized', {}).get('keywords_added', [])
    model = result.get('model_name', 'GigaChat Pro')

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        color = get_score_color(score_after)
        badge_cls = get_badge_class(score_after)
        st.markdown(f"""
        <div class="stat-card" style="text-align: center;">
            <div class="stat-label">Match Score</div>
            <div class="stat-value" style="color: {color};">{score_after:.0f}%</div>
            <div class="badge {badge_cls}">+{improvement:.0f}% улучшение</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        ats_color = get_ats_color(ats)
        st.markdown(f"""
        <div class="stat-card" style="text-align: center;">
            <div class="stat-label">ATS совместимость</div>
            <div class="stat-value" style="color: {ats_color};">{ats}</div>
            <div class="badge badge-green">Все секции оптимальны</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        kw_count = len(keywords_added)
        st.markdown(f"""
        <div class="stat-card" style="text-align: center;">
            <div class="stat-label">Ключевые слова</div>
            <div class="stat-value" style="color: #565ADD;">{kw_count}</div>
            <div class="badge badge-green">+{kw_count} добавлено</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="stat-card" style="text-align: center;">
            <div class="stat-label">AI модель</div>
            <div class="stat-value" style="font-size: 1.5rem;">{model}</div>
            <div class="badge badge-indigo">⚡ Основная</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<br>', unsafe_allow_html=True)

    # ── Разбивка Match Score ──
    st.subheader('Разбивка Match Score')
    components = [
        ('Ключевые слова', result.get('keywords', {}).get('weight', 40),
         result.get('keywords', {}).get('score', 92)),
        ('Опыт', result.get('experience', {}).get('weight', 25),
         result.get('experience', {}).get('score', 85)),
        ('Структура', result.get('structure', {}).get('weight', 20),
         result.get('structure', {}).get('score', 80)),
        ('Читаемость', result.get('readability', {}).get('weight', 15),
         result.get('readability', {}).get('score', 88)),
    ]

    for label, weight, score in components:
        cl, cb, cv = st.columns([2, 5, 1])
        with cl:
            st.markdown(f'**{label}** ({weight}%)')
        with cb:
            st.progress(score / 100)
        with cv:
            color = get_score_color(score)
            st.markdown(
                f'<span style="color: {color}; font-weight: 600;">{score}%</span>',
                unsafe_allow_html=True,
            )

    st.markdown('<br>', unsafe_allow_html=True)

    # ── Diff сравнение ──
    st.subheader('Сравнение: Оригинал → Оптимизировано')
    col_orig, col_opt = st.columns(2)

    with col_orig:
        st.markdown(f"""
        <div style="background: white; border-radius: 12px; padding: 1.5rem;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                <strong>Оригинал</strong>
                <span class="badge badge-red">{score_before:.0f}%</span>
            </div>
            <div style="font-size: 0.9rem; line-height: 1.6; color: #374151;">
                {st.session_state.get('resume_text', 'Текст оригинала')}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_opt:
        optimized = result.get('optimized', {})
        if isinstance(optimized, dict):
            summary = optimized.get('summary', '')
            experience_list = optimized.get('experience', [])
            skills_list = optimized.get('skills', [])

            exp_html = ''
            for exp in experience_list[:2]:
                achievements = ''.join(f'<li>{a}</li>' for a in exp.get('achievements', []))
                exp_html += f"""
                <div style="margin-bottom: 1rem;">
                    <strong>{exp.get('position', '')}</strong> — {exp.get('company', '')}
                    <span style="color: #6B7280;">({exp.get('period', '')})</span>
                    <ul style="margin: 0.25rem 0; padding-left: 1.25rem;">{achievements}</ul>
                </div>
                """

            skills_html = ', '.join(
                f'<span class="diff-improved">{s}</span>' for s in skills_list[:10]
            )

            st.markdown(f"""
            <div style="background: white; border-radius: 12px; padding: 1.5rem;
                        border-left: 3px solid #10B981;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                    <strong>Оптимизировано</strong>
                    <span class="badge badge-green">{score_after:.0f}%</span>
                </div>
                <div style="font-size: 0.9rem; line-height: 1.6; color: #374151;">
                    <p><span class="diff-improved">{summary}</span></p>
                    {exp_html}
                    <p><strong>Навыки:</strong> {skills_html}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<br>', unsafe_allow_html=True)

    # ── Ключевые слова ──
    if keywords_added:
        st.subheader('Добавленные ключевые слова')
        kw_html = ''.join(f'<span class="keyword-pill">{kw}</span>' for kw in keywords_added)
        st.markdown(f'<div>{kw_html}</div>', unsafe_allow_html=True)

    st.markdown('<br>', unsafe_allow_html=True)

    # ── Действия ──
    ca, cb, cc, cd = st.columns(4)
    with ca:
        if st.button('✏️ Редактировать', use_container_width=True):
            st.session_state.page = 'editor'
            st.rerun()
    with cb:
        if st.button('📥 Экспорт', type='primary', use_container_width=True):
            st.session_state.page = 'export'
            st.rerun()
    with cc:
        if st.button('📋 Сохранить', use_container_width=True):
            st.toast('Результат сохранён в историю')
    with cd:
        if st.button('🔄 Новая оптимизация', use_container_width=True):
            for key in ['resume_id', 'resume_text', 'vacancy_id', 'vacancy_title',
                        'vacancy_company', 'vacancy_description', 'task_id', 'result']:
                st.session_state[key] = None
            st.session_state.step = 0
            st.rerun()

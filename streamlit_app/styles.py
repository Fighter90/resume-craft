"""ResumeCraft Streamlit Demo UI — общие стили и утилиты.

Содержит CSS, цветовую схему и вспомогательные функции,
используемые всеми страницами приложения.
"""

from __future__ import annotations

import streamlit as st

# ── Цветовая схема (из прототипов) ─────────────────────────────────────────
COLORS = {
    'primary': '#565ADD',
    'primary_hover': '#4338CA',
    'primary_light': '#EEF2FF',
    'success': '#10B981',
    'success_light': '#D1FAE5',
    'danger': '#EF4444',
    'danger_light': '#FEE2E2',
    'warning': '#F59E0B',
    'warning_light': '#FEF3C7',
    'bg_body': '#F3F4F6',
    'bg_card': '#FFFFFF',
    'text_main': '#111827',
    'text_secondary': '#6B7280',
}


def get_score_color(score: float) -> str:
    """Цвет по значению оценки: >=80 зелёный, >=60 жёлтый, <60 красный."""
    if score >= 80:
        return COLORS['success']
    if score >= 60:
        return COLORS['warning']
    return COLORS['danger']


def get_badge_class(score: float) -> str:
    """CSS-класс бейджа по оценке."""
    if score >= 80:
        return 'badge-green'
    if score >= 60:
        return 'badge-yellow'
    return 'badge-red'


def get_ats_color(rating: str) -> str:
    """Цвет ATS-рейтинга."""
    if rating in ('A+', 'A'):
        return COLORS['success']
    if rating in ('B+', 'B'):
        return COLORS['warning']
    return COLORS['danger']


def inject_css() -> None:
    """Кастомные стили для приближения к прототипу."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    .stApp { font-family: 'Inter', sans-serif; }
    /* Скрыть стандартное Streamlit меню и футер */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* ── Top Navbar (лендинг / публичные страницы) ── */
    .top-navbar {
        display: flex; align-items: center; justify-content: space-between;
        padding: 0.75rem 2rem; background: white;
        border-bottom: 1px solid #E5E7EB; margin: -1rem -1rem 1.5rem -1rem;
        position: sticky; top: 0; z-index: 999;
    }
    .top-navbar .logo {
        display: flex; align-items: center; gap: 0.5rem;
        font-weight: 700; font-size: 1.25rem; color: #111827;
        cursor: pointer; text-decoration: none;
    }
    .top-navbar .logo-icon {
        width: 28px; height: 28px;
        background: linear-gradient(135deg, #4F46E5, #7C3AED);
        border-radius: 6px; display: flex; align-items: center; justify-content: center;
        color: white; font-weight: 700; font-size: 0.85rem;
    }
    .top-navbar .nav-actions { display: flex; gap: 0.75rem; align-items: center; }
    .top-navbar .nav-btn {
        padding: 0.5rem 1.25rem; border-radius: 8px; font-size: 0.9rem;
        font-weight: 500; cursor: pointer; text-decoration: none; display: inline-block;
        border: none; transition: all 0.15s;
    }
    .nav-btn-secondary {
        background: #F3F4F6; color: #374151;
    }
    .nav-btn-secondary:hover { background: #E5E7EB; }
    .nav-btn-primary {
        background: linear-gradient(135deg, #4F46E5, #7C3AED);
        color: white;
    }
    .nav-btn-primary:hover { opacity: 0.9; }

    /* ── Общие карточки и компоненты ── */
    .main-header {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
        padding: 2rem; border-radius: 20px; color: white; margin-bottom: 1.5rem;
    }
    .main-header h1 { color: white; margin: 0; font-size: 2rem; }
    .main-header p { color: rgba(255,255,255,0.85); margin: 0.5rem 0 0 0; }
    .score-card {
        background: white; border-radius: 16px; padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; height: 100%;
    }
    .score-card .value {
        font-size: 2.5rem; font-weight: 700; line-height: 1; margin: 0.5rem 0;
    }
    .score-card .label { font-size: 0.85rem; color: #6B7280; margin-bottom: 0.25rem; }
    .score-card .badge {
        display: inline-block; padding: 0.2rem 0.75rem; border-radius: 9999px;
        font-size: 0.75rem; font-weight: 600;
    }
    .badge-green { background: #D1FAE5; color: #059669; }
    .badge-yellow { background: #FEF3C7; color: #D97706; }
    .badge-red { background: #FEE2E2; color: #DC2626; }
    .badge-indigo { background: #EEF2FF; color: #4F46E5; }
    .badge-gray { background: #F3F4F6; color: #6B7280; }
    .keyword-pill {
        display: inline-block; padding: 0.3rem 0.75rem; border-radius: 9999px;
        font-size: 0.8rem; font-weight: 500; margin: 0.2rem;
        background: #DCFCE7; color: #166534;
    }
    .diff-original { background: #FEE2E2; padding: 0.2rem 0.4rem; border-radius: 4px; }
    .diff-improved { background: #DCFCE7; padding: 0.2rem 0.4rem; border-radius: 4px; }
    .step-active { color: #4F46E5; font-weight: 600; }
    .step-done { color: #10B981; }
    .step-pending { color: #9CA3AF; }
    .progress-section {
        background: white; border-radius: 16px; padding: 2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .stat-card {
        background: white; border-radius: 16px; padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .stat-card .stat-value { font-size: 2rem; font-weight: 700; color: #111827; }
    .stat-card .stat-label { font-size: 0.85rem; color: #6B7280; }
    .resume-card {
        background: white; border-radius: 16px; padding: 1.25rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 0.75rem;
    }
    .timeline-item {
        border-left: 2px solid #E5E7EB; padding-left: 1.5rem;
        padding-bottom: 1.5rem; margin-left: 0.5rem; position: relative;
    }
    .timeline-item::before {
        content: ''; position: absolute; left: -6px; top: 4px;
        width: 10px; height: 10px; border-radius: 50%;
        background: #4F46E5; border: 2px solid white;
    }
    .timeline-item.success::before { background: #10B981; }
    .timeline-item.info::before { background: #3B82F6; }
    .plan-card {
        background: white; border-radius: 16px; padding: 2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center;
    }
    .plan-card.popular { border: 2px solid #4F46E5; }
    .settings-section {
        background: white; border-radius: 16px; padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 1rem;
    }
    .hero-section {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
        padding: 4rem 2rem; border-radius: 20px; color: white;
        text-align: center; margin-bottom: 2rem;
    }
    .hero-section h1 { color: white; font-size: 2.5rem; margin-bottom: 0.5rem; }
    .hero-section p { color: rgba(255,255,255,0.85); font-size: 1.1rem; }
    .feature-card {
        background: white; border-radius: 16px; padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1); height: 100%;
    }
    .feature-card h3 { font-size: 1rem; margin: 0.75rem 0 0.5rem 0; }
    .feature-card p { font-size: 0.9rem; color: #6B7280; }
    </style>
    """, unsafe_allow_html=True)


def render_logo() -> None:
    """Логотип ResumeCraft."""
    st.markdown("""
    <div style="display: flex; align-items: center;
                gap: 0.75rem; margin-bottom: 2rem;">
        <div style="width: 36px; height: 36px;
                    background: linear-gradient(135deg, #4F46E5, #7C3AED);
                    border-radius: 10px; display: flex;
                    align-items: center;
                    justify-content: center;">
            <span style="color: white; font-weight: 700; font-size: 1.1rem;">R</span>
        </div>
        <span style="font-weight: 700; font-size: 1.25rem; color: #111827;">ResumeCraft</span>
    </div>
    """, unsafe_allow_html=True)


def render_top_navbar() -> None:
    """Top navbar для публичных страниц (лендинг, auth, pricing, error).

    Как в прототипе 01-landing.html: логотип + кнопки Войти / Начать бесплатно.
    Навигация происходит через Streamlit session_state.
    """
    st.markdown("""
    <div class="top-navbar">
        <div class="logo">
            <div class="logo-icon">R</div>
            ResumeCraft
        </div>
        <div class="nav-actions" id="top-nav-actions"></div>
    </div>
    """, unsafe_allow_html=True)

    # Streamlit-кнопки для навигации (рендерим в одну строку)
    cols = st.columns([6, 1, 1, 1])
    with cols[1]:
        if st.button('💰 Тарифы', key='topnav_pricing', use_container_width=True):
            st.session_state.page = 'pricing'
            st.rerun()
    with cols[2]:
        if st.button('🔑 Войти', key='topnav_login', use_container_width=True):
            st.session_state.page = 'auth'
            st.rerun()
    with cols[3]:
        if st.button('🚀 Начать', key='topnav_start', type='primary',
                     use_container_width=True):
            st.session_state.page = 'auth'
            st.rerun()

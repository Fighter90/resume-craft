/* ============================================
   ResumeCraft Shared Navigation v2.0
   Inserts sidebar, mobile header, bottom nav, dev nav
   ============================================ */

const SCREENS = [
    { id: 'index', file: 'index.html', label: 'Хаб', group: 'nav' },
    { id: 'landing', file: '01-landing.html', label: 'Лендинг', group: 'public' },
    { id: 'auth', file: '02-auth.html', label: 'Авторизация', group: 'public' },
    { id: 'password-recovery', file: '03-password-recovery.html', label: 'Восстановление', group: 'public' },
    { id: 'email-verify', file: '04-email-verify.html', label: 'Верификация', group: 'public' },
    { id: 'pricing', file: '05-pricing.html', label: 'Тарифы', group: 'public' },
    { id: 'dashboard', file: '06-dashboard.html', label: 'Дашборд', group: 'app' },
    { id: 'resumes', file: '07-resumes.html', label: 'Мои резюме', group: 'app' },
    { id: 'upload', file: '08-upload.html', label: 'Загрузка', group: 'app' },
    { id: 'vacancy', file: '09-vacancy.html', label: 'Вакансия', group: 'app' },
    { id: 'models', file: '10-models.html', label: 'AI модели', group: 'app' },
    { id: 'processing', file: '11-processing.html', label: 'Обработка', group: 'app' },
    { id: 'results', file: '12-results.html', label: 'Результаты', group: 'app' },
    { id: 'editor', file: '13-editor.html', label: 'Редактор', group: 'app' },
    { id: 'export', file: '14-export.html', label: 'Экспорт', group: 'app' },
    { id: 'history', file: '15-history.html', label: 'История', group: 'app' },
    { id: 'settings-profile', file: '16-settings-profile.html', label: 'Профиль', group: 'settings' },
    { id: 'settings-ai', file: '17-settings-ai.html', label: 'AI модель', group: 'settings' },
    { id: 'settings-sub', file: '18-settings-subscription.html', label: 'Подписка', group: 'settings' },
    { id: 'settings-security', file: '19-settings-security.html', label: 'Безопасность', group: 'settings' },
    { id: 'error-404', file: '20-error-404.html', label: '404', group: 'public' },
];

const SIDEBAR_NAV_ITEMS = [
    { icon: 'grid', label: 'Дашборд', file: '06-dashboard.html', id: 'dashboard' },
    { icon: 'file-text', label: 'Мои резюме', file: '07-resumes.html', id: 'resumes' },
    { icon: 'clock', label: 'История', file: '15-history.html', id: 'history' },
    { icon: 'help', label: 'Справка', file: '#', id: 'help' },
    { icon: 'settings', label: 'Настройки', file: '16-settings-profile.html', id: 'settings' },
];

const ICONS = {
    grid: `<svg class="icon-sm" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>`,
    'file-text': `<svg class="icon-sm" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>`,
    clock: `<svg class="icon-sm" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`,
    settings: `<svg class="icon-sm" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9c.26.604.852.997 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>`,
    home: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`,
    plus: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>`,
    doc: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>`,
    help: `<svg class="icon-sm" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
};

function getCurrentPageId() {
    const filename = window.location.pathname.split('/').pop();
    const screen = SCREENS.find(s => s.file === filename);
    return screen ? screen.id : '';
}

function buildSidebar(activeId) {
    const navItems = SIDEBAR_NAV_ITEMS.map(item => {
        const isActive = activeId === item.id || (activeId.startsWith('settings') && item.id === 'settings');
        return `<a href="${item.file}" class="nav-item${isActive ? ' active' : ''}">${ICONS[item.icon]} ${item.label}</a>`;
    }).join('');

    return `
    <div class="sidebar-overlay" onclick="closeSidebar()"></div>
    <aside class="sidebar" id="sidebar">
        <div class="sidebar-logo">
            <div class="sidebar-logo-icon">
                ${ICONS.doc}
            </div>
            <span>ResumeCraft</span>
        </div>
        <nav class="sidebar-nav">${navItems}</nav>
        <div class="sidebar-footer">
            <div class="plan-widget">
                <div class="plan-name">Бесплатный план</div>
                <div class="plan-bar"><div class="plan-bar-fill" style="width:40%"></div></div>
                <div class="plan-usage">2 / 5 оптимизаций</div>
                <a href="18-settings-subscription.html" class="plan-upgrade">Обновить до Pro &rarr;</a>
            </div>
            <div class="user-profile">
                <div class="user-avatar">АП</div>
                <div class="user-info">
                    <div class="user-name">Александр Петров</div>
                    <div class="user-email">alex@example.com</div>
                </div>
            </div>
        </div>
    </aside>`;
}

function buildMobileHeader(title) {
    return `
    <div class="mobile-header">
        <button class="hamburger" onclick="toggleSidebar()">
            <span></span><span></span><span></span>
        </button>
        <span style="font-weight:700;font-size:1rem;">${title || 'ResumeCraft'}</span>
        <div style="width:40px"></div>
    </div>`;
}

function buildBottomNav(activeId) {
    const items = [
        { icon: ICONS.home, label: 'Главная', file: '06-dashboard.html', id: 'dashboard' },
        { icon: ICONS['file-text'], label: 'Резюме', file: '07-resumes.html', id: 'resumes' },
        { icon: ICONS.plus, label: 'Загрузить', file: '08-upload.html', id: 'upload' },
        { icon: ICONS.clock, label: 'История', file: '15-history.html', id: 'history' },
        { icon: ICONS.settings, label: 'Настройки', file: '16-settings-profile.html', id: 'settings' },
    ];
    const btns = items.map(item => {
        const isActive = activeId === item.id || (activeId.startsWith('settings') && item.id === 'settings');
        return `<a href="${item.file}" class="bottom-nav-item${isActive ? ' active' : ''}">${item.icon}<span>${item.label}</span></a>`;
    }).join('');
    return `<nav class="bottom-nav"><div class="bottom-nav-inner">${btns}</div></nav>`;
}

function buildDevNav() {
    const currentId = getCurrentPageId();
    const links = SCREENS.map(s => {
        const cls = s.id === currentId ? ' current' : '';
        return `<a href="${s.file}" class="${cls}">${s.label}</a>`;
    }).join('');
    return `<div class="dev-nav">${links}</div>`;
}

// Inject dev nav on all pages
document.addEventListener('DOMContentLoaded', () => {
    document.body.insertAdjacentHTML('beforeend', buildDevNav());
});

function toggleSidebar() {
    document.getElementById('sidebar')?.classList.toggle('open');
    document.querySelector('.sidebar-overlay')?.classList.toggle('visible');
}
function closeSidebar() {
    document.getElementById('sidebar')?.classList.remove('open');
    document.querySelector('.sidebar-overlay')?.classList.remove('visible');
}

// Toggle switch handler
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('toggle-switch')) {
        e.target.classList.toggle('on');
    }
});

import { Outlet, NavLink, useLocation, useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { LayoutGrid, FileText, Clock, Settings, File, Menu, X, Home, Plus, LogOut, User, ChevronUp, HelpCircle } from 'lucide-react'
import { useState, useRef, useEffect } from 'react'

const NAV_ITEMS = [
  { to: '/app/dashboard', icon: LayoutGrid, label: 'Дашборд', id: 'dashboard' },
  { to: '/app/resumes', icon: FileText, label: 'Мои резюме', id: 'resumes' },
  { to: '/app/history', icon: Clock, label: 'История', id: 'history' },
  { to: '/app/help', icon: HelpCircle, label: 'Справка', id: 'help' },
  { to: '/app/settings', icon: Settings, label: 'Настройки', id: 'settings' },
]

const BOTTOM_NAV = [
  { to: '/app/dashboard', icon: Home, label: 'Главная' },
  { to: '/app/resumes', icon: FileText, label: 'Резюме' },
  { to: '/app/upload', icon: Plus, label: 'Загрузить' },
  { to: '/app/history', icon: Clock, label: 'История' },
  { to: '/app/settings', icon: Settings, label: 'Настройки' },
]

export default function AppLayout() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [profileMenuOpen, setProfileMenuOpen] = useState(false)
  const profileRef = useRef<HTMLDivElement>(null)

  const isActive = (id: string) => {
    if (id === 'settings') return location.pathname.startsWith('/app/settings')
    return location.pathname.startsWith(`/app/${id}`)
  }

  const initials = user?.full_name
    ? user.full_name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
    : user?.email?.[0]?.toUpperCase() || 'U'

  // Close profile menu on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setProfileMenuOpen(false)
      }
    }
    if (profileMenuOpen) document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [profileMenuOpen])

  const handleLogout = () => {
    logout()
    setProfileMenuOpen(false)
    navigate('/auth')
  }

  return (
    <div className="app-shell">
      {/* Sidebar overlay (mobile) */}
      {sidebarOpen && (
        <div className="sidebar-overlay visible" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={`sidebar${sidebarOpen ? ' open' : ''}`} id="sidebar">
        <Link to="/app/dashboard" className="sidebar-logo" style={{ textDecoration: 'none', color: 'inherit' }}>
          <div className="sidebar-logo-icon">
            <File size={16} />
          </div>
          <span>ResumeCraft</span>
        </Link>

        <nav className="sidebar-nav">
          {NAV_ITEMS.map(item => (
            <NavLink
              key={item.id}
              to={item.to}
              className={() => `nav-item${isActive(item.id) ? ' active' : ''}`}
              onClick={() => setSidebarOpen(false)}
            >
              <item.icon size={16} />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="plan-widget">
            <div className="plan-name">
              {user?.plan === 'pro' ? 'Pro план' : user?.plan === 'standard' ? 'Standard план' : 'Бесплатный план'}
            </div>
            <div className="plan-bar">
              <div className="plan-bar-fill" style={{ width: `${user?.plan === 'pro' ? 100 : Math.min((user?.optimizations_used || 0) / (user?.plan === 'standard' ? 30 : 5) * 100, 100)}%` }} />
            </div>
            <div className="plan-usage">
              {user?.plan === 'pro' ? 'Безлимит' : `${user?.optimizations_used || 0} / ${user?.plan === 'standard' ? 30 : 5} оптимизаций`}
            </div>
            {user?.plan !== 'pro' && (
              <Link
                to="/app/settings/subscription"
                className="plan-upgrade"
                onClick={(e) => {
                  e.preventDefault()
                  e.stopPropagation()
                  setSidebarOpen(false)
                  navigate('/app/settings/subscription')
                }}
              >
                Обновить до Pro →
              </Link>
            )}
          </div>

          {/* User profile with dropdown */}
          <div ref={profileRef} style={{ position: 'relative' }}>
            {profileMenuOpen && (
              <div style={{
                position: 'absolute', bottom: '100%', left: 0, right: 0,
                marginBottom: 8, background: 'var(--card-bg, #fff)',
                borderRadius: 12, boxShadow: '0 4px 24px rgba(0,0,0,0.12)',
                border: '1px solid var(--border)', overflow: 'hidden', zIndex: 100,
              }}>
                <button
                  onClick={() => { setProfileMenuOpen(false); navigate('/app/settings/profile'); setSidebarOpen(false) }}
                  className="profile-menu-btn"
                  style={{
                    display: 'flex', alignItems: 'center', gap: '0.75rem', width: '100%',
                    padding: '0.75rem 1rem', background: 'none', border: 'none',
                    cursor: 'pointer', fontSize: '0.875rem', color: 'var(--text-primary)',
                  }}
                >
                  <User size={16} /> Профиль
                </button>
                <div style={{ height: 1, background: 'var(--border)' }} />
                <button
                  onClick={handleLogout}
                  className="profile-menu-btn"
                  style={{
                    display: 'flex', alignItems: 'center', gap: '0.75rem', width: '100%',
                    padding: '0.75rem 1rem', background: 'none', border: 'none',
                    cursor: 'pointer', fontSize: '0.875rem', color: '#EF4444',
                  }}
                >
                  <LogOut size={16} /> Выйти
                </button>
              </div>
            )}
            <div
              className="user-profile"
              onClick={() => setProfileMenuOpen(!profileMenuOpen)}
              style={{ cursor: 'pointer' }}
              role="button"
              tabIndex={0}
              aria-label="Меню профиля"
              onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') setProfileMenuOpen(!profileMenuOpen) }}
            >
              <div className="user-avatar">{initials}</div>
              <div className="user-info">
                <div className="user-name">{user?.full_name || 'Пользователь'}</div>
                <div className="user-email">{user?.email || 'demo@resumecraft.ru'}</div>
              </div>
              <ChevronUp size={16} style={{
                marginLeft: 'auto', color: 'var(--text-secondary)', transition: 'transform 0.2s',
                transform: profileMenuOpen ? 'rotate(0deg)' : 'rotate(180deg)',
              }} />
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="main-content">
        {/* Mobile header */}
        <div className="mobile-header">
          <button className="hamburger" onClick={() => setSidebarOpen(!sidebarOpen)}>
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          <Link to="/app/dashboard" style={{ fontWeight: 700, fontSize: '1rem', textDecoration: 'none', color: 'inherit' }}>ResumeCraft</Link>
          <div style={{ width: 40 }} />
        </div>

        <div className="view">
          <Outlet />
        </div>

        {/* Bottom nav (mobile) */}
        <nav className="bottom-nav">
          <div className="bottom-nav-inner">
            {BOTTOM_NAV.map(item => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive: active }) => `bottom-nav-item${active ? ' active' : ''}`}
                onClick={() => setSidebarOpen(false)}
              >
                <item.icon size={22} />
                <span>{item.label}</span>
              </NavLink>
            ))}
          </div>
        </nav>
      </div>
    </div>
  )
}

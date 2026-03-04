import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { LayoutGrid, FileText, Clock, Settings, File, Menu, X, Home, Plus } from 'lucide-react'
import { useState } from 'react'

const NAV_ITEMS = [
  { to: '/app/dashboard', icon: LayoutGrid, label: 'Дашборд', id: 'dashboard' },
  { to: '/app/resumes', icon: FileText, label: 'Мои резюме', id: 'resumes' },
  { to: '/app/history', icon: Clock, label: 'История', id: 'history' },
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
  const { user } = useAuth()
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const isActive = (id: string) => {
    if (id === 'settings') return location.pathname.startsWith('/app/settings')
    return location.pathname.startsWith(`/app/${id}`)
  }

  const initials = user?.full_name
    ? user.full_name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
    : user?.email?.[0]?.toUpperCase() || 'U'

  return (
    <div className="app-shell">
      {/* Sidebar overlay (mobile) */}
      {sidebarOpen && (
        <div className="sidebar-overlay visible" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={`sidebar${sidebarOpen ? ' open' : ''}`} id="sidebar">
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">
            <File size={16} />
          </div>
          <span>ResumeCraft</span>
        </div>

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
              <div className="plan-bar-fill" style={{ width: `${Math.min((user?.optimizations_used || 0) / 5 * 100, 100)}%` }} />
            </div>
            <div className="plan-usage">{user?.optimizations_used || 0} / 5 оптимизаций</div>
            <NavLink to="/app/settings/subscription" className="plan-upgrade">Обновить до Pro →</NavLink>
          </div>
          <div className="user-profile">
            <div className="user-avatar">{initials}</div>
            <div className="user-info">
              <div className="user-name">{user?.full_name || 'Пользователь'}</div>
              <div className="user-email">{user?.email}</div>
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
          <span style={{ fontWeight: 700, fontSize: '1rem' }}>ResumeCraft</span>
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

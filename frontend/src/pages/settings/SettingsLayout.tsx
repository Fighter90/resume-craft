import { NavLink, Outlet, useLocation, Navigate } from 'react-router-dom'
import { User, Cpu, CreditCard, Shield } from 'lucide-react'

const TABS = [
  { to: '/app/settings/profile', icon: User, label: 'Профиль' },
  { to: '/app/settings/ai', icon: Cpu, label: 'AI-модели' },
  { to: '/app/settings/subscription', icon: CreditCard, label: 'Подписка' },
  { to: '/app/settings/security', icon: Shield, label: 'Безопасность' },
]

export default function SettingsLayout() {
  const location = useLocation()

  if (location.pathname === '/app/settings') {
    return <Navigate to="/app/settings/profile" replace />
  }

  return (
    <div>
      <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '1.5rem' }}>Настройки</h2>

      <div className="tab-bar" style={{ marginBottom: '2rem' }}>
        {TABS.map(t => (
          <NavLink
            key={t.to}
            to={t.to}
            className={({ isActive }) => `tab-bar-item${isActive ? ' active' : ''}`}
            style={{ textDecoration: 'none' }}
          >
            <t.icon size={16} /> {t.label}
          </NavLink>
        ))}
      </div>

      <Outlet />
    </div>
  )
}

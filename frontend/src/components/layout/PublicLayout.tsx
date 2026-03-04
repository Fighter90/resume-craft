import { Outlet, Link } from 'react-router-dom'
import { File } from 'lucide-react'

export default function PublicLayout() {
  return (
    <div className="landing-page">
      <nav className="landing-nav">
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            width: 28, height: 28,
            background: 'var(--primary-gradient)', borderRadius: 8,
            display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white'
          }}>
            <File size={14} />
          </div>
          <span style={{ fontWeight: 700, fontSize: '1.25rem' }}>ResumeCraft</span>
        </Link>
        <div className="landing-nav-actions">
          <Link to="/auth" className="btn btn-secondary btn-sm">Войти</Link>
          <Link to="/auth?tab=register" className="btn btn-primary btn-sm">Начать бесплатно</Link>
        </div>
      </nav>
      <Outlet />
    </div>
  )
}

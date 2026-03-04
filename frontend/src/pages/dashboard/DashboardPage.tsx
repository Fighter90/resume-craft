import { Link } from 'react-router-dom'
import { FileText, BarChart3, TrendingUp, Plus } from 'lucide-react'
import { DEMO_RESUMES } from '../../data/demo'
import { useAuth } from '../../contexts/AuthContext'

export default function DashboardPage() {
  const { user } = useAuth()
  const displayName = user?.full_name?.split(' ')[0] || 'Пользователь'

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Добрый день, {displayName}</h1>
          <p>Управляйте резюме и отслеживайте результаты</p>
        </div>
        <Link to="/app/upload" className="btn btn-primary">Оптимизировать резюме</Link>
      </div>

      {/* Stats */}
      <div className="stats-grid">
        <div className="card stat-card">
          <div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Всего резюме</div>
            <div style={{ fontSize: '2rem', fontWeight: 700 }}>12</div>
          </div>
          <div className="stat-icon" style={{ background: 'var(--primary-light)', color: 'var(--primary)' }}>
            <FileText size={24} />
          </div>
        </div>
        <div className="card stat-card">
          <div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Оптимизаций</div>
            <div style={{ fontSize: '2rem', fontWeight: 700 }}>48</div>
          </div>
          <div className="stat-icon" style={{ background: 'var(--success-light)', color: 'var(--success)' }}>
            <TrendingUp size={24} />
          </div>
        </div>
        <div className="card stat-card">
          <div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Средний Match Score</div>
            <div style={{ fontSize: '2rem', fontWeight: 700 }}>78%</div>
          </div>
          <div className="stat-icon" style={{ background: '#FEF3C7', color: '#D97706' }}>
            <BarChart3 size={24} />
          </div>
        </div>
      </div>

      {/* Recent Resumes */}
      <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1rem' }}>Недавние резюме</h2>
      <div className="resume-grid">
        {DEMO_RESUMES.slice(0, 2).map(r => (
          <Link to={`/app/results/${r.id}`} key={r.id} className="card card-hover" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>{r.title}</h3>
              <span className={`badge ${r.status === 'optimized' ? 'badge-green' : 'badge-gray'}`}>
                {r.status === 'optimized' ? 'Optimized' : 'Draft'}
              </span>
            </div>
            {r.match_score && (
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--success)', marginBottom: '0.5rem' }}>
                {r.match_score}% <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 400 }}>Match Score</span>
              </div>
            )}
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              {r.tags.map(t => <span key={t} className="badge badge-indigo">{t}</span>)}
            </div>
          </Link>
        ))}
        {/* New resume card */}
        <Link to="/app/upload" className="card" style={{
          padding: '1.5rem', border: '2px dashed #E5E7EB', display: 'flex',
          alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '0.75rem',
          color: 'var(--text-secondary)', cursor: 'pointer', minHeight: 150
        }}>
          <Plus size={32} />
          <span style={{ fontWeight: 500 }}>Создать новое</span>
        </Link>
      </div>
    </>
  )
}

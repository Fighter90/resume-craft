import { Link } from 'react-router-dom'
import { FileText, BarChart3, TrendingUp, Plus, Loader } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { useEffect, useState } from 'react'
import { api } from '../../services/api'

/* eslint-disable @typescript-eslint/no-explicit-any */

export default function DashboardPage() {
  const { user } = useAuth()
  const displayName = user?.full_name?.split(' ')[0] || 'Пользователь'
  const [resumes, setResumes] = useState<any[]>([])
  const [history, setHistory] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const [resumeRes, historyRes] = await Promise.all([
          api.getResumes().catch(() => []),
          api.getRewriteHistory().catch(() => []),
        ])
        setResumes(Array.isArray(resumeRes) ? resumeRes : [])
        setHistory(Array.isArray(historyRes) ? historyRes : [])
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const totalResumes = resumes.length
  const totalOptimizations = history.length
  const scored = history.filter((h: any) => h.match_score_after != null && h.match_score_after > 0)
  const avgScore = scored.length > 0
    ? Math.round(scored.reduce((acc: number, h: any) => acc + h.match_score_after, 0) / scored.length)
    : 0

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Добрый день, {displayName}</h1>
          <p>Готовы получить оффер мечты сегодня?</p>
        </div>
        <Link to="/app/upload" className="btn btn-primary"><Plus size={16} /> Оптимизировать резюме</Link>
      </div>

      {/* Stats */}
      <div className="stats-grid">
        <div className="card stat-card">
          <div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Загружено резюме</div>
            <div style={{ fontSize: '2rem', fontWeight: 700 }}>{loading ? '—' : totalResumes}</div>
          </div>
          <div className="stat-icon" style={{ background: 'var(--primary-light)', color: 'var(--primary)' }}>
            <FileText size={24} />
          </div>
        </div>
        <div className="card stat-card">
          <div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Оптимизаций</div>
            <div style={{ fontSize: '2rem', fontWeight: 700 }}>{loading ? '—' : totalOptimizations}</div>
          </div>
          <div className="stat-icon" style={{ background: 'var(--success-light)', color: 'var(--success)' }}>
            <TrendingUp size={24} />
          </div>
        </div>
        <div className="card stat-card">
          <div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Средний Match Score</div>
            <div style={{ position: 'relative', width: 56, height: 56, margin: '0.25rem 0' }}>
              <svg viewBox="0 0 36 36" style={{ width: '100%', height: '100%', transform: 'rotate(-90deg)' }}>
                <path d="M18 2.0845a15.9155 15.9155 0 0 1 0 31.831a15.9155 15.9155 0 0 1 0-31.831" fill="none" stroke="#E5E7EB" strokeWidth="3" />
                <path d="M18 2.0845a15.9155 15.9155 0 0 1 0 31.831a15.9155 15.9155 0 0 1 0-31.831" fill="none" stroke="#D97706" strokeWidth="3" strokeDasharray={`${avgScore},100`} />
              </svg>
              <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.85rem', fontWeight: 700, color: '#D97706' }}>{loading ? '—' : `${avgScore}%`}</div>
            </div>
          </div>
          <div className="stat-icon" style={{ background: '#FEF3C7', color: '#D97706' }}>
            <BarChart3 size={24} />
          </div>
        </div>
      </div>

      {/* Recent Resumes */}
      <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1rem' }}>Недавние резюме</h2>
      <div className="resume-grid">
        {loading ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)' }}><Loader size={16} className="spin" /> Загрузка...</div>
        ) : resumes.slice(0, 2).map((r: any) => (
          <Link to="/app/resumes" key={r.id} className="card card-hover" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>{r.title || 'Резюме'}</h3>
              <span className={`badge ${r.status === 'optimized' ? 'badge-green' : 'badge-gray'}`}>
                {r.status === 'optimized' ? 'Оптимизировано' : r.status === 'processing' ? 'В обработке' : 'Черновик'}
              </span>
            </div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              {r.file_format?.toUpperCase()} · {r.created_at ? new Date(r.created_at).toLocaleDateString('ru-RU') : ''}
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

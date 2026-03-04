import { useNavigate } from 'react-router-dom'
import { ArrowRight, Download, TrendingUp, Target, Award, Tag } from 'lucide-react'
import { DEMO_SCORES, DEMO_KEYWORDS, DEMO_ORIGINAL_TEXT, DEMO_OPTIMIZED_TEXT } from '../../data/demo'

export default function ResultsPage() {
  const navigate = useNavigate()
  const score = DEMO_SCORES.matchScore
  const radius = 54
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference

  return (
    <div>
      {/* Top score section */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        {/* Main score */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '1.5rem' }}>
          <svg width={128} height={128} viewBox="0 0 128 128" className="score-circle">
            <circle cx="64" cy="64" r={radius} fill="none" stroke="var(--border)" strokeWidth="10" />
            <circle
              cx="64" cy="64" r={radius} fill="none"
              stroke="url(#scoreGrad)" strokeWidth="10" strokeLinecap="round"
              strokeDasharray={circumference} strokeDashoffset={offset}
              transform="rotate(-90 64 64)"
            />
            <defs>
              <linearGradient id="scoreGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="var(--primary)" />
                <stop offset="100%" stopColor="#7C3AED" />
              </linearGradient>
            </defs>
            <text x="64" y="60" textAnchor="middle" fontSize="28" fontWeight="700" fill="var(--text-primary)">{score}</text>
            <text x="64" y="78" textAnchor="middle" fontSize="11" fill="var(--text-secondary)">Match Score</text>
          </svg>
          <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem' }}>
            <span className="badge badge-green">ATS: {DEMO_SCORES.atsRating}</span>
            <span className="badge badge-indigo">+{DEMO_SCORES.improvement} пунктов</span>
          </div>
        </div>

        {/* Metrics */}
        {[
          { icon: Target, label: 'Ключевые слова', value: DEMO_SCORES.breakdown.keywords, color: 'var(--primary)' },
          { icon: TrendingUp, label: 'Опыт', value: DEMO_SCORES.breakdown.experience, color: 'var(--success)' },
          { icon: Award, label: 'Структура', value: DEMO_SCORES.breakdown.structure, color: 'var(--info)' },
        ].map((m, i) => (
          <div key={i} className="card" style={{ padding: '1.25rem' }}>
            <m.icon size={20} style={{ color: m.color, marginBottom: '0.5rem' }} />
            <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{m.value}%</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{m.label}</div>
            <div className="progress-bar" style={{ marginTop: '0.5rem' }}>
              <div className="progress-fill" style={{ width: `${m.value}%`, background: m.color }} />
            </div>
          </div>
        ))}
      </div>

      {/* Keywords */}
      <div className="card" style={{ padding: '1.25rem', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <Tag size={16} />
          <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Добавленные ключевые слова</h3>
          <span className="badge badge-indigo">{DEMO_KEYWORDS.length}</span>
        </div>
        <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
          {DEMO_KEYWORDS.map((kw, i) => (
            <span key={kw} className={`badge ${i < 6 ? 'badge-green' : i < 12 ? 'badge-indigo' : 'badge-yellow'}`}>
              {kw}
            </span>
          ))}
        </div>
      </div>

      {/* Diff comparison */}
      <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>Сравнение версий</h3>
      <div className="diff-container">
        <div className="diff-panel">
          <div className="diff-header">
            <span style={{ fontWeight: 600 }}>Оригинал</span>
            <span className="badge badge-gray">{DEMO_ORIGINAL_TEXT.score} баллов</span>
          </div>
          <div className="diff-content" style={{ whiteSpace: 'pre-wrap', fontSize: '0.85rem', lineHeight: 1.7, padding: '1rem' }}>
            <strong>{DEMO_ORIGINAL_TEXT.position}</strong>{'\n\n'}
            {DEMO_ORIGINAL_TEXT.summary}{'\n\n'}
            {DEMO_ORIGINAL_TEXT.experience}
          </div>
        </div>
        <div className="diff-panel">
          <div className="diff-header">
            <span style={{ fontWeight: 600 }}>Оптимизировано</span>
            <span className="badge badge-green">{DEMO_OPTIMIZED_TEXT.score} баллов</span>
          </div>
          <div className="diff-content" style={{ whiteSpace: 'pre-wrap', fontSize: '0.85rem', lineHeight: 1.7, padding: '1rem' }}>
            <strong>{DEMO_OPTIMIZED_TEXT.position}</strong>{'\n\n'}
            {DEMO_OPTIMIZED_TEXT.summary}{'\n\n'}
            {DEMO_OPTIMIZED_TEXT.experience}
          </div>
        </div>
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
        <button onClick={() => navigate('/app/editor')} className="btn btn-primary" style={{ flex: 1 }}>
          Редактировать <ArrowRight size={16} />
        </button>
        <button onClick={() => navigate('/app/export')} className="btn btn-secondary" style={{ flex: 1 }}>
          <Download size={16} /> Экспорт
        </button>
      </div>
    </div>
  )
}

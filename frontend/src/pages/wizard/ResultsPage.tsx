import { useNavigate, useParams } from 'react-router-dom'
import { ArrowRight, Download, TrendingUp, Target, Award, Tag, BookOpen, Cpu, Edit } from 'lucide-react'
import { DEMO_SCORES, DEMO_KEYWORDS, DEMO_ORIGINAL_TEXT, DEMO_OPTIMIZED_TEXT, DEMO_RESUMES } from '../../data/demo'

export default function ResultsPage() {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const resume = id ? DEMO_RESUMES.find(r => r.id === id) : null
  const score = DEMO_SCORES.matchScore
  const radius = 54
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference

  return (
    <div>
      {/* Page header — matches prototype */}
      <div className="page-header">
        <div>
          <h1>Результаты оптимизации</h1>
          <p>{resume ? `${resume.title} — ${resume.vacancy || 'Черновик'}` : 'Senior Product Manager @ Яндекс'}</p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button onClick={() => navigate('/app/editor')} className="btn btn-secondary">
            <Edit size={16} /> Редактировать
          </button>
          <button onClick={() => navigate('/app/export')} className="btn btn-primary">
            <Download size={16} /> Экспорт
          </button>
        </div>
      </div>

      {/* Score cards — 4 cards like prototype */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        {/* Main Match Score */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '1.5rem' }}>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Match Score</div>
          <svg width={100} height={100} viewBox="0 0 128 128" className="score-circle">
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
            <text x="64" y="78" textAnchor="middle" fontSize="11" fill="var(--text-secondary)">%</text>
          </svg>
          <div style={{ marginTop: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.85rem', color: 'var(--success)', fontWeight: 600 }}>
            <TrendingUp size={14} />
            +{DEMO_SCORES.improvement} пунктов
          </div>
        </div>

        {/* ATS card — separate like prototype */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '1.5rem' }}>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>ATS совместимость</div>
          <div style={{
            width: 64, height: 64, borderRadius: 16, display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '1.75rem', fontWeight: 700, color: 'var(--success)',
            background: 'rgba(16,185,129,0.1)', marginBottom: '0.5rem',
          }}>
            {DEMO_SCORES.atsRating}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Отлично</div>
        </div>

        {/* AI Model card — matches prototype */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '1.5rem' }}>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>AI-модель</div>
          <div style={{
            width: 64, height: 64, borderRadius: 16, display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: 'rgba(86,90,221,0.1)', marginBottom: '0.5rem',
          }}>
            <Cpu size={28} style={{ color: 'var(--primary)' }} />
          </div>
          <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>GigaChat Pro</div>
        </div>

        {/* Processing time */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '1.5rem' }}>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Время обработки</div>
          <div style={{ fontSize: '2rem', fontWeight: 700 }}>12<span style={{ fontSize: '1rem', fontWeight: 400, color: 'var(--text-secondary)' }}> сек</span></div>
        </div>
      </div>

      {/* Metrics breakdown — 4 components per prototype (Keywords 40% + Experience 25% + Structure 20% + Readability 15%) */}
      <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>Компоненты Match Score</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        {[
          { icon: Target, label: 'Ключевые слова', value: DEMO_SCORES.breakdown.keywords, weight: '40%', color: 'var(--primary)' },
          { icon: TrendingUp, label: 'Опыт', value: DEMO_SCORES.breakdown.experience, weight: '25%', color: 'var(--success)' },
          { icon: Award, label: 'Структура', value: DEMO_SCORES.breakdown.structure, weight: '20%', color: 'var(--info)' },
          { icon: BookOpen, label: 'Читаемость', value: 88, weight: '15%', color: '#D97706' },
        ].map((m, i) => (
          <div key={i} className="card" style={{ padding: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <m.icon size={20} style={{ color: m.color }} />
              <span className="badge badge-gray">{m.weight}</span>
            </div>
            <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{m.value}%</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>{m.label}</div>
            <div className="progress-bar">
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
          {DEMO_KEYWORDS.map(kw => (
            <span key={kw} className="badge badge-green">{kw}</span>
          ))}
        </div>
      </div>

      {/* Diff comparison with highlighting */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Сравнение версий</h3>
        <div style={{ display: 'flex', gap: '1rem', fontSize: '0.8rem' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span style={{ width: 12, height: 12, borderRadius: 3, background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)' }} />
            Слабые формулировки
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span style={{ width: 12, height: 12, borderRadius: 3, background: 'rgba(16,185,129,0.15)', border: '1px solid rgba(16,185,129,0.3)' }} />
            Улучшения AI
          </span>
        </div>
      </div>
      <div className="diff-container">
        <div className="diff-panel">
          <div className="diff-header">
            <span style={{ fontWeight: 600 }}>Оригинал</span>
            <span className="badge badge-gray">{DEMO_ORIGINAL_TEXT.score} баллов</span>
          </div>
          <div className="diff-content" style={{ whiteSpace: 'pre-wrap', fontSize: '0.85rem', lineHeight: 1.7, padding: '1rem' }}>
            <strong>{DEMO_ORIGINAL_TEXT.position}</strong>{'\n\n'}
            <mark style={{ background: 'rgba(239,68,68,0.12)', color: 'inherit', padding: '1px 3px', borderRadius: 3 }}>
              {DEMO_ORIGINAL_TEXT.summary}
            </mark>
            {'\n\n'}
            <mark style={{ background: 'rgba(239,68,68,0.12)', color: 'inherit', padding: '1px 3px', borderRadius: 3 }}>
              {DEMO_ORIGINAL_TEXT.experience}
            </mark>
          </div>
        </div>
        <div className="diff-panel">
          <div className="diff-header">
            <span style={{ fontWeight: 600 }}>Оптимизировано</span>
            <span className="badge badge-green">{DEMO_OPTIMIZED_TEXT.score} баллов</span>
          </div>
          <div className="diff-content" style={{ whiteSpace: 'pre-wrap', fontSize: '0.85rem', lineHeight: 1.7, padding: '1rem' }}>
            <strong>{DEMO_OPTIMIZED_TEXT.position}</strong>{'\n\n'}
            <mark style={{ background: 'rgba(16,185,129,0.12)', color: 'inherit', padding: '1px 3px', borderRadius: 3 }}>
              {DEMO_OPTIMIZED_TEXT.summary}
            </mark>
            {'\n\n'}
            <mark style={{ background: 'rgba(16,185,129,0.12)', color: 'inherit', padding: '1px 3px', borderRadius: 3 }}>
              {DEMO_OPTIMIZED_TEXT.experience}
            </mark>
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

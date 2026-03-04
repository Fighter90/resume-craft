import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Download, Sparkles } from 'lucide-react'

const SECTIONS = [
  { id: 'summary', label: 'Саммари' },
  { id: 'experience', label: 'Опыт работы' },
  { id: 'education', label: 'Образование' },
  { id: 'skills', label: 'Навыки' },
  { id: 'additional', label: 'Дополнительно' },
]

const INITIAL: Record<string, string> = {
  summary: 'Product Manager с 6+ лет опыта в B2B/B2C продуктах (DAU 500K+). Руководил командами до 12 человек. Специализация — data-driven стратегия, Growth, монетизация SaaS, интеграция AI. Увеличил конверсию на 34%, LTV на 45%.',
  experience: 'Product Manager — Яндекс\n2021 – настоящее время\n\n• Руководил запуском 3 продуктовых линеек, каждая достигла 100K+ MAU за 6 месяцев\n• Повысил конверсию воронки на 34% через A/B тестирование (120+ экспериментов)\n• Управлял кросс-функциональной командой из 12 человек (frontend, backend, ML, design)\n• Внедрил OKR-фреймворк, повысив alignment команды на 40% (по внутренним опросам)',
  education: 'МГУ им. М.В. Ломоносова\nМагистратура, Прикладная математика и информатика\n2014 – 2018\n\nКурсы: Product Management (ProductStar), Machine Learning (Coursera)',
  skills: 'Agile, Scrum, Kanban, SQL, Python, A/B Testing, Unit-экономика, CJM, JTBD, Product Strategy, Growth Marketing, Data Analysis, Jira, Figma, Amplitude, Mixpanel',
  additional: 'Языки: Русский (родной), Английский (C1)\nСертификаты: PSPO I (Scrum.org)\nВыступления: ProductSense 2023, Teamlead Conf 2022',
}

export default function EditorPage() {
  const navigate = useNavigate()
  const [activeSection, setActiveSection] = useState('summary')
  const [content, setContent] = useState(INITIAL)

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <button onClick={() => navigate(-1)} className="btn btn-secondary btn-sm"><ArrowLeft size={16} /></button>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Редактор резюме</h2>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button className="btn btn-secondary btn-sm"><Sparkles size={14} /> AI-подсказка</button>
          <button onClick={() => navigate('/app/export')} className="btn btn-primary btn-sm"><Download size={14} /> Экспорт</button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '220px 1fr', gap: '1.5rem' }}>
        {/* Sidebar sections */}
        <div className="card" style={{ padding: '0.5rem', height: 'fit-content' }}>
          {SECTIONS.map(s => (
            <div
              key={s.id}
              onClick={() => setActiveSection(s.id)}
              style={{
                padding: '0.65rem 0.85rem', borderRadius: 'var(--radius-sm)', cursor: 'pointer',
                fontWeight: activeSection === s.id ? 600 : 400, fontSize: '0.9rem',
                background: activeSection === s.id ? 'var(--primary-bg)' : 'transparent',
                color: activeSection === s.id ? 'var(--primary)' : 'var(--text-secondary)',
              }}
            >
              {s.label}
            </div>
          ))}
        </div>

        {/* Editor area */}
        <div className="card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ fontWeight: 600, fontSize: '1rem' }}>{SECTIONS.find(s => s.id === activeSection)?.label}</h3>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              {content[activeSection].length} символов
            </span>
          </div>
          <textarea
            value={content[activeSection]}
            onChange={e => setContent({ ...content, [activeSection]: e.target.value })}
            className="input-field"
            style={{ minHeight: 300, fontFamily: 'inherit', lineHeight: 1.7, resize: 'vertical' }}
          />

          {/* AI Hint */}
          <div style={{
            marginTop: '1rem', padding: '0.85rem 1rem', borderRadius: 'var(--radius-sm)',
            background: 'linear-gradient(135deg, rgba(86,90,221,0.08), rgba(124,58,237,0.08))',
            border: '1px solid rgba(86,90,221,0.2)', fontSize: '0.85rem',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontWeight: 600, marginBottom: '0.35rem', color: 'var(--primary)' }}>
              <Sparkles size={14} /> AI-рекомендация
            </div>
            Добавьте конкретные метрики (%, ₽, количество) к каждому достижению для повышения Match Score.
          </div>
        </div>
      </div>
    </div>
  )
}

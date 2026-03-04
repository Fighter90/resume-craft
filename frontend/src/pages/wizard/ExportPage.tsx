import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Download, FileText, FileType, ExternalLink, Check } from 'lucide-react'

const FORMATS = [
  { id: 'docx', icon: FileText, label: 'DOCX', desc: 'Microsoft Word — рекомендуем для hh.ru' },
  { id: 'pdf', icon: FileType, label: 'PDF', desc: 'Универсальный формат для печати' },
  { id: 'hh', icon: ExternalLink, label: 'hh.ru', desc: 'Обновить резюме на hh.ru напрямую' },
]

const TEMPLATES = [
  { id: 'minimal', label: 'Минималистичный', desc: 'Чистый, без лишнего', color: '#565ADD' },
  { id: 'professional', label: 'Профессиональный', desc: 'Структурированный, с акцентами', color: '#059669' },
  { id: 'creative', label: 'Креативный', desc: 'Современный, с элементами дизайна', color: '#7C3AED' },
]

export default function ExportPage() {
  const navigate = useNavigate()
  const [format, setFormat] = useState('docx')
  const [template, setTemplate] = useState('professional')

  return (
    <div className="wizard-container">
      <button onClick={() => navigate(-1)} className="btn btn-secondary btn-sm" style={{ marginBottom: '1.5rem' }}>
        <ArrowLeft size={16} /> Назад
      </button>

      <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>Экспорт резюме</h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>Скачайте оптимизированное резюме</p>

      {/* Format selection */}
      <h3 style={{ fontWeight: 600, marginBottom: '1rem' }}>Формат файла</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
        {FORMATS.map(f => (
          <div
            key={f.id}
            className={`card${format === f.id ? ' selected' : ''}`}
            onClick={() => setFormat(f.id)}
            style={{ padding: '1.25rem', cursor: 'pointer', textAlign: 'center', position: 'relative' }}
          >
            <f.icon size={28} style={{ color: 'var(--primary)', marginBottom: '0.5rem' }} />
            <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>{f.label}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{f.desc}</div>
            {format === f.id && (
              <div style={{
                position: 'absolute', top: '0.6rem', right: '0.6rem',
                width: 22, height: 22, borderRadius: '50%', background: 'var(--primary)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <Check size={13} color="#fff" />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Template selection */}
      <h3 style={{ fontWeight: 600, marginBottom: '1rem' }}>Шаблон оформления</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
        {TEMPLATES.map(t => (
          <div
            key={t.id}
            className={`card${template === t.id ? ' selected' : ''}`}
            onClick={() => setTemplate(t.id)}
            style={{ padding: '1.25rem', cursor: 'pointer', position: 'relative' }}
          >
            <div style={{ width: '100%', height: 80, borderRadius: 'var(--radius-sm)', marginBottom: '0.75rem', background: `linear-gradient(135deg, ${t.color}22, ${t.color}44)`, border: `2px solid ${t.color}33` }} />
            <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>{t.label}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{t.desc}</div>
            {template === t.id && (
              <div style={{
                position: 'absolute', top: '0.6rem', right: '0.6rem',
                width: 22, height: 22, borderRadius: '50%', background: 'var(--primary)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <Check size={13} color="#fff" />
              </div>
            )}
          </div>
        ))}
      </div>

      <button className="btn btn-primary btn-block" style={{ height: 52 }}>
        <Download size={18} /> Скачать {format.toUpperCase()}
      </button>

      {/* Ready to download — matches prototype */}
      <div className="card" style={{ padding: '1.25rem', marginTop: '1.5rem' }}>
        <h3 style={{ fontWeight: 600, marginBottom: '1rem' }}>Готово к скачиванию</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', fontSize: '0.85rem' }}>
          <div>
            <span style={{ color: 'var(--text-secondary)' }}>Файл:</span>{' '}
            <span style={{ fontWeight: 500 }}>resume_optimized.{format}</span>
          </div>
          <div>
            <span style={{ color: 'var(--text-secondary)' }}>Шаблон:</span>{' '}
            <span style={{ fontWeight: 500 }}>{TEMPLATES.find(t => t.id === template)?.label}</span>
          </div>
          <div>
            <span style={{ color: 'var(--text-secondary)' }}>Размер:</span>{' '}
            <span style={{ fontWeight: 500 }}>~48 КБ</span>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <span className="badge badge-green">Match 87%</span>
            <span className="badge badge-green">ATS A+</span>
          </div>
        </div>
      </div>
    </div>
  )
}

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Loader, FileText, Search, Sparkles, CheckCircle } from 'lucide-react'

const STEPS = [
  { icon: FileText, label: 'Загрузка документа', desc: 'Парсинг и извлечение текста' },
  { icon: Search, label: 'Анализ вакансии', desc: 'Определение требований и ключевых слов' },
  { icon: Sparkles, label: 'AI оптимизация', desc: 'Генерация улучшенного текста резюме' },
  { icon: CheckCircle, label: 'Финализация', desc: 'Скоринг, проверка качества, ATS-рейтинг' },
]

export default function ProcessingPage() {
  const navigate = useNavigate()
  const [current, setCurrent] = useState(0)
  const [progress, setProgress] = useState(0)
  const [done, setDone] = useState(false)

  useEffect(() => {
    const timer = setInterval(() => {
      setProgress(p => {
        if (p >= 100) {
          clearInterval(timer)
          setDone(true)
          return 100
        }
        return p + 1
      })
    }, 80)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    if (progress < 25) setCurrent(0)
    else if (progress < 50) setCurrent(1)
    else if (progress < 75) setCurrent(2)
    else setCurrent(3)
  }, [progress])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', padding: '2rem', textAlign: 'center' }}>
      {/* Spinner */}
      <div style={{ position: 'relative', marginBottom: '2rem' }}>
        <div className="processing-spinner">
          <Loader size={48} className="spinning" style={{ color: 'var(--primary)' }} />
        </div>
      </div>

      <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>
        {done ? 'Оптимизация завершена!' : 'Оптимизируем ваше резюме...'}
      </h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>
        {done ? 'Ваше резюме готово к просмотру' : 'GigaChat Pro анализирует и улучшает ваше резюме · Обычно 10–30 секунд'}
      </p>

      {/* Progress bar */}
      <div style={{ width: '100%', maxWidth: 400, marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.5rem' }}>
          <span>{progress}%</span>
          <span>~{Math.max(0, Math.round((100 - progress) * 0.15))} сек</span>
        </div>
        <div className="progress-bar" style={{ height: 8 }}>
          <div className="progress-fill" style={{ width: `${progress}%`, transition: 'width 0.1s linear' }} />
        </div>
      </div>

      {/* Steps */}
      <div style={{ width: '100%', maxWidth: 400 }}>
        {STEPS.map((s, i) => {
          const Icon = s.icon
          const done = i < current
          const active = i === current
          return (
            <div key={i} style={{
              display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.75rem',
              borderRadius: 'var(--radius-sm)',
              opacity: done || active ? 1 : 0.4,
              background: active ? 'var(--primary-bg)' : 'transparent',
              transition: 'all 0.3s',
            }}>
              <Icon size={20} style={{ color: done ? 'var(--success)' : active ? 'var(--primary)' : 'var(--text-secondary)' }} />
              <div style={{ textAlign: 'left' }}>
                <div style={{ fontSize: '0.9rem', fontWeight: 600, color: done ? 'var(--success)' : undefined }}>{s.label}</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>{s.desc}</div>
              </div>
              {done && <CheckCircle size={16} style={{ marginLeft: 'auto', color: 'var(--success)' }} />}
            </div>
          )
        })}
      </div>

      {done && (
        <button onClick={() => navigate('/app/results')} className="btn btn-primary" style={{ marginTop: '2rem' }}>
          Посмотреть результат
        </button>
      )}
    </div>
  )
}

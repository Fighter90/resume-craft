import { Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, Check, AlertCircle, Loader } from 'lucide-react'
import { useState } from 'react'
import { api } from '../../services/api'
import { useWizard } from '../../contexts/WizardContext'

const MODELS = [
  {
    id: 'gigachat-pro',
    name: 'GigaChat Pro',
    provider: 'Сбер',
    badge: 'Рекомендуем',
    badgeClass: 'badge-green',
    description: '#1 в MERA бенчмарке для русского языка. Лучшее понимание российского рынка труда.',
    quality: 95,
    speed: 70,
    tags: ['Русский язык', 'ATS-оптимизация', 'Данные в РФ'],
    plan: 'standard',
  },
  {
    id: 'gpt-4o',
    name: 'GPT-4o',
    provider: 'OpenAI',
    badge: 'Pro',
    badgeClass: 'badge-indigo',
    description: 'Сильнейшая мультиязычная модель. Глубокое понимание контекста и нюансов.',
    quality: 92,
    speed: 65,
    tags: ['Мультиязычная', 'Креативность', 'Аналитика'],
    plan: 'pro',
  },
  {
    id: 'llama-3-70b',
    name: 'Llama 3.3 70B',
    provider: 'Groq',
    badge: 'Бесплатная',
    badgeClass: 'badge-yellow',
    description: 'Молниеносная скорость генерации. 14 400 запросов/день бесплатно.',
    quality: 78,
    speed: 95,
    tags: ['Скорость', 'Бесплатно', 'Open Source'],
  },
  {
    id: 'openrouter',
    name: 'OpenRouter',
    provider: 'OpenRouter',
    badge: 'Гибкая',
    badgeClass: 'badge-indigo',
    description: '100+ моделей через единый API. Claude, Gemini, Mistral и другие — выбирайте лучшую.',
    quality: 90,
    speed: 80,
    tags: ['Мультимодель', 'Гибкость', '100+ моделей'],
    plan: 'standard',
  },
]

export default function ModelsPage() {
  const navigate = useNavigate()
  const { resumeId, vacancyId, setModel, setTaskId } = useWizard()
  const [selected, setSelected] = useState('gigachat-pro')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleStart = async () => {
    if (!resumeId || !vacancyId) {
      setError('Сначала загрузите резюме и выберите вакансию')
      return
    }
    setLoading(true)
    setError(null)
    try {
      setModel(selected)
      const res = await api.startRewrite(resumeId, vacancyId, selected) as { task_id: string }
      setTaskId(res.task_id)
      navigate('/app/processing')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка запуска оптимизации')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="wizard-container">
      <Link to="/app/vacancy" className="btn btn-secondary btn-sm" style={{ marginBottom: '1.5rem' }}>
        <ArrowLeft size={16} /> Назад
      </Link>

      <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>Выберите AI-модель</h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>Каждая модель имеет свои сильные стороны</p>

      <div className="model-grid">
        {MODELS.map(m => (
          <div
            key={m.id}
            className={`card model-card${selected === m.id ? ' selected' : ''}`}
            onClick={() => setSelected(m.id)}
            style={{ cursor: 'pointer', padding: '1.25rem', position: 'relative' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <div>
                <h3 style={{ fontWeight: 600, fontSize: '1rem' }}>{m.name}</h3>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{m.provider}</span>
              </div>
              <span className={`badge ${m.badgeClass}`}>{m.badge}</span>
            </div>

            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>{m.description}</p>

            {/* Quality bar */}
            <div style={{ marginBottom: '0.75rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '0.3rem' }}>
                <span>Качество</span><span>{m.quality}%</span>
              </div>
              <div className="progress-bar"><div className="progress-fill" style={{ width: `${m.quality}%` }} /></div>
            </div>

            {/* Speed bar */}
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '0.3rem' }}>
                <span>Скорость</span><span>{m.speed}%</span>
              </div>
              <div className="progress-bar"><div className="progress-fill" style={{ width: `${m.speed}%`, background: 'var(--info)' }} /></div>
            </div>

            <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
              {m.tags.map(t => <span key={t} className="badge badge-gray">{t}</span>)}
            </div>

            {m.plan && (
              <div style={{ marginTop: '0.75rem', fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>
                Доступна на тарифе <span style={{ fontWeight: 600, textTransform: 'capitalize' }}>{m.plan === 'pro' ? 'Pro' : 'Standard+'}</span>
              </div>
            )}

            {selected === m.id && (
              <div style={{
                position: 'absolute', top: '0.75rem', right: '0.75rem',
                width: 24, height: 24, borderRadius: '50%',
                background: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <Check size={14} color="#fff" />
              </div>
            )}
          </div>
        ))}
      </div>

      <button onClick={handleStart} className="btn btn-primary btn-block" style={{ marginTop: '1.5rem' }} disabled={loading}>
        {loading ? <><Loader size={16} className="spin" /> Запуск...</> : 'Начать оптимизацию'}
      </button>
      {error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--error)', marginTop: '0.75rem', fontSize: '0.875rem' }}>
          <AlertCircle size={16} /> {error}
        </div>
      )}
    </div>
  )
}

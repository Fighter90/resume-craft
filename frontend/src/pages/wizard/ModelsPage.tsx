import { Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, Check, AlertCircle, Loader, AlertTriangle, Settings } from 'lucide-react'
import { useState, useEffect } from 'react'
import { api } from '../../services/api'
import { useWizard } from '../../contexts/WizardContext'

/* eslint-disable @typescript-eslint/no-explicit-any */

interface ModelInfo {
  id: string
  name: string
  provider: string
  available: boolean
  description: string
  sub_models?: Array<{ id: string; name: string; provider: string }>
}

const MODEL_META: Record<string, { badge: string; badgeClass: string; quality: number; speed: number; tags: string[] }> = {
  'gigachat-pro': { badge: 'Рекомендуем', badgeClass: 'badge-green', quality: 95, speed: 70, tags: ['Русский язык', 'ATS-оптимизация', 'Данные в РФ'] },
  'gpt-4o': { badge: 'Pro', badgeClass: 'badge-indigo', quality: 92, speed: 65, tags: ['Мультиязычная', 'Креативность', 'Аналитика'] },
  'llama-3-70b': { badge: 'Бесплатная', badgeClass: 'badge-yellow', quality: 78, speed: 95, tags: ['Скорость', 'Бесплатно', 'Open Source'] },
  'openrouter': { badge: 'Гибкая', badgeClass: 'badge-indigo', quality: 90, speed: 80, tags: ['Мультимодель', 'Гибкость', '100+ моделей'] },
}

const FALLBACK_MODELS: ModelInfo[] = [
  { id: 'gigachat-pro', name: 'GigaChat Pro', provider: 'Сбер', available: true, description: '#1 в MERA бенчмарке для русского языка. Лучшее понимание российского рынка труда.' },
  { id: 'gpt-4o', name: 'GPT-4o', provider: 'OpenAI', available: true, description: 'Сильнейшая мультиязычная модель. Глубокое понимание контекста и нюансов.' },
  { id: 'llama-3-70b', name: 'Llama 3.3 70B', provider: 'Groq', available: true, description: 'Молниеносная скорость генерации. 14 400 запросов/день бесплатно.' },
  { id: 'openrouter', name: 'OpenRouter', provider: 'OpenRouter', available: true, description: '100+ моделей через единый API. Claude, Gemini, Mistral и другие.' },
]

export default function ModelsPage() {
  const navigate = useNavigate()
  const { resumeId, vacancyId, setModel, setTaskId } = useWizard()
  const [selected, setSelected] = useState('gigachat-pro')
  const [openrouterModel, setOpenrouterModel] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [models, setModels] = useState<ModelInfo[]>(FALLBACK_MODELS)
  const [loadingModels, setLoadingModels] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.getModels()
        const list = res.models || []
        if (list.length > 0) {
          setModels(list)
          const first = list.find((m: ModelInfo) => m.available)
          if (first) setSelected(first.id)
          const or = list.find((m: ModelInfo) => m.id === 'openrouter')
          if (or?.sub_models?.length) setOpenrouterModel(or.sub_models[0].id)
        }
      } catch { /* use fallback models */ }
      setLoadingModels(false)
    }
    load()
  }, [])

  const noKeysConfigured = models.length > 0 && !models.some(m => m.available)
  const selectedModel = models.find(m => m.id === selected)

  const handleStart = async () => {
    if (!resumeId || !vacancyId) {
      setError('Сначала загрузите резюме и выберите вакансию')
      return
    }
    if (selectedModel && !selectedModel.available) {
      setError(`API-ключ для ${selectedModel.name} не настроен. Выберите другую модель или настройте ключ в Настройках AI.`)
      return
    }
    setLoading(true)
    setError(null)
    try {
      setModel(selected)
      const orModel = selected === 'openrouter' && openrouterModel ? openrouterModel : undefined
      const res = await api.startRewrite(resumeId, vacancyId, selected, orModel) as { task_id: string }
      setTaskId(res.task_id)
      navigate('/app/processing')
    } catch (err: any) {
      const msg = err?.message || 'Ошибка запуска оптимизации'
      setError(msg)
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

      {noKeysConfigured && (
        <div className="card" style={{ padding: '1rem 1.25rem', marginBottom: '1.5rem', background: '#FEF3C7', border: '1px solid #F59E0B' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <AlertTriangle size={18} color="#D97706" />
            <strong style={{ color: '#92400E' }}>API-ключи не настроены</strong>
          </div>
          <p style={{ fontSize: '0.85rem', color: '#78350F', margin: 0 }}>
            Ни одна AI-модель недоступна. Настройте API-ключ хотя бы для одного провайдера в{' '}
            <Link to="/app/settings/ai" style={{ color: '#D97706', fontWeight: 600 }}>Настройках AI</Link>.
          </p>
        </div>
      )}

      {loadingModels ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)', padding: '2rem 0' }}>
          <Loader size={16} className="spin" /> Загрузка моделей...
        </div>
      ) : (
        <div className="model-grid">
          {models.map(m => {
            const meta = MODEL_META[m.id] || { badge: '', badgeClass: 'badge-gray', quality: 80, speed: 80, tags: [] }
            return (
              <div
                key={m.id}
                className={`card model-card${selected === m.id ? ' selected' : ''}`}
                onClick={() => m.available ? setSelected(m.id) : undefined}
                style={{
                  cursor: m.available ? 'pointer' : 'not-allowed',
                  padding: '1.25rem', position: 'relative',
                  opacity: m.available ? 1 : 0.55,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                  <div>
                    <h3 style={{ fontWeight: 600, fontSize: '1rem' }}>{m.name}</h3>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{m.provider}</span>
                  </div>
                  <div style={{ display: 'flex', gap: '0.35rem', alignItems: 'center' }}>
                    {!m.available && <span className="badge badge-red" style={{ fontSize: '0.7rem' }}>Нет ключа</span>}
                    {meta.badge && <span className={`badge ${meta.badgeClass}`}>{meta.badge}</span>}
                  </div>
                </div>

                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>{m.description}</p>

                <div style={{ marginBottom: '0.75rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '0.3rem' }}>
                    <span>Качество</span><span>{meta.quality}%</span>
                  </div>
                  <div className="progress-bar"><div className="progress-fill" style={{ width: `${meta.quality}%` }} /></div>
                </div>

                <div style={{ marginBottom: '1rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '0.3rem' }}>
                    <span>Скорость</span><span>{meta.speed}%</span>
                  </div>
                  <div className="progress-bar"><div className="progress-fill" style={{ width: `${meta.speed}%`, background: 'var(--info)' }} /></div>
                </div>

                <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
                  {meta.tags.map(t => <span key={t} className="badge badge-gray">{t}</span>)}
                </div>

                {!m.available && (
                  <Link to="/app/settings/ai" onClick={e => e.stopPropagation()}
                    style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', marginTop: '0.75rem', fontSize: '0.8rem', color: 'var(--primary)' }}>
                    <Settings size={14} /> Настроить ключ
                  </Link>
                )}

                {selected === m.id && m.available && (
                  <div style={{
                    position: 'absolute', top: '0.75rem', right: '0.75rem',
                    width: 24, height: 24, borderRadius: '50%',
                    background: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    <Check size={14} color="#fff" />
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* OpenRouter sub-model selector */}
      {selected === 'openrouter' && selectedModel?.available && selectedModel.sub_models && selectedModel.sub_models.length > 0 && (
        <div className="card" style={{ padding: '1rem 1.25rem', marginTop: '1rem' }}>
          <label style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.5rem', display: 'block' }}>
            Модель OpenRouter
          </label>
          <select
            className="input-field"
            value={openrouterModel}
            onChange={e => setOpenrouterModel(e.target.value)}
            style={{ width: '100%' }}
          >
            {selectedModel.sub_models.map(sm => (
              <option key={sm.id} value={sm.id}>{sm.name} ({sm.provider})</option>
            ))}
          </select>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: '0.5rem 0 0' }}>
            Выберите конкретную модель из каталога OpenRouter
          </p>
        </div>
      )}

      <button onClick={handleStart} className="btn btn-primary btn-block" style={{ marginTop: '1.5rem' }}
        disabled={loading || !!(selectedModel && !selectedModel.available)}>
        {loading ? <><Loader size={16} className="spin" /> Запуск...</> : 'Начать оптимизацию'}
      </button>
      {error && (
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem', color: 'var(--error)', marginTop: '0.75rem', fontSize: '0.875rem' }}>
          <AlertCircle size={16} style={{ flexShrink: 0, marginTop: 2 }} /> <span>{error}</span>
        </div>
      )}
    </div>
  )
}

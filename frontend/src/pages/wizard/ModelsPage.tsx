import { Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, Check, AlertCircle, Loader, AlertTriangle, Settings } from 'lucide-react'
import { useState, useEffect } from 'react'
import { api } from '../../services/api'
import { useWizard } from '../../contexts/WizardContext'

/* eslint-disable @typescript-eslint/no-explicit-any */

interface SubModel { id: string; name: string; provider: string }
interface ModelInfo {
  id: string
  name: string
  provider: string
  available: boolean
  description: string
  has_sub_models?: boolean
}

const MODEL_META: Record<string, { badge: string; badgeClass: string; quality: number; speed: number; tags: string[] }> = {
  'gigachat-pro': { badge: 'Рекомендуем', badgeClass: 'badge-green', quality: 95, speed: 70, tags: ['Русский язык', 'ATS-оптимизация', 'Данные в РФ'] },
  'openai': { badge: 'Pro', badgeClass: 'badge-indigo', quality: 92, speed: 65, tags: ['Мультиязычная', 'Креативность', 'GPT-4o'] },
  'anthropic': { badge: 'Pro', badgeClass: 'badge-indigo', quality: 93, speed: 70, tags: ['Claude 4', 'Русский язык', '200K контекст'] },
  'openrouter': { badge: 'Гибкая', badgeClass: 'badge-indigo', quality: 90, speed: 80, tags: ['Мультимодель', 'Гибкость', '100+ моделей'] },
}

const FALLBACK_MODELS: ModelInfo[] = [
  { id: 'gigachat-pro', name: 'GigaChat Pro', provider: 'Сбер', available: true, description: '#1 в MERA бенчмарке для русского языка. Лучшее понимание российского рынка труда.', has_sub_models: false },
  { id: 'openai', name: 'OpenAI', provider: 'OpenAI', available: true, description: 'GPT-4o, GPT-4o-mini и другие модели OpenAI. 128K контекст.', has_sub_models: true },
  { id: 'anthropic', name: 'Anthropic Claude', provider: 'Anthropic', available: true, description: 'Claude Sonnet 4, Claude Haiku — отличный русский, 200K контекст.', has_sub_models: true },
  { id: 'openrouter', name: 'OpenRouter', provider: 'OpenRouter', available: true, description: '100+ моделей через единый API. Claude, Gemini, Mistral и другие.', has_sub_models: true },
]

const FALLBACK_SUB_MODELS: Record<string, SubModel[]> = {
  'openai': [
    { id: 'gpt-4o', name: 'GPT-4o', provider: 'OpenAI' },
    { id: 'gpt-4o-mini', name: 'GPT-4o Mini', provider: 'OpenAI' },
    { id: 'gpt-4-turbo', name: 'GPT-4 Turbo', provider: 'OpenAI' },
  ],
  'anthropic': [
    { id: 'claude-sonnet-4-20250514', name: 'Claude Sonnet 4', provider: 'Anthropic' },
    { id: 'claude-3-5-haiku-20241022', name: 'Claude 3.5 Haiku', provider: 'Anthropic' },
  ],
  'openrouter': [
    { id: 'anthropic/claude-sonnet-4', name: 'Claude Sonnet 4', provider: 'OpenRouter' },
    { id: 'google/gemini-2.5-flash', name: 'Gemini 2.5 Flash', provider: 'OpenRouter' },
    { id: 'mistralai/mistral-large', name: 'Mistral Large', provider: 'OpenRouter' },
  ],
}

export default function ModelsPage() {
  const navigate = useNavigate()
  const { resumeId, vacancyId, setModel, setTaskId } = useWizard()

  // Read default model from settings
  const getDefaultModel = (): string => {
    try {
      const settings = JSON.parse(localStorage.getItem('ai_settings') || '{}')
      if (settings.model && typeof settings.model === 'string') return settings.model
    } catch { /* ignore */ }
    return 'gigachat-pro'
  }

  const [selected, setSelected] = useState(getDefaultModel())
  const [subModel, setSubModel] = useState('')
  const [subModels, setSubModels] = useState<SubModel[]>([])
  const [loadingSubModels, setLoadingSubModels] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [models, setModels] = useState<ModelInfo[]>(FALLBACK_MODELS)
  const [loadingModels, setLoadingModels] = useState(false)

  // Map provider id to localStorage API key field
  const LOCAL_KEY_MAP: Record<string, string> = {
    'gigachat-pro': 'gigachat', 'openai': 'openai', 'anthropic': 'anthropic', 'openrouter': 'openrouter',
  }

  // Check if user has local API key set for a given model
  const hasLocalKey = (modelId: string): boolean => {
    try {
      const settings = JSON.parse(localStorage.getItem('ai_settings') || '{}')
      const keys = settings.apiKeys || {}
      const field = LOCAL_KEY_MAP[modelId]
      return !!(field && keys[field]?.trim())
    } catch { return false }
  }

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.getModels()
        const list = res.models || []
        if (list.length > 0) {
          // Merge server availability with local keys
          const merged = list.map((m: ModelInfo) => ({
            ...m,
            available: m.available || hasLocalKey(m.id),
          }))
          setModels(merged)
          const first = merged.find((m: ModelInfo) => m.available)
          if (first) setSelected(first.id)
        } else {
          // No server models — use fallback with local key check
          setModels(FALLBACK_MODELS.map(m => ({ ...m, available: m.available || hasLocalKey(m.id) })))
        }
      } catch {
        // Server unavailable — use fallback with local key check
        setModels(FALLBACK_MODELS.map(m => ({ ...m, available: m.available || hasLocalKey(m.id) })))
      }
      setLoadingModels(false)
    }
    load()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Загрузка подмоделей при выборе провайдера с has_sub_models
  useEffect(() => {
    const selectedModel = models.find(m => m.id === selected)
    if (!selectedModel?.has_sub_models || !selectedModel.available) {
      setSubModels([])
      setSubModel('')
      return
    }

    const fetchSubModels = async () => {
      setLoadingSubModels(true)
      try {
        const res = await api.getSubModels(selected)
        const list = res.sub_models || []
        if (list.length > 0) {
          setSubModels(list)
          setSubModel(list[0].id)
        } else {
          // Use fallback sub-models when server returns empty
          const fallback = FALLBACK_SUB_MODELS[selected] || []
          setSubModels(fallback)
          if (fallback.length > 0) setSubModel(fallback[0].id)
        }
      } catch {
        // Use fallback sub-models on error
        const fallback = FALLBACK_SUB_MODELS[selected] || []
        setSubModels(fallback)
        if (fallback.length > 0) setSubModel(fallback[0].id)
      }
      setLoadingSubModels(false)
    }
    fetchSubModels()
  }, [selected, models])

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
      const sm = selectedModel?.has_sub_models && subModel ? subModel : undefined
      const res = await api.startRewrite(resumeId, vacancyId, selected, sm) as { task_id: string }
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

      {/* Sub-model selector for providers with 2-step selection */}
      {selectedModel?.has_sub_models && selectedModel.available && (
        <div className="card" style={{ padding: '1rem 1.25rem', marginTop: '1rem' }}>
          <label style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.5rem', display: 'block' }}>
            Модель {selectedModel.name}
          </label>
          {loadingSubModels ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)', padding: '0.5rem 0' }}>
              <Loader size={14} className="spin" /> Загрузка доступных моделей...
            </div>
          ) : subModels.length > 0 ? (
            <>
              <select
                className="input-field"
                value={subModel}
                onChange={e => setSubModel(e.target.value)}
                style={{ width: '100%' }}
              >
                {subModels.map(sm => (
                  <option key={sm.id} value={sm.id}>{sm.name} ({sm.provider})</option>
                ))}
              </select>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: '0.5rem 0 0' }}>
                Выберите конкретную модель из каталога {selectedModel.name}
              </p>
            </>
          ) : (
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Не удалось загрузить список моделей. Будет использована модель по умолчанию.
            </p>
          )}
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

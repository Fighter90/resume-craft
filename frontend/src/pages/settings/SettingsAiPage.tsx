import { useState, useEffect } from 'react'
import { Save, RotateCcw, Eye, EyeOff, Zap, Brain, Globe, Cpu, AlertTriangle, CheckCircle, Loader } from 'lucide-react'
import { api } from '../../services/api'

/* eslint-disable @typescript-eslint/no-explicit-any */

interface SubModel { id: string; name: string; provider: string }
interface ModelOption {
  id: string
  name: string
  provider: string
  desc: string
  badge?: string
  badgeColor?: string
  icon: typeof Cpu
  apiKeyField: string
  apiKeyPlaceholder: string
  available?: boolean
  hasSubModels?: boolean
}

const MODELS: ModelOption[] = [
  {
    id: 'gigachat-pro', name: 'GigaChat Pro', provider: 'Сбер',
    desc: '#1 русский язык (MERA), данные в РФ, ФЗ-152 compliant',
    badge: 'Рекомендуем', badgeColor: '#4F46E5',
    icon: Zap, apiKeyField: 'gigachat', apiKeyPlaceholder: 'Credentials (Base64)',
    hasSubModels: false,
  },
  {
    id: 'openai', name: 'OpenAI', provider: 'OpenAI',
    desc: 'GPT-4o, GPT-4o-mini и другие модели OpenAI, 128K контекст',
    icon: Brain, apiKeyField: 'openai', apiKeyPlaceholder: 'sk-...',
    hasSubModels: true,
  },
  {
    id: 'anthropic', name: 'Anthropic Claude', provider: 'Anthropic',
    desc: 'Claude Sonnet 4, Claude Haiku — отличный русский, 200K контекст',
    badge: 'Новое', badgeColor: '#D97706',
    icon: Brain, apiKeyField: 'anthropic', apiKeyPlaceholder: 'sk-ant-...',
    hasSubModels: true,
  },
  {
    id: 'openrouter', name: 'OpenRouter', provider: 'OpenRouter',
    desc: 'Доступ к 100+ моделям через единый API (Claude, Gemini, Mixtral...)',
    icon: Globe, apiKeyField: 'openrouter', apiKeyPlaceholder: 'sk-or-v1-...',
    hasSubModels: true,
  },
]

const TOGGLES = [
  { id: 'auto_metrics', label: 'Автоматические метрики', desc: 'Генерировать количественные достижения', default: true },
  { id: 'ats', label: 'ATS оптимизация', desc: 'Адаптировать текст под ATS-фильтры', default: true },
  { id: 'upgrade_title', label: 'Апгрейд должности', desc: 'Предложить более сильные формулировки позиций', default: false },
  { id: 'keep_language', label: 'Сохранять язык', desc: 'Не менять язык оригинального резюме', default: true },
  { id: 'soft_skills', label: 'Soft skills', desc: 'Добавлять soft skills из описания вакансии', default: false },
]

// Fallback sub-model lists when server can't provide them
const FALLBACK_SUB_MODELS: Record<string, SubModel[]> = {
  openai: [
    { id: 'gpt-4o', name: 'GPT-4o', provider: 'OpenAI' },
    { id: 'gpt-4o-mini', name: 'GPT-4o Mini', provider: 'OpenAI' },
    { id: 'gpt-4-turbo', name: 'GPT-4 Turbo', provider: 'OpenAI' },
    { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', provider: 'OpenAI' },
  ],
  anthropic: [
    { id: 'claude-sonnet-4-20250514', name: 'Claude Sonnet 4', provider: 'Anthropic' },
    { id: 'claude-3-5-sonnet-20241022', name: 'Claude 3.5 Sonnet', provider: 'Anthropic' },
    { id: 'claude-3-5-haiku-20241022', name: 'Claude 3.5 Haiku', provider: 'Anthropic' },
  ],
  openrouter: [
    { id: 'anthropic/claude-sonnet-4-20250514', name: 'Claude Sonnet 4', provider: 'OpenRouter' },
    { id: 'openai/gpt-4o', name: 'GPT-4o', provider: 'OpenRouter' },
    { id: 'google/gemini-2.5-pro-preview', name: 'Gemini 2.5 Pro', provider: 'OpenRouter' },
    { id: 'meta-llama/llama-3.1-405b-instruct', name: 'Llama 3.1 405B', provider: 'OpenRouter' },
  ],
}

// Fetch live model lists from provider APIs using user's API key
async function fetchLiveModels(provider: string, apiKey: string): Promise<SubModel[]> {
  try {
    if (provider === 'openai') {
      const res = await fetch('https://api.openai.com/v1/models', {
        headers: { 'Authorization': `Bearer ${apiKey}` },
      })
      if (!res.ok) return []
      const data = await res.json()
      const chatModels = (data.data || [])
        .filter((m: any) => m.id.startsWith('gpt-') || m.id.startsWith('o') || m.id.includes('chatgpt'))
        .sort((a: any, b: any) => (b.created || 0) - (a.created || 0))
        .slice(0, 20)
      return chatModels.map((m: any) => ({ id: m.id, name: m.id, provider: 'OpenAI' }))
    }
    if (provider === 'anthropic') {
      const res = await fetch('https://api.anthropic.com/v1/models', {
        headers: { 'x-api-key': apiKey, 'anthropic-version': '2023-06-01', 'anthropic-dangerous-direct-browser-access': 'true' },
      })
      if (!res.ok) return []
      const data = await res.json()
      return (data.data || [])
        .sort((a: any, b: any) => (b.created_at || '').localeCompare(a.created_at || ''))
        .slice(0, 20)
        .map((m: any) => ({ id: m.id, name: m.display_name || m.id, provider: 'Anthropic' }))
    }
    if (provider === 'openrouter') {
      const res = await fetch('https://openrouter.ai/api/v1/models', {
        headers: { 'Authorization': `Bearer ${apiKey}` },
      })
      if (!res.ok) return []
      const data = await res.json()
      return (data.data || [])
        .filter((m: any) => m.id && !m.id.includes(':free'))
        .slice(0, 50)
        .map((m: any) => ({ id: m.id, name: m.name || m.id, provider: 'OpenRouter' }))
    }
  } catch { /* CORS or network error — fall through */ }
  return []
}

export default function SettingsAiPage() {
  // Load from localStorage
  const savedSettings = (() => {
    try { return JSON.parse(localStorage.getItem('ai_settings') || '{}') } catch { return {} }
  })()
  const [model, setModel] = useState(savedSettings.model || 'gigachat-pro')
  const [apiKeys, setApiKeys] = useState<Record<string, string>>(savedSettings.apiKeys || {
    gigachat: '', openai: '', anthropic: '', openrouter: '',
  })
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({})
  const [toggles, setToggles] = useState<Record<string, boolean>>(
    savedSettings.toggles || Object.fromEntries(TOGGLES.map(t => [t.id, t.default]))
  )
  const [saved, setSaved] = useState(false)
  const [serverModels, setServerModels] = useState<ModelOption[]>([])
  const [subModels, setSubModels] = useState<SubModel[]>([])
  const [selectedSubModel, setSelectedSubModel] = useState<string>(savedSettings.subModel || '')
  const [loadingSubModels, setLoadingSubModels] = useState(false)

  // Fetch server-side model availability
  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.getModels()
        const list = res.models || []
        setServerModels(list.map((m: any) => ({ ...m, icon: Cpu, apiKeyField: '', apiKeyPlaceholder: '' })))
      } catch { /* server unavailable, continue with local settings */ }
    }
    load()
  }, [])

  // Load sub-models when provider with hasSubModels is selected
  const currentModel = MODELS.find(m => m.id === model)
  useEffect(() => {
    if (!currentModel?.hasSubModels) {
      setSubModels([])
      return
    }
    const fetchSub = async () => {
      setLoadingSubModels(true)
      try {
        // Try fetching live models from provider API using user's key
        const userKey = apiKeys[currentModel.apiKeyField]?.trim()
        if (userKey) {
          const live = await fetchLiveModels(model, userKey)
          if (live.length > 0) {
            setSubModels(live)
            if (!selectedSubModel || !live.find(m => m.id === selectedSubModel)) setSelectedSubModel(live[0].id)
            setLoadingSubModels(false)
            return
          }
        }
        // Fallback: try server-side sub-models
        const res = await api.getSubModels(model)
        const list = res.sub_models || []
        if (list.length > 0) {
          setSubModels(list)
          if (!selectedSubModel) setSelectedSubModel(list[0].id)
        } else {
          // Use fallback list
          const fallback = FALLBACK_SUB_MODELS[model] || []
          setSubModels(fallback)
          if (fallback.length > 0 && !selectedSubModel) setSelectedSubModel(fallback[0].id)
        }
      } catch {
        // Server unavailable — use fallback list
        const fallback = FALLBACK_SUB_MODELS[model] || []
        setSubModels(fallback)
        if (fallback.length > 0 && !selectedSubModel) setSelectedSubModel(fallback[0].id)
      }
      setLoadingSubModels(false)
    }
    fetchSub()
  }, [model, apiKeys]) // eslint-disable-line react-hooks/exhaustive-deps

  const getServerAvailability = (modelId: string): boolean | null => {
    // LIVE-004: Показываем статус ТОЛЬКО на основе серверной доступности,
    // не показываем зелёную галочку только потому, что пользователь ввёл ключ локально
    const m = serverModels.find((s: any) => s.id === modelId)
    return m ? m.available ?? null : null
  }

  const toggle = (id: string) => setToggles({ ...toggles, [id]: !toggles[id] })

  const handleSave = () => {
    localStorage.setItem('ai_settings', JSON.stringify({ model, apiKeys, toggles, subModel: selectedSubModel }))
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const handleReset = () => {
    setModel('gigachat-pro')
    setToggles(Object.fromEntries(TOGGLES.map(t => [t.id, t.default])))
    setApiKeys({ gigachat: '', openai: '', anthropic: '', openrouter: '' })
    setSelectedSubModel('')
    localStorage.removeItem('ai_settings')
  }

  return (
    <div style={{ maxWidth: 640 }}>
      {/* Model selection cards */}
      <h3 style={{ fontWeight: 600, marginBottom: '1rem' }}>AI-модель по умолчанию</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1.5rem' }}>
        {MODELS.map(m => (
          <div
            key={m.id}
            onClick={() => setModel(m.id)}
            style={{
              padding: '1rem 1.25rem', borderRadius: 12, cursor: 'pointer',
              border: model === m.id ? '2px solid var(--primary, #4F46E5)' : '1px solid var(--border, #E5E7EB)',
              background: model === m.id ? 'var(--primary-bg, #EEF2FF)' : 'var(--card-bg, #fff)',
              transition: 'all 0.2s', display: 'flex', alignItems: 'flex-start', gap: '1rem',
            }}
            role="button"
            tabIndex={0}
            onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') setModel(m.id) }}
          >
            <div style={{
              width: 40, height: 40, borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: model === m.id ? 'var(--primary, #4F46E5)' : '#F3F4F6',
              color: model === m.id ? '#fff' : 'var(--text-secondary)',
              flexShrink: 0, transition: 'all 0.2s',
            }}>
              <m.icon size={20} />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>{m.name}</span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>({m.provider})</span>
                {m.badge && (
                  <span style={{
                    fontSize: '0.7rem', fontWeight: 600, padding: '2px 8px', borderRadius: 99,
                    background: m.badgeColor, color: '#fff',
                  }}>{m.badge}</span>
                )}
                {getServerAvailability(m.id) === true && (
                  <span title="Ключ настроен на сервере"><CheckCircle size={14} color="#059669" /></span>
                )}
                {getServerAvailability(m.id) === false && (
                  <span title="Ключ не настроен на сервере"><AlertTriangle size={14} color="#D97706" /></span>
                )}
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>{m.desc}</div>
            </div>
            <div style={{
              width: 20, height: 20, borderRadius: '50%', border: '2px solid',
              borderColor: model === m.id ? 'var(--primary, #4F46E5)' : '#D1D5DB',
              display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: 2,
            }}>
              {model === m.id && <div style={{ width: 10, height: 10, borderRadius: '50%', background: 'var(--primary, #4F46E5)' }} />}
            </div>
          </div>
        ))}
      </div>

      {/* Sub-model picker for providers with 2-step selection */}
      {currentModel?.hasSubModels && (
        <div className="card" style={{ padding: '1.25rem', marginBottom: '1.5rem', border: '1px solid var(--primary, #4F46E5)', background: 'var(--primary-bg, #EEF2FF)' }}>
          <h4 style={{ fontWeight: 600, fontSize: '0.95rem', marginBottom: '0.5rem' }}>Модель {currentModel.name}</h4>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
            Выберите конкретную модель из каталога {currentModel.name}
          </p>
          {loadingSubModels ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)' }}>
              <Loader size={14} className="spin" /> Загрузка доступных моделей...
            </div>
          ) : subModels.length > 0 ? (
            <select
              className="input-field"
              value={selectedSubModel}
              onChange={e => setSelectedSubModel(e.target.value)}
              style={{ width: '100%' }}
            >
              {subModels.map(sm => (
                <option key={sm.id} value={sm.id}>{sm.name} — {sm.provider}</option>
              ))}
            </select>
          ) : (
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Не удалось загрузить список моделей
            </p>
          )}
        </div>
      )}

      {/* API Keys */}
      <div className="card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
        <h3 style={{ fontWeight: 600, marginBottom: '0.5rem' }}>API-ключи</h3>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
          Подключите свои ключи для использования моделей. Ключи хранятся в зашифрованном виде.
        </p>
        {MODELS.map(m => (
          <div key={m.apiKeyField} className="input-group" style={{ marginBottom: '1rem' }}>
            <label className="input-label">{m.name} ({m.provider})</label>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <input
                className="input-field"
                type={showKeys[m.apiKeyField] ? 'text' : 'password'}
                placeholder={m.apiKeyPlaceholder}
                value={apiKeys[m.apiKeyField]}
                onChange={e => setApiKeys({ ...apiKeys, [m.apiKeyField]: e.target.value })}
                style={{ flex: 1 }}
              />
              <button
                type="button"
                onClick={() => setShowKeys({ ...showKeys, [m.apiKeyField]: !showKeys[m.apiKeyField] })}
                style={{
                  padding: '0.75rem', borderRadius: 12, border: '1px solid var(--border)',
                  background: 'var(--card-bg, #fff)', cursor: 'pointer', display: 'flex', alignItems: 'center',
                }}
                title={showKeys[m.apiKeyField] ? 'Скрыть' : 'Показать'}
              >
                {showKeys[m.apiKeyField] ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Toggles */}
      <div className="card" style={{ padding: '1.5rem' }}>
        <h3 style={{ fontWeight: 600, marginBottom: '1rem' }}>Параметры оптимизации</h3>
        {TOGGLES.map(t => (
          <div key={t.id} style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            padding: '0.85rem 0', borderBottom: '1px solid var(--border)',
          }}>
            <div>
              <div style={{ fontWeight: 500, fontSize: '0.9rem' }}>{t.label}</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{t.desc}</div>
            </div>
            <label className="toggle-switch">
              <input type="checkbox" checked={toggles[t.id]} onChange={() => toggle(t.id)} />
              <span className="toggle-slider" />
            </label>
          </div>
        ))}
      </div>

      {/* Buttons */}
      <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.25rem' }}>
        <button className="btn btn-primary" onClick={handleSave}>
          <Save size={16} /> {saved ? '✓ Сохранено' : 'Сохранить'}
        </button>
        <button className="btn btn-secondary" onClick={handleReset}>
          <RotateCcw size={16} /> Сбросить
        </button>
      </div>
    </div>
  )
}

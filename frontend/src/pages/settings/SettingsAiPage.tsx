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
    hasSubModels: true,
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
  {
    id: 'groq', name: 'Groq', provider: 'Groq',
    desc: 'Быстрый inference — Llama 3, Mixtral, Gemma. Низкая латентность.',
    badge: 'Новое', badgeColor: '#059669',
    icon: Zap, apiKeyField: 'groq', apiKeyPlaceholder: 'gsk_...',
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
  'gigachat-pro': [
    { id: 'GigaChat-Pro', name: 'GigaChat-Pro', provider: 'GigaChat' },
    { id: 'GigaChat', name: 'GigaChat', provider: 'GigaChat' },
    { id: 'GigaChat-Max', name: 'GigaChat-Max', provider: 'GigaChat' },
  ],
  openai: [
    { id: 'gpt-4o', name: 'GPT-4o', provider: 'OpenAI' },
    { id: 'gpt-4o-mini', name: 'GPT-4o Mini', provider: 'OpenAI' },
    { id: 'gpt-4-turbo', name: 'GPT-4 Turbo', provider: 'OpenAI' },
    { id: 'gpt-4.1', name: 'GPT-4.1', provider: 'OpenAI' },
    { id: 'gpt-4.1-mini', name: 'GPT-4.1 Mini', provider: 'OpenAI' },
    { id: 'gpt-4.1-nano', name: 'GPT-4.1 Nano', provider: 'OpenAI' },
    { id: 'o3', name: 'o3', provider: 'OpenAI' },
    { id: 'o3-mini', name: 'o3 Mini', provider: 'OpenAI' },
    { id: 'o4-mini', name: 'o4 Mini', provider: 'OpenAI' },
    { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', provider: 'OpenAI' },
  ],
  anthropic: [
    { id: 'claude-sonnet-4-20250514', name: 'Claude Sonnet 4', provider: 'Anthropic' },
    { id: 'claude-opus-4-20250514', name: 'Claude Opus 4', provider: 'Anthropic' },
    { id: 'claude-3-7-sonnet-20250219', name: 'Claude 3.7 Sonnet', provider: 'Anthropic' },
    { id: 'claude-3-5-sonnet-20241022', name: 'Claude 3.5 Sonnet v2', provider: 'Anthropic' },
    { id: 'claude-3-5-haiku-20241022', name: 'Claude 3.5 Haiku', provider: 'Anthropic' },
    { id: 'claude-3-opus-20240229', name: 'Claude 3 Opus', provider: 'Anthropic' },
    { id: 'claude-3-haiku-20240307', name: 'Claude 3 Haiku', provider: 'Anthropic' },
  ],
  openrouter: [
    { id: 'anthropic/claude-sonnet-4', name: 'Claude Sonnet 4', provider: 'OpenRouter' },
    { id: 'anthropic/claude-opus-4', name: 'Claude Opus 4', provider: 'OpenRouter' },
    { id: 'anthropic/claude-3.7-sonnet', name: 'Claude 3.7 Sonnet', provider: 'OpenRouter' },
    { id: 'google/gemini-2.5-pro-preview', name: 'Gemini 2.5 Pro', provider: 'OpenRouter' },
    { id: 'google/gemini-2.5-flash', name: 'Gemini 2.5 Flash', provider: 'OpenRouter' },
    { id: 'google/gemini-2.0-flash-001', name: 'Gemini 2.0 Flash', provider: 'OpenRouter' },
    { id: 'openai/gpt-4o', name: 'GPT-4o', provider: 'OpenRouter' },
    { id: 'openai/gpt-4.1', name: 'GPT-4.1', provider: 'OpenRouter' },
    { id: 'mistralai/mistral-large', name: 'Mistral Large', provider: 'OpenRouter' },
    { id: 'mistralai/mistral-medium', name: 'Mistral Medium', provider: 'OpenRouter' },
    { id: 'meta-llama/llama-4-maverick', name: 'Llama 4 Maverick', provider: 'OpenRouter' },
    { id: 'meta-llama/llama-4-scout', name: 'Llama 4 Scout', provider: 'OpenRouter' },
    { id: 'deepseek/deepseek-r1', name: 'DeepSeek R1', provider: 'OpenRouter' },
    { id: 'deepseek/deepseek-chat-v3-0324', name: 'DeepSeek V3', provider: 'OpenRouter' },
    { id: 'qwen/qwen3-235b-a22b', name: 'Qwen3 235B', provider: 'OpenRouter' },
    { id: 'x-ai/grok-3-mini-beta', name: 'Grok 3 Mini', provider: 'OpenRouter' },
  ],
  groq: [
    { id: 'llama-3.3-70b-versatile', name: 'Llama 3.3 70B', provider: 'Groq' },
    { id: 'llama-3.1-8b-instant', name: 'Llama 3.1 8B', provider: 'Groq' },
    { id: 'llama3-70b-8192', name: 'Llama 3 70B', provider: 'Groq' },
    { id: 'mixtral-8x7b-32768', name: 'Mixtral 8x7B', provider: 'Groq' },
    { id: 'gemma2-9b-it', name: 'Gemma 2 9B', provider: 'Groq' },
  ],
}

export default function SettingsAiPage() {
  const [model, setModel] = useState('gigachat-pro')
  const [apiKeys, setApiKeys] = useState<Record<string, string>>({
    gigachat: '', openai: '', anthropic: '', openrouter: '', groq: '',
  })
  const [serverKeyStatus, setServerKeyStatus] = useState<Record<string, { has_key: boolean; masked_key: string }>>({})
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({})
  const [toggles, setToggles] = useState<Record<string, boolean>>(
    Object.fromEntries(TOGGLES.map(t => [t.id, t.default]))
  )
  const [saved, setSaved] = useState(false)
  const [saving, setSaving] = useState(false)
  const [serverModels, setServerModels] = useState<ModelOption[]>([])
  const [subModels, setSubModels] = useState<SubModel[]>([])
  const [selectedSubModel, setSelectedSubModel] = useState<string>('')
  const [loadingSubModels, setLoadingSubModels] = useState(false)
  const [subModelSearch, setSubModelSearch] = useState('')

  // Load settings from server
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const [keysRes, togglesRes, modelRes] = await Promise.all([
          api.getAIKeys().catch(() => null),
          api.getAIToggles().catch(() => null),
          api.getSelectedModel().catch(() => null),
        ])
        if (keysRes?.keys) {
          const status: Record<string, { has_key: boolean; masked_key: string }> = {}
          keysRes.keys.forEach(k => { status[k.provider] = { has_key: k.has_key, masked_key: k.masked_key } })
          setServerKeyStatus(status)
        }
        if (togglesRes?.toggles) setToggles(togglesRes.toggles)
        if (modelRes) {
          setModel(modelRes.model || 'gigachat-pro')
          setSelectedSubModel(modelRes.sub_model || '')
        }
      } catch { /* server unavailable, continue with defaults */ }
      // Clear legacy localStorage keys
      localStorage.removeItem('ai_settings')
    }
    loadSettings()
  }, [])

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
      setSubModelSearch('')
      return
    }
    let cancelled = false
    const fetchSub = async () => {
      setLoadingSubModels(true)
      try {
        // 1. Try server-side sub-models (uses saved API keys from DB or env)
        const res = await api.getSubModels(model)
        const list = (res.sub_models || []) as SubModel[]
        // Only use server list if it has models AND isn't a fallback/error response
        if (!cancelled && list.length > 0 && !res.error) {
          setSubModels(list)
          if (!selectedSubModel || !list.find((m: SubModel) => m.id === selectedSubModel)) setSelectedSubModel(list[0].id)
          setLoadingSubModels(false)
          return
        }
      } catch { /* server unavailable, fall through to fallback */ }
      if (cancelled) return
      // 2. Use comprehensive fallback list
      const fallback = FALLBACK_SUB_MODELS[model] || []
      setSubModels(fallback)
      if (fallback.length > 0 && !selectedSubModel) setSelectedSubModel(fallback[0].id)
      setLoadingSubModels(false)
    }
    fetchSub()
    return () => { cancelled = true }
  }, [model]) // eslint-disable-line react-hooks/exhaustive-deps

  const getServerAvailability = (modelId: string): boolean | null => {
    // LIVE-004: Показываем статус ТОЛЬКО на основе серверной доступности,
    // не показываем зелёную галочку только потому, что пользователь ввёл ключ локально
    const m = serverModels.find((s: any) => s.id === modelId)
    return m ? m.available ?? null : null
  }

  const toggle = (id: string) => setToggles({ ...toggles, [id]: !toggles[id] })

  const handleSave = async () => {
    setSaving(true)
    try {
      // Save API keys to server (encrypted)
      for (const m of MODELS) {
        const key = apiKeys[m.apiKeyField]?.trim()
        if (key) {
          await api.saveAIKey(m.apiKeyField, key)
        }
      }
      // Save toggles to server
      await api.saveAIToggles(Object.entries(toggles).map(([key, value]) => ({ key, value })))
      // Save selected model to server
      await api.saveSelectedModel(model, selectedSubModel || undefined)
      // Clear local input keys (server has them now)
      setApiKeys({ gigachat: '', openai: '', anthropic: '', openrouter: '' })
      // Refresh server key status
      const keysRes = await api.getAIKeys().catch(() => null)
      if (keysRes?.keys) {
        const status: Record<string, { has_key: boolean; masked_key: string }> = {}
        keysRes.keys.forEach(k => { status[k.provider] = { has_key: k.has_key, masked_key: k.masked_key } })
        setServerKeyStatus(status)
      }
      // Clear legacy localStorage
      localStorage.removeItem('ai_settings')
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch { /* save error */ }
    finally { setSaving(false) }
  }

  const handleReset = async () => {
    setModel('gigachat-pro')
    setToggles(Object.fromEntries(TOGGLES.map(t => [t.id, t.default])))
    setApiKeys({ gigachat: '', openai: '', anthropic: '', openrouter: '' })
    setSelectedSubModel('')
    localStorage.removeItem('ai_settings')
    // Delete all keys from server
    for (const provider of ['gigachat', 'openai', 'anthropic', 'openrouter']) {
      await api.deleteAIKey(provider).catch(() => {})
    }
    setServerKeyStatus({})
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
            <>
              {/* P3-1: Search filter for long model lists */}
              {subModels.length > 6 && (
                <input
                  className="input-field"
                  placeholder="Поиск модели..."
                  value={subModelSearch}
                  onChange={e => setSubModelSearch(e.target.value)}
                  style={{ width: '100%', marginBottom: '0.5rem' }}
                />
              )}
              <select
                className="input-field"
                value={selectedSubModel}
                onChange={e => setSelectedSubModel(e.target.value)}
                style={{ width: '100%' }}
              >
                {(() => {
                  const q = subModelSearch.toLowerCase()
                  const filtered = q ? subModels.filter(sm => sm.name.toLowerCase().includes(q) || sm.id.toLowerCase().includes(q)) : subModels
                  // Group by provider prefix (e.g. 'anthropic/', 'google/', 'openai/')
                  const groups: Record<string, SubModel[]> = {}
                  for (const sm of filtered) {
                    const slash = sm.id.indexOf('/')
                    const group = slash > 0 ? sm.id.slice(0, slash) : sm.provider
                    ;(groups[group] ??= []).push(sm)
                  }
                  const keys = Object.keys(groups)
                  if (keys.length <= 1) {
                    return filtered.map(sm => (
                      <option key={sm.id} value={sm.id}>{sm.name}</option>
                    ))
                  }
                  return keys.map(g => (
                    <optgroup key={g} label={g.charAt(0).toUpperCase() + g.slice(1)}>
                      {groups[g].map(sm => (
                        <option key={sm.id} value={sm.id}>{sm.name}</option>
                      ))}
                    </optgroup>
                  ))
                })()}
              </select>
            </>
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
        {MODELS.map(m => {
          const status = serverKeyStatus[m.apiKeyField]
          return (
          <div key={m.apiKeyField} className="input-group" style={{ marginBottom: '1rem' }}>
            <label className="input-label">
              {m.name} ({m.provider})
              {status?.has_key && (
                <span style={{ marginLeft: '0.5rem', fontSize: '0.75rem', color: 'var(--success, #059669)' }}>
                  ✓ Сохранён: {status.masked_key}
                </span>
              )}
            </label>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <input
                className="input-field"
                type={showKeys[m.apiKeyField] ? 'text' : 'password'}
                placeholder={status?.has_key ? `Текущий: ${status.masked_key}` : m.apiKeyPlaceholder}
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
          )
        })}
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
        <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
          <Save size={16} /> {saving ? 'Сохранение...' : saved ? '✓ Сохранено' : 'Сохранить'}
        </button>
        <button className="btn btn-secondary" onClick={handleReset}>
          <RotateCcw size={16} /> Сбросить
        </button>
      </div>
    </div>
  )
}

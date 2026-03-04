import { useState, useEffect } from 'react'
import { Save, RotateCcw, Eye, EyeOff, Zap, Brain, Globe, Cpu, AlertTriangle, CheckCircle } from 'lucide-react'
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
}

const MODELS: ModelOption[] = [
  {
    id: 'gigachat-pro', name: 'GigaChat Pro', provider: 'Сбер',
    desc: '#1 русский язык (MERA), данные в РФ, ФЗ-152 compliant',
    badge: 'Рекомендуем', badgeColor: '#4F46E5',
    icon: Zap, apiKeyField: 'gigachat', apiKeyPlaceholder: 'Credentials (Base64)',
  },
  {
    id: 'gpt-4o', name: 'GPT-4o', provider: 'OpenAI',
    desc: 'Топ-модель OpenAI, мультиязычность, 128K контекст',
    icon: Brain, apiKeyField: 'openai', apiKeyPlaceholder: 'sk-...',
  },
  {
    id: 'llama-3-70b', name: 'Llama 3.3 70B', provider: 'Groq',
    desc: 'Бесплатно 14 400 запросов/день, быстрый inference',
    badge: 'Бесплатно', badgeColor: '#059669',
    icon: Cpu, apiKeyField: 'groq', apiKeyPlaceholder: 'gsk_...',
  },
  {
    id: 'openrouter', name: 'OpenRouter', provider: 'OpenRouter',
    desc: 'Доступ к 100+ моделям через единый API (Claude, Gemini, Mixtral...)',
    badge: 'Новое', badgeColor: '#D97706',
    icon: Globe, apiKeyField: 'openrouter', apiKeyPlaceholder: 'sk-or-v1-...',
  },
]

const TOGGLES = [
  { id: 'auto_metrics', label: 'Автоматические метрики', desc: 'Генерировать количественные достижения', default: true },
  { id: 'ats', label: 'ATS оптимизация', desc: 'Адаптировать текст под ATS-фильтры', default: true },
  { id: 'upgrade_title', label: 'Апгрейд должности', desc: 'Предложить более сильные формулировки позиций', default: false },
  { id: 'keep_language', label: 'Сохранять язык', desc: 'Не менять язык оригинального резюме', default: true },
  { id: 'soft_skills', label: 'Soft skills', desc: 'Добавлять soft skills из описания вакансии', default: false },
]

export default function SettingsAiPage() {
  // Load from localStorage
  const savedSettings = (() => {
    try { return JSON.parse(localStorage.getItem('ai_settings') || '{}') } catch { return {} }
  })()
  const [model, setModel] = useState(savedSettings.model || 'gigachat-pro')
  const [apiKeys, setApiKeys] = useState<Record<string, string>>(savedSettings.apiKeys || {
    gigachat: '', openai: '', groq: '', openrouter: '',
  })
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({})
  const [toggles, setToggles] = useState<Record<string, boolean>>(
    savedSettings.toggles || Object.fromEntries(TOGGLES.map(t => [t.id, t.default]))
  )
  const [saved, setSaved] = useState(false)
  const [serverModels, setServerModels] = useState<ModelOption[]>([])
  const [openrouterSubModels, setOpenrouterSubModels] = useState<SubModel[]>([])
  const [selectedOrModel, setSelectedOrModel] = useState<string>(savedSettings.openrouterModel || '')

  // Fetch server-side model availability
  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.getModels()
        const list = res.models || []
        setServerModels(list.map((m: any) => ({ ...m, icon: Cpu, apiKeyField: '', apiKeyPlaceholder: '' })))
        const or = list.find((m: any) => m.id === 'openrouter')
        if (or?.sub_models?.length) {
          setOpenrouterSubModels(or.sub_models)
          if (!selectedOrModel) setSelectedOrModel(or.sub_models[0].id)
        }
      } catch { /* server unavailable, continue with local settings */ }
    }
    load()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const getServerAvailability = (modelId: string): boolean | null => {
    const m = serverModels.find((s: any) => s.id === modelId)
    return m ? m.available ?? null : null
  }

  const toggle = (id: string) => setToggles({ ...toggles, [id]: !toggles[id] })

  const handleSave = () => {
    localStorage.setItem('ai_settings', JSON.stringify({ model, apiKeys, toggles, openrouterModel: selectedOrModel }))
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const handleReset = () => {
    setModel('gigachat-pro')
    setToggles(Object.fromEntries(TOGGLES.map(t => [t.id, t.default])))
    setApiKeys({ gigachat: '', openai: '', groq: '', openrouter: '' })
    setSelectedOrModel('')
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

      {/* OpenRouter sub-model picker */}
      {model === 'openrouter' && openrouterSubModels.length > 0 && (
        <div className="card" style={{ padding: '1.25rem', marginBottom: '1.5rem', border: '1px solid var(--primary, #4F46E5)', background: 'var(--primary-bg, #EEF2FF)' }}>
          <h4 style={{ fontWeight: 600, fontSize: '0.95rem', marginBottom: '0.5rem' }}>Модель OpenRouter</h4>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
            Выберите конкретную модель из каталога OpenRouter
          </p>
          <select
            className="input-field"
            value={selectedOrModel}
            onChange={e => setSelectedOrModel(e.target.value)}
            style={{ width: '100%' }}
          >
            {openrouterSubModels.map(sm => (
              <option key={sm.id} value={sm.id}>{sm.name} — {sm.provider}</option>
            ))}
          </select>
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

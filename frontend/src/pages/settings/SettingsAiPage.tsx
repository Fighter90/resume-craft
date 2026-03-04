import { useState } from 'react'
import { Save } from 'lucide-react'

const TOGGLES = [
  { id: 'ats', label: 'ATS-оптимизация', desc: 'Адаптировать текст под ATS-фильтры', default: true },
  { id: 'keywords', label: 'Добавление ключевых слов', desc: 'Автоматически добавлять релевантные keywords', default: true },
  { id: 'metrics', label: 'Метрики достижений', desc: 'Генерировать количественные метрики', default: true },
  { id: 'structure', label: 'Реструктуризация', desc: 'Оптимизировать порядок секций', default: false },
  { id: 'creative', label: 'Креативные формулировки', desc: 'Нестандартные фразы и обороты', default: false },
]

export default function SettingsAiPage() {
  const [model, setModel] = useState('gigachat-pro')
  const [toggles, setToggles] = useState<Record<string, boolean>>(
    Object.fromEntries(TOGGLES.map(t => [t.id, t.default]))
  )

  const toggle = (id: string) => setToggles({ ...toggles, [id]: !toggles[id] })

  return (
    <div style={{ maxWidth: 640 }}>
      {/* Model selection */}
      <div className="card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
        <h3 style={{ fontWeight: 600, marginBottom: '1rem' }}>AI-модель по умолчанию</h3>
        <select
          className="input-field select-field"
          value={model}
          onChange={e => setModel(e.target.value)}
        >
          <option value="gigachat-pro">GigaChat Pro (рекомендуем)</option>
          <option value="gpt-4o">GPT-4o</option>
          <option value="llama-3-70b">Llama 3.3 70B (Groq)</option>
        </select>
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

      <button className="btn btn-primary" style={{ marginTop: '1.25rem' }}>
        <Save size={16} /> Сохранить
      </button>
    </div>
  )
}

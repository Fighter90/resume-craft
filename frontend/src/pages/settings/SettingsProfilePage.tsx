import { useState } from 'react'
import { Camera, Save } from 'lucide-react'

export default function SettingsProfilePage() {
  const [form, setForm] = useState({
    name: 'Алексей Петров',
    email: 'aleksey@example.com',
    phone: '+7 (999) 123-45-67',
    city: 'Москва',
    position: 'Product Manager',
    bio: 'Product Manager с 6+ лет опыта в IT-продуктах. Специализация — Growth, монетизация SaaS, интеграция AI.',
  })

  const onChange = (key: string, value: string) => setForm({ ...form, [key]: value })

  return (
    <div className="card" style={{ padding: '1.5rem', maxWidth: 640 }}>
      {/* Avatar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
        <div style={{
          width: 72, height: 72, borderRadius: '50%', background: 'var(--primary-gradient)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#fff', fontSize: '1.5rem', fontWeight: 700, position: 'relative',
        }}>
          АП
          <button style={{
            position: 'absolute', bottom: -2, right: -2, width: 26, height: 26, borderRadius: '50%',
            background: 'var(--card-bg)', border: '2px solid var(--border)', display: 'flex',
            alignItems: 'center', justifyContent: 'center', cursor: 'pointer', padding: 0,
          }}>
            <Camera size={12} />
          </button>
        </div>
        <div>
          <div style={{ fontWeight: 600 }}>{form.name}</div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{form.email}</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        <div className="input-group">
          <label className="input-label">Имя и фамилия</label>
          <input className="input-field" value={form.name} onChange={e => onChange('name', e.target.value)} />
        </div>
        <div className="input-group">
          <label className="input-label">Email</label>
          <input className="input-field" type="email" value={form.email} onChange={e => onChange('email', e.target.value)} />
        </div>
        <div className="input-group">
          <label className="input-label">Телефон</label>
          <input className="input-field" value={form.phone} onChange={e => onChange('phone', e.target.value)} />
        </div>
        <div className="input-group">
          <label className="input-label">Город</label>
          <input className="input-field" value={form.city} onChange={e => onChange('city', e.target.value)} />
        </div>
        <div className="input-group" style={{ gridColumn: '1 / -1' }}>
          <label className="input-label">Текущая должность</label>
          <input className="input-field" value={form.position} onChange={e => onChange('position', e.target.value)} />
        </div>
        <div className="input-group" style={{ gridColumn: '1 / -1' }}>
          <label className="input-label">О себе</label>
          <textarea className="input-field" rows={3} value={form.bio} onChange={e => onChange('bio', e.target.value)} />
        </div>
      </div>

      <button className="btn btn-primary" style={{ marginTop: '1.25rem' }}>
        <Save size={16} /> Сохранить
      </button>
    </div>
  )
}

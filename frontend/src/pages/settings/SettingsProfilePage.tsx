import { useState, useRef } from 'react'
import { Camera, Save, Upload, Trash2, CheckCircle } from 'lucide-react'

export default function SettingsProfilePage() {
  const [form, setForm] = useState({
    firstName: 'Алексей',
    lastName: 'Петров',
    email: 'aleksey@example.com',
    phone: '+7 (999) 123-45-67',
    city: 'Москва',
    position: 'Product Manager',
    bio: 'Product Manager с 6+ лет опыта в IT-продуктах. Специализация — Growth, монетизация SaaS, интеграция AI.',
  })
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null)
  const [saveMsg, setSaveMsg] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const onChange = (key: string, value: string) => setForm({ ...form, [key]: value })

  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && file.type.startsWith('image/')) {
      const url = URL.createObjectURL(file)
      setAvatarUrl(url)
    }
  }

  const handleRemovePhoto = () => {
    setAvatarUrl(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handleSave = () => {
    setSaveMsg('Изменения сохранены')
    setTimeout(() => setSaveMsg(null), 2000)
  }

  return (
    <div className="card" style={{ padding: '1.5rem', maxWidth: 640 }}>
      {/* Hidden file input for photo */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handlePhotoUpload}
        style={{ display: 'none' }}
        data-testid="photo-upload-input"
      />

      {/* Avatar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
        <div style={{
          width: 72, height: 72, borderRadius: '50%',
          background: avatarUrl ? `url(${avatarUrl}) center/cover no-repeat` : 'var(--primary-gradient)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#fff', fontSize: '1.5rem', fontWeight: 700, position: 'relative',
          overflow: 'hidden',
        }}>
          {!avatarUrl && 'АП'}
          <button
            onClick={() => fileInputRef.current?.click()}
            style={{
              position: 'absolute', bottom: -2, right: -2, width: 26, height: 26, borderRadius: '50%',
              background: 'var(--card-bg)', border: '2px solid var(--border)', display: 'flex',
              alignItems: 'center', justifyContent: 'center', cursor: 'pointer', padding: 0,
            }}
          >
            <Camera size={12} />
          </button>
        </div>
        <div>
          <div style={{ fontWeight: 600 }}>{form.firstName} {form.lastName}</div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            {form.email}
            <CheckCircle size={14} style={{ color: 'var(--success)' }} />
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
            <button className="btn btn-secondary btn-sm" style={{ fontSize: '0.75rem', padding: '0.25rem 0.6rem' }}
              onClick={() => fileInputRef.current?.click()}>
              <Upload size={12} /> Загрузить фото
            </button>
            <button className="btn btn-ghost btn-sm" style={{ fontSize: '0.75rem', padding: '0.25rem 0.6rem', color: 'var(--danger)' }}
              onClick={handleRemovePhoto} disabled={!avatarUrl}>
              <Trash2 size={12} /> Удалить
            </button>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        <div className="input-group">
          <label className="input-label">Имя</label>
          <input className="input-field" value={form.firstName} onChange={e => onChange('firstName', e.target.value)} />
        </div>
        <div className="input-group">
          <label className="input-label">Фамилия</label>
          <input className="input-field" value={form.lastName} onChange={e => onChange('lastName', e.target.value)} />
        </div>
        <div className="input-group">
          <label className="input-label">Email</label>
          <div style={{ position: 'relative' }}>
            <input className="input-field" type="email" value={form.email} onChange={e => onChange('email', e.target.value)} />
            <span style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', display: 'flex', alignItems: 'center', gap: '0.25rem', color: 'var(--success)', fontSize: '0.75rem' }}>
              <CheckCircle size={14} /> Подтверждён
            </span>
          </div>
        </div>
        <div className="input-group">
          <label className="input-label">Телефон</label>
          <input className="input-field" value={form.phone} onChange={e => onChange('phone', e.target.value)} />
        </div>
        <div className="input-group">
          <label className="input-label">Город</label>
          <select className="input-field select-field" value={form.city} onChange={e => onChange('city', e.target.value)}>
            <option>Москва</option>
            <option>Санкт-Петербург</option>
            <option>Новосибирск</option>
            <option>Екатеринбург</option>
            <option>Казань</option>
            <option>Другой</option>
          </select>
        </div>
        <div className="input-group">
          <label className="input-label">Текущая должность</label>
          <input className="input-field" value={form.position} onChange={e => onChange('position', e.target.value)} />
        </div>
        <div className="input-group" style={{ gridColumn: '1 / -1' }}>
          <label className="input-label">О себе</label>
          <textarea className="input-field" rows={3} value={form.bio} onChange={e => onChange('bio', e.target.value)} />
        </div>
      </div>

      {saveMsg && (
        <div style={{ padding: '0.75rem 1rem', borderRadius: 8, marginTop: '1rem', fontSize: '0.9rem',
          background: 'var(--success-light, #D1FAE5)', color: 'var(--success, #059669)' }}>
          {saveMsg}
        </div>
      )}
      <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.25rem' }}>
        <button className="btn btn-secondary">Отмена</button>
        <button className="btn btn-primary" onClick={handleSave}>
          <Save size={16} /> Сохранить изменения
        </button>
      </div>
    </div>
  )
}

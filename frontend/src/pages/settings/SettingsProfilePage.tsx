import { useState, useRef } from 'react'
import { Camera, Save, Upload, Trash2, CheckCircle, Loader } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { api } from '../../services/api'

export default function SettingsProfilePage() {
  const { user, refreshUser } = useAuth()
  const nameParts = (user?.full_name || '').split(' ')
  const [form, setForm] = useState({
    firstName: nameParts[0] || '',
    lastName: nameParts.slice(1).join(' ') || '',
    email: user?.email || '',
  })

  // Avatar from server (user.avatar_url), with localStorage migration
  const [avatarUrl, setAvatarUrl] = useState<string | null>((user as any)?.avatar_url || null)
  const [avatarUploading, setAvatarUploading] = useState(false)
  const [saveMsg, setSaveMsg] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Migrate old localStorage avatar on mount (one-time)
  useState(() => {
    const oldKey = `user_avatar_${user?.id || 'default'}`
    try { localStorage.removeItem(oldKey) } catch { /* ignore */ }
  })

  const onChange = (key: string, value: string) => setForm({ ...form, [key]: value })

  const handlePhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && file.type.startsWith('image/')) {
      setAvatarUploading(true)
      try {
        const res = await api.uploadAvatar(file)
        // Server returns avatar URL in message field
        setAvatarUrl(res.message)
        await refreshUser()
      } catch (err) {
        setSaveMsg(err instanceof Error ? err.message : 'Ошибка загрузки аватара')
        setTimeout(() => setSaveMsg(null), 3000)
      } finally {
        setAvatarUploading(false)
      }
    }
  }

  const handleRemovePhoto = async () => {
    setAvatarUploading(true)
    try {
      await api.deleteAvatar()
      setAvatarUrl(null)
      await refreshUser()
    } catch { /* ignore */ }
    finally { setAvatarUploading(false) }
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handleSave = async () => {
    setSaving(true)
    setSaveMsg(null)
    try {
      const fullName = `${form.firstName} ${form.lastName}`.trim()
      await api.updateProfile({ full_name: fullName || undefined, email: form.email || undefined })
      await refreshUser()
      setSaveMsg('Изменения сохранены')
      setTimeout(() => setSaveMsg(null), 3000)
    } catch (err) {
      setSaveMsg(err instanceof Error ? err.message : 'Ошибка сохранения')
    } finally {
      setSaving(false)
    }
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
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        <div style={{ width: 72, height: 72, minWidth: 72, minHeight: 72, position: 'relative', flexShrink: 0 }}>
          <div style={{
            width: '100%', height: '100%', borderRadius: '50%', overflow: 'hidden',
            background: avatarUrl ? `url(${avatarUrl}) center/cover no-repeat` : 'var(--primary-gradient)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', fontSize: '1.5rem', fontWeight: 700,
          }}>
            {!avatarUrl && ((form.firstName?.charAt(0) || '') + (form.lastName?.charAt(0) || '') || '??').toUpperCase()}
          </div>
          <button
            onClick={() => fileInputRef.current?.click()}
            style={{
              position: 'absolute', bottom: 0, right: 0, width: 26, height: 26, borderRadius: '50%',
              background: 'var(--card-bg)', border: '2px solid var(--border)', display: 'flex',
              alignItems: 'center', justifyContent: 'center', cursor: 'pointer', padding: 0, zIndex: 1,
            }}
          >
            <Camera size={12} />
          </button>
        </div>
        <div style={{ minWidth: 0, flex: 1, overflow: 'hidden' }}>
          <div style={{ fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{form.firstName} {form.lastName}</div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.35rem', maxWidth: '100%', overflow: 'hidden' }}>
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', minWidth: 0, flex: '1 1 auto' }} title={form.email}>{form.email}</span>
            <CheckCircle size={14} style={{ color: 'var(--success)', flexShrink: 0 }} />
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
            <button className="btn btn-secondary btn-sm" style={{ fontSize: '0.75rem', padding: '0.25rem 0.6rem' }}
              onClick={() => fileInputRef.current?.click()}>
              <Upload size={12} /> {avatarUploading ? 'Загрузка...' : 'Загрузить фото'}
            </button>
            <button className="btn btn-ghost btn-sm" style={{ fontSize: '0.75rem', padding: '0.25rem 0.6rem', color: 'var(--danger)' }}
              onClick={handleRemovePhoto} disabled={!avatarUrl || avatarUploading}>
              <Trash2 size={12} /> Удалить
            </button>
          </div>
        </div>
      </div>

      <div className="profile-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
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
            <input className="input-field" type="email" value={form.email} onChange={e => onChange('email', e.target.value)} style={{ paddingRight: '7.5rem' }} />
            <span style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', display: 'flex', alignItems: 'center', gap: '0.25rem', color: 'var(--success)', fontSize: '0.75rem', background: 'var(--card-bg, #fff)', paddingLeft: 4 }}>
              <CheckCircle size={14} /> Подтверждён
            </span>
          </div>
        </div>
        <div className="input-group">
          <label className="input-label">Телефон</label>
          <input className="input-field" placeholder="+7 (___) ___-__-__" disabled style={{ opacity: 0.6 }} title="Функция в разработке" />
        </div>
        <div className="input-group">
          <label className="input-label">Город</label>
          <select className="input-field select-field" disabled style={{ opacity: 0.6 }}>
            <option>Москва</option>
            <option>Санкт-Петербург</option>
            <option>Новосибирск</option>
            <option>Екатеринбург</option>
            <option>Казань</option>
            <option>Другой</option>
          </select>
        </div>
      </div>

      {saveMsg && (
        <div style={{ padding: '0.75rem 1rem', borderRadius: 8, marginTop: '1rem', fontSize: '0.9rem',
          background: saveMsg.includes('Ошибка') ? 'var(--danger-light, #FEF2F2)' : 'var(--success-light, #D1FAE5)',
          color: saveMsg.includes('Ошибка') ? 'var(--danger, #EF4444)' : 'var(--success, #059669)' }}>
          {saveMsg}
        </div>
      )}
      <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.25rem' }}>
        <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
          {saving ? <><Loader size={16} className="spin" /> Сохранение...</> : <><Save size={16} /> Сохранить изменения</>}
        </button>
      </div>
    </div>
  )
}

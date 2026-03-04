import { useState } from 'react'
import { Shield, Smartphone, Monitor, AlertTriangle, Save } from 'lucide-react'

const SESSIONS = [
  { device: 'Chrome — macOS', location: 'Москва, Россия', time: 'Сейчас', current: true },
  { device: 'Safari — iPhone', location: 'Москва, Россия', time: '2 часа назад', current: false },
  { device: 'Firefox — Windows', location: 'Санкт-Петербург, Россия', time: 'Вчера', current: false },
]

export default function SettingsSecurityPage() {
  const [twofa, setTwofa] = useState(false)
  const [showDelete, setShowDelete] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState('')
  const [pwForm, setPwForm] = useState({ current: '', newPw: '', confirm: '' })
  const [pwMessage, setPwMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const handlePwChange = (key: string, value: string) => setPwForm({ ...pwForm, [key]: value })

  const handlePwSubmit = () => {
    setPwMessage(null)
    if (!pwForm.current || !pwForm.newPw || !pwForm.confirm) {
      setPwMessage({ type: 'error', text: 'Заполните все поля' })
      return
    }
    if (pwForm.newPw.length < 8) {
      setPwMessage({ type: 'error', text: 'Пароль должен быть минимум 8 символов' })
      return
    }
    if (pwForm.newPw !== pwForm.confirm) {
      setPwMessage({ type: 'error', text: 'Пароли не совпадают' })
      return
    }
    setPwMessage({ type: 'success', text: 'Пароль успешно обновлён' })
    setPwForm({ current: '', newPw: '', confirm: '' })
  }

  return (
    <div style={{ maxWidth: 640 }}>
      {/* Change password */}
      <div className="card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
        <h3 style={{ fontWeight: 600, marginBottom: '1rem' }}>Сменить пароль</h3>
        {pwMessage && (
          <div style={{ padding: '0.75rem 1rem', borderRadius: 8, marginBottom: '1rem', fontSize: '0.9rem',
            background: pwMessage.type === 'success' ? 'var(--success-light, #D1FAE5)' : 'var(--danger-light, #FEF2F2)',
            color: pwMessage.type === 'success' ? 'var(--success, #059669)' : 'var(--danger, #EF4444)',
          }}>
            {pwMessage.text}
          </div>
        )}
        <div className="input-group" style={{ marginBottom: '1rem' }}>
          <label className="input-label">Текущий пароль</label>
          <input className="input-field" type="password" placeholder="••••••••"
            value={pwForm.current} onChange={e => handlePwChange('current', e.target.value)} />
        </div>
        <div className="input-group" style={{ marginBottom: '1rem' }}>
          <label className="input-label">Новый пароль</label>
          <input className="input-field" type="password" placeholder="Мин. 8 символов, цифра + буква"
            value={pwForm.newPw} onChange={e => handlePwChange('newPw', e.target.value)} />
        </div>
        <div className="input-group" style={{ marginBottom: '1rem' }}>
          <label className="input-label">Подтвердите пароль</label>
          <input className="input-field" type="password" placeholder="••••••••"
            value={pwForm.confirm} onChange={e => handlePwChange('confirm', e.target.value)} />
        </div>
        <button className="btn btn-primary" onClick={handlePwSubmit}><Save size={16} /> Обновить пароль</button>
      </div>

      {/* 2FA */}
      <div className="card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Shield size={20} style={{ color: 'var(--primary)' }} />
            <div>
              <div style={{ fontWeight: 600 }}>Двухфакторная аутентификация</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>SMS или приложение-аутентификатор</div>
            </div>
          </div>
          <label className="toggle-switch">
            <input type="checkbox" checked={twofa} onChange={() => setTwofa(!twofa)} />
            <span className="toggle-slider" />
          </label>
        </div>
      </div>

      {/* Active sessions */}
      <div className="card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
        <h3 style={{ fontWeight: 600, marginBottom: '1rem' }}>Активные сессии</h3>
        {SESSIONS.map((s, i) => (
          <div key={i} className="session-item" style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            padding: '0.75rem 0', borderBottom: i < SESSIONS.length - 1 ? '1px solid var(--border)' : 'none',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              {s.device.includes('iPhone') ? <Smartphone size={18} /> : <Monitor size={18} />}
              <div>
                <div style={{ fontWeight: 500, fontSize: '0.9rem' }}>
                  {s.device} {s.current && <span className="badge badge-green" style={{ marginLeft: '0.5rem' }}>Текущая</span>}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{s.location} · {s.time}</div>
              </div>
            </div>
            {!s.current && (
              <button className="btn btn-secondary btn-sm" style={{ fontSize: '0.78rem' }}>Завершить</button>
            )}
          </div>
        ))}
      </div>

      {/* Danger zone */}
      <div className="card" style={{ padding: '1.5rem', border: '1px solid var(--danger)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', color: 'var(--danger)' }}>
          <AlertTriangle size={18} />
          <h3 style={{ fontWeight: 600 }}>Опасная зона</h3>
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
          Удаление аккаунта безвозвратно. Все данные, резюме и история будут потеряны.
        </p>
        {!showDelete ? (
          <button className="btn" onClick={() => setShowDelete(true)} style={{ background: 'var(--danger)', color: '#fff' }}>
            Удалить аккаунт
          </button>
        ) : (
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <input className="input-field" placeholder='Введите "УДАЛИТЬ" для подтверждения' style={{ flex: 1 }}
              value={deleteConfirm} onChange={e => setDeleteConfirm(e.target.value)} />
            <button className="btn" style={{ background: 'var(--danger)', color: '#fff' }} disabled={deleteConfirm !== 'УДАЛИТЬ'}>Подтвердить</button>
            <button className="btn btn-secondary" onClick={() => { setShowDelete(false); setDeleteConfirm('') }}>Отмена</button>
          </div>
        )}
      </div>
    </div>
  )
}

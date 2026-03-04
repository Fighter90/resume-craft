import { useState } from 'react'
import { Shield, AlertTriangle, Save, Loader } from 'lucide-react'
import { api } from '../../services/api'

export default function SettingsSecurityPage() {
  const [showDelete, setShowDelete] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState('')
  const [pwForm, setPwForm] = useState({ current: '', newPw: '', confirm: '' })
  const [pwMessage, setPwMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const [pwLoading, setPwLoading] = useState(false)

  const handlePwChange = (key: string, value: string) => setPwForm({ ...pwForm, [key]: value })

  const handlePwSubmit = async () => {
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
    setPwLoading(true)
    try {
      await api.changePassword({ current_password: pwForm.current, new_password: pwForm.newPw })
      setPwMessage({ type: 'success', text: 'Пароль успешно обновлён' })
      setPwForm({ current: '', newPw: '', confirm: '' })
    } catch (err) {
      setPwMessage({ type: 'error', text: err instanceof Error ? err.message : 'Ошибка смены пароля' })
    } finally {
      setPwLoading(false)
    }
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
        <button className="btn btn-primary" onClick={handlePwSubmit} disabled={pwLoading}>
          {pwLoading ? <><Loader size={16} className="spin" /> Обновление...</> : <><Save size={16} /> Обновить пароль</>}
        </button>
      </div>

      {/* 2FA */}
      <div className="card" style={{ padding: '1.5rem', marginBottom: '1.5rem', opacity: 0.6 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Shield size={20} style={{ color: 'var(--primary)' }} />
            <div>
              <div style={{ fontWeight: 600 }}>Двухфакторная аутентификация</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Будет доступно в следующем обновлении</div>
            </div>
          </div>
          <span className="badge badge-gray">Скоро</span>
        </div>
      </div>

      {/* Active sessions — placeholder */}
      <div className="card" style={{ padding: '1.5rem', marginBottom: '1.5rem', opacity: 0.6 }}>
        <h3 style={{ fontWeight: 600, marginBottom: '0.5rem' }}>Активные сессии</h3>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Управление сессиями будет доступно в следующем обновлении</p>
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

import { Link } from 'react-router-dom'
import { Lock } from 'lucide-react'

export default function PasswordRecoveryPage() {
  return (
    <div className="card" style={{ padding: '2.5rem', maxWidth: 420, width: '100%', textAlign: 'center' }}>
      <div style={{
        width: 56, height: 56, borderRadius: 16, background: 'var(--primary-light)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem', color: 'var(--primary)'
      }}>
        <Lock size={24} />
      </div>
      <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>Восстановление пароля</h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '0.95rem' }}>
        Введите email вашего аккаунта. Мы отправим ссылку для сброса пароля.
      </p>
      <form onSubmit={e => e.preventDefault()}>
        <div className="input-group" style={{ marginBottom: '1rem', textAlign: 'left' }}>
          <label className="input-label">Email</label>
          <input type="email" className="input-field" placeholder="alex@example.com" />
        </div>
        <Link to="/email-verify" className="btn btn-primary btn-block">Отправить ссылку</Link>
      </form>
      <Link to="/auth" style={{ display: 'block', marginTop: '1.5rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
        ← Вернуться к входу
      </Link>
    </div>
  )
}

import { Link } from 'react-router-dom'
import { Mail } from 'lucide-react'

export default function EmailVerifyPage() {
  return (
    <div className="card" style={{ padding: '2.5rem', maxWidth: 420, width: '100%', textAlign: 'center' }}>
      <div style={{
        width: 72, height: 72, borderRadius: '50%', background: 'var(--success-light)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem', color: 'var(--success)',
        animation: 'float-orb 3s ease-in-out infinite'
      }}>
        <Mail size={32} />
      </div>
      <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>Проверьте почту</h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
        Мы отправили письмо на <strong>alex@example.com</strong>
      </p>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '1.5rem' }}>
        Нажмите на ссылку в письме для подтверждения аккаунта. Письмо придёт в течение 1–2 минут.
      </p>
      <Link to="/app/dashboard" className="btn btn-primary btn-block">Я подтвердил email</Link>
      <div style={{ display: 'flex', justifyContent: 'center', gap: '1.5rem', marginTop: '1rem' }}>
        <button className="btn btn-ghost" style={{ color: 'var(--primary)' }}>Отправить повторно</button>
        <Link to="/auth" className="btn btn-ghost">Изменить email</Link>
      </div>
    </div>
  )
}

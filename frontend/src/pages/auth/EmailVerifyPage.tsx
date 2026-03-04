import { Link } from 'react-router-dom'
import { Mail, Info } from 'lucide-react'

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
      <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>Аккаунт создан!</h2>

      <div style={{
        background: '#F0F9FF', border: '1px solid #BAE6FD', borderRadius: 12,
        padding: '1rem 1.25rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'flex-start', gap: '0.75rem', textAlign: 'left'
      }}>
        <Info size={20} style={{ color: '#0284C7', flexShrink: 0, marginTop: 2 }} />
        <div style={{ fontSize: '0.9rem', color: '#0369A1', lineHeight: 1.5 }}>
          Верификация email будет доступна в следующем обновлении.
          Вы можете начать пользоваться сервисом прямо сейчас.
        </div>
      </div>

      <Link to="/app/dashboard" className="btn btn-primary btn-block">Перейти в личный кабинет</Link>
      <Link to="/auth" style={{ display: 'block', marginTop: '1rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
        ← Вернуться к входу
      </Link>
    </div>
  )
}

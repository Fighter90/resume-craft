import { Link } from 'react-router-dom'
import { Lock, Info } from 'lucide-react'

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

      <div style={{
        background: '#F0F9FF', border: '1px solid #BAE6FD', borderRadius: 12,
        padding: '1rem 1.25rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'flex-start', gap: '0.75rem', textAlign: 'left'
      }}>
        <Info size={20} style={{ color: '#0284C7', flexShrink: 0, marginTop: 2 }} />
        <div style={{ fontSize: '0.9rem', color: '#0369A1', lineHeight: 1.5 }}>
          Функция восстановления пароля будет доступна в следующем обновлении.
          Если вы забыли пароль, обратитесь в поддержку.
        </div>
      </div>

      <Link to="/auth" className="btn btn-primary btn-block">
        ← Вернуться к входу
      </Link>
    </div>
  )
}

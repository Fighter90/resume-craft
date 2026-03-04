import { useState } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'

export default function AuthPage() {
  const [searchParams] = useSearchParams()
  const [tab, setTab] = useState<'login' | 'register'>(searchParams.get('tab') === 'register' ? 'register' : 'login')
  const [method, setMethod] = useState<'email' | 'phone'>('email')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login, register } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (tab === 'login') {
        await login(email, password)
      } else {
        await register(email, password)
      }
      navigate('/app/dashboard')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-split">
      {/* Visual side */}
      <div className="auth-visual">
        <div style={{ textAlign: 'center', color: 'white', position: 'relative', zIndex: 1 }}>
          <div style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '1rem' }}>ResumeCraft</div>
          <p style={{ opacity: 0.85 }}>AI-оптимизация резюме для российского рынка труда</p>
        </div>
        <div className="floating-orb" style={{ width: 200, height: 200, background: 'rgba(255,255,255,0.1)', top: '10%', left: '10%' }} />
        <div className="floating-orb" style={{ width: 150, height: 150, background: 'rgba(255,255,255,0.08)', bottom: '15%', right: '15%', animationDelay: '2s' }} />
      </div>

      {/* Form side */}
      <div className="auth-form-side">
        <div className="auth-form-container">
          <h2 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.5rem' }}>
            {tab === 'login' ? 'Вход в аккаунт' : 'Создание аккаунта'}
          </h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
            {tab === 'login' ? 'Войдите, чтобы продолжить' : 'Начните оптимизировать резюме бесплатно'}
          </p>

          {/* Auth tabs */}
          <div className="tab-bar" style={{ marginBottom: '1.5rem' }}>
            <div className={`tab-bar-item${tab === 'register' ? ' active' : ''}`} onClick={() => setTab('register')}>
              Регистрация
            </div>
            <div className={`tab-bar-item${tab === 'login' ? ' active' : ''}`} onClick={() => setTab('login')}>
              Войти
            </div>
          </div>

          {/* Method tabs */}
          <div className="method-tabs">
            <button className={`method-tab${method === 'phone' ? ' active' : ''}`} onClick={() => setMethod('phone')}>
              Телефон
            </button>
            <button className={`method-tab${method === 'email' ? ' active' : ''}`} onClick={() => setMethod('email')}>
              Почта
            </button>
          </div>

          {error && (
            <div style={{ background: 'var(--danger-light)', color: 'var(--danger)', padding: '0.75rem 1rem', borderRadius: 8, marginBottom: '1rem', fontSize: '0.9rem' }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {method === 'phone' ? (
              <div className="input-group" style={{ marginBottom: '1rem' }}>
                <label className="input-label">Телефон</label>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <div style={{ padding: '0.875rem 1rem', border: '1px solid #E5E7EB', borderRadius: 12, background: '#F9FAFB', fontSize: '0.95rem', flexShrink: 0 }}>
                    🇷🇺 +7
                  </div>
                  <input type="tel" className="input-field" placeholder="(999) 123-45-67" />
                </div>
              </div>
            ) : (
              <>
                <div className="input-group" style={{ marginBottom: '1rem' }}>
                  <label className="input-label">Email</label>
                  <input
                    type="email" className="input-field" placeholder="alex@example.com"
                    value={email} onChange={e => setEmail(e.target.value)} required
                  />
                </div>
                <div className="input-group" style={{ marginBottom: '1rem' }}>
                  <label className="input-label">Пароль</label>
                  <input
                    type="password" className="input-field" placeholder="Минимум 8 символов"
                    value={password} onChange={e => setPassword(e.target.value)} required minLength={8}
                  />
                  {tab === 'login' && (
                    <Link to="/password-recovery" style={{ display: 'block', textAlign: 'right', fontSize: '0.85rem', color: 'var(--primary)', marginTop: '0.5rem' }}>
                      Забыли пароль?
                    </Link>
                  )}
                </div>
              </>
            )}

            <button type="submit" className="btn btn-primary btn-block" disabled={loading} style={{ marginTop: '0.5rem' }}>
              {loading ? 'Загрузка...' : tab === 'login' ? 'Войти' : 'Продолжить'}
            </button>
          </form>

          <p style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', textAlign: 'center', marginTop: '1.5rem', lineHeight: 1.5 }}>
            Нажимая «Продолжить», вы соглашаетесь с{' '}
            <a href="#" style={{ color: 'var(--primary)' }}>Условиями использования</a> и{' '}
            <a href="#" style={{ color: 'var(--primary)' }}>Политикой конфиденциальности</a>
          </p>
        </div>
      </div>
    </div>
  )
}

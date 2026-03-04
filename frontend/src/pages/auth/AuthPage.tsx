import { useState } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { ArrowLeft } from 'lucide-react'

/* ──────── CSS for auth animations (injected once) ──────── */
const authStyles = `
/* Animated orbs */
.orb{position:absolute;border-radius:50%;filter:blur(40px);opacity:.5}
.orb-1{width:300px;height:300px;background:#7C3AED;top:-50px;left:-50px;animation:orbFloat 8s ease-in-out infinite}
.orb-2{width:250px;height:250px;background:#4F46E5;bottom:-30px;right:-30px;animation:orbFloat 10s ease-in-out infinite;animation-delay:-3s}
.orb-3{width:180px;height:180px;background:#818CF8;top:50%;left:50%;transform:translate(-50%,-50%);animation:orbFloat3 12s ease-in-out infinite;animation-delay:-5s}
@keyframes orbFloat{0%,100%{transform:translate(0,0)scale(1)}25%{transform:translate(30px,-20px)scale(1.05)}50%{transform:translate(-20px,30px)scale(.95)}75%{transform:translate(20px,20px)scale(1.02)}}
@keyframes orbFloat3{0%,100%{transform:translate(-50%,-50%)scale(1)}25%{transform:translate(-40%,-60%)scale(1.08)}50%{transform:translate(-60%,-40%)scale(.92)}75%{transform:translate(-45%,-55%)scale(1.05)}}

/* Floating resume card */
.resume-card{width:280px;height:380px;background:rgba(255,255,255,.95);backdrop-filter:blur(20px);border-radius:24px;position:relative;box-shadow:0 25px 60px rgba(79,70,229,.25);display:flex;flex-direction:column;padding:2rem 1.5rem;animation:cardFloat 6s ease-in-out infinite;z-index:2}
@keyframes cardFloat{0%,100%{transform:translateY(0)}50%{transform:translateY(-12px)}}

/* Skeleton lines */
.skel{border-radius:4px}
.skel-header{height:10px;background:var(--primary,#4F46E5);opacity:.7;margin-bottom:.5rem}
.skel-sub{height:7px;background:#C4B5FD;margin-bottom:1.25rem}
.skel-section{height:8px;background:#A5B4FC;margin-top:.75rem;margin-bottom:.5rem}
.skel-line{height:6px;margin-bottom:.5rem;background:linear-gradient(90deg,#E5E7EB 25%,#F3F4F6 50%,#E5E7EB 75%);background-size:200% 100%;animation:shimmer 2s ease-in-out infinite}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}

/* Sparkle particles */
.sparkle{position:absolute;width:6px;height:6px;background:#fff;border-radius:50%;opacity:0;z-index:3;animation:sparkleAnim 3s ease-in-out infinite}
.sparkle:nth-child(4){top:15%;left:20%;animation-delay:0s}
.sparkle:nth-child(5){top:30%;right:15%;animation-delay:.8s}
.sparkle:nth-child(6){bottom:25%;left:25%;animation-delay:1.6s}
.sparkle:nth-child(7){bottom:15%;right:20%;animation-delay:2.2s}
.sparkle:nth-child(8){top:50%;left:10%;animation-delay:.4s}
@keyframes sparkleAnim{0%,100%{opacity:0;transform:scale(0)}50%{opacity:.8;transform:scale(1)}}

/* Phone input row */
.phone-row{display:flex;gap:.75rem;align-items:stretch}
.phone-prefix{display:flex;align-items:center;gap:.4rem;padding:0 1rem;border-radius:12px;border:1px solid #E5E7EB;background:#F9FAFB;font-size:.95rem;font-weight:500;white-space:nowrap;user-select:none}
.phone-row .input-field{flex:1}

/* Method tabs */
.method-tabs{display:flex;background:#F3F4F6;border-radius:12px;padding:4px;margin-bottom:1.5rem}
.method-tab{flex:1;text-align:center;padding:.6rem 1rem;border-radius:10px;font-size:.9rem;font-weight:500;color:var(--text-secondary,#6B7280);cursor:pointer;transition:all .2s;border:none;background:none}
.method-tab.active{background:#fff;color:var(--text-main,#111827);box-shadow:0 1px 3px rgba(0,0,0,.08)}

@media(max-width:768px){.resume-card{width:200px;height:260px;padding:1.25rem 1rem}.orb-1{width:180px;height:180px}.orb-2{width:150px;height:150px}.orb-3{width:100px;height:100px}}
`

export default function AuthPage() {
  const [searchParams] = useSearchParams()
  const [tab, setTab] = useState<'login' | 'register'>(searchParams.get('tab') === 'register' ? 'register' : 'login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
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
        await register(email, password, fullName || undefined)
      }
      navigate('/app/dashboard')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <style>{authStyles}</style>
      <div className="auth-split" style={{ display: 'flex', height: '100vh' }}>
        {/* Left visual panel with animations */}
        <div className="auth-visual" style={{ flex: 1, background: 'var(--primary-light, linear-gradient(135deg, #4F46E5, #7C3AED))', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', overflow: 'hidden' }}>
          {/* Animated orbs */}
          <div className="orb orb-1" />
          <div className="orb orb-2" />
          <div className="orb orb-3" />

          {/* Sparkle particles */}
          <div className="sparkle" />
          <div className="sparkle" />
          <div className="sparkle" />
          <div className="sparkle" />
          <div className="sparkle" />

          {/* Floating resume card */}
          <div className="resume-card">
            <div className="skel skel-header" style={{ width: '55%' }} />
            <div className="skel skel-sub" style={{ width: '40%' }} />

            <div className="skel skel-section" style={{ width: '35%' }} />
            <div className="skel skel-line" style={{ width: '100%' }} />
            <div className="skel skel-line" style={{ width: '85%', animationDelay: '0.15s' }} />
            <div className="skel skel-line" style={{ width: '92%', animationDelay: '0.3s' }} />

            <div className="skel skel-section" style={{ width: '40%' }} />
            <div className="skel skel-line" style={{ width: '100%', animationDelay: '0.45s' }} />
            <div className="skel skel-line" style={{ width: '78%', animationDelay: '0.6s' }} />
            <div className="skel skel-line" style={{ width: '90%', animationDelay: '0.75s' }} />
            <div className="skel skel-line" style={{ width: '65%', animationDelay: '0.9s' }} />

            <div className="skel skel-section" style={{ width: '30%' }} />
            <div className="skel skel-line" style={{ width: '95%', animationDelay: '1.05s' }} />
            <div className="skel skel-line" style={{ width: '70%', animationDelay: '1.2s' }} />
          </div>
        </div>

        {/* Right form side */}
        <div className="auth-form-side" style={{ flex: 1, background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
          <div style={{ width: '100%', maxWidth: 400 }}>
            <Link to="/" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '2rem', textDecoration: 'none' }}>
              <ArrowLeft size={16} /> На главную
            </Link>

            <h2 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '1.5rem' }}>
              {tab === 'login' ? 'Войти' : 'Поиск работы'}
            </h2>

            {/* Auth tabs */}
            <div className="tab-bar" style={{ marginBottom: '1.5rem' }}>
              <div className={`tab-bar-item${tab === 'register' ? ' active' : ''}`} onClick={() => setTab('register')}>
                Регистрация
              </div>
              <div className={`tab-bar-item${tab === 'login' ? ' active' : ''}`} onClick={() => setTab('login')}>
                Войти
              </div>
            </div>

            {error && (
              <div style={{ background: 'var(--danger-light, #FEF2F2)', color: 'var(--danger, #EF4444)', padding: '0.75rem 1rem', borderRadius: 8, marginBottom: '1rem', fontSize: '0.9rem' }}>
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {tab === 'register' && (
                  <div className="input-group">
                    <label className="input-label">Имя</label>
                    <input
                      type="text" className="input-field" placeholder="Александр Иванов"
                      value={fullName} onChange={e => setFullName(e.target.value)}
                    />
                  </div>
                )}
                <div className="input-group">
                  <label className="input-label">Email</label>
                  <input
                    type="email" className="input-field" placeholder="alex@example.com"
                    value={email} onChange={e => setEmail(e.target.value)} required
                  />
                </div>
                <div className="input-group">
                  <label className="input-label">Пароль</label>
                  <input
                    type="password" className="input-field"
                    placeholder={tab === 'login' ? '••••••••' : 'Минимум 8 символов'}
                    value={password} onChange={e => setPassword(e.target.value)} required minLength={8}
                  />
                  {tab === 'login' && (
                    <div style={{ textAlign: 'right', marginTop: '0.5rem' }}>
                      <Link to="/password-recovery" style={{ fontSize: '0.85rem', color: 'var(--primary)', fontWeight: 500 }}>
                        Забыли пароль?
                      </Link>
                    </div>
                  )}
                </div>
                <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
                  {loading ? 'Загрузка...' : tab === 'login' ? 'Войти' : 'Создать аккаунт'}
                </button>
              </div>
            </form>

            <p style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', textAlign: 'center', marginTop: '1.5rem', lineHeight: 1.5 }}>
              Продолжая, вы принимаете{' '}
              <Link to="/privacy" style={{ color: 'var(--primary)' }}>политику конфиденциальности</Link> и{' '}
              <Link to="/terms" style={{ color: 'var(--primary)' }}>правила сервиса</Link>
            </p>
          </div>
        </div>
      </div>
    </>
  )
}

import { Link } from 'react-router-dom'
import { Home, ArrowLeft } from 'lucide-react'

export default function ErrorPage() {
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      minHeight: '100vh', textAlign: 'center', padding: '2rem',
    }}>
      <div style={{
        fontSize: '8rem', fontWeight: 900, lineHeight: 1,
        background: 'var(--primary-gradient)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
        marginBottom: '1rem',
      }}>
        404
      </div>
      <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>Страница не найдена</h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem', maxWidth: 400 }}>
        Возможно, она была перемещена или удалена. Проверьте URL или вернитесь на главную.
      </p>
      <div style={{ display: 'flex', gap: '0.75rem' }}>
        <Link to="/" className="btn btn-primary"><Home size={16} /> На главную</Link>
        <button onClick={() => window.history.back()} className="btn btn-secondary"><ArrowLeft size={16} /> Назад</button>
      </div>
    </div>
  )
}

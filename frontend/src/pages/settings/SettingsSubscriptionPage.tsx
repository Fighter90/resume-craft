import { Check, CreditCard } from 'lucide-react'

const PLANS = [
  {
    id: 'free', name: 'Free', price: '0', period: '',
    features: ['5 оптимизаций/мес', '1 AI-модель (GigaChat)', 'Экспорт DOCX', 'Базовый скоринг'],
    current: false,
  },
  {
    id: 'standard', name: 'Standard', price: '490', period: '/мес',
    features: ['30 оптимизаций/мес', '2 AI-модели', 'Все форматы экспорта', 'ATS-рейтинг', 'Приоритетная поддержка'],
    current: true,
  },
  {
    id: 'pro', name: 'Pro', price: '1 490', period: '/мес',
    features: ['Безлимит оптимизаций', 'Все AI-модели', 'API-доступ', 'Интеграция с hh.ru', 'Выделенная поддержка', 'Ранний доступ'],
    current: false,
  },
]

export default function SettingsSubscriptionPage() {
  return (
    <div>
      {/* Current plan */}
      <div className="card" style={{ padding: '1.5rem', marginBottom: '2rem', background: 'var(--primary-bg)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <CreditCard size={20} style={{ color: 'var(--primary)' }} />
          <h3 style={{ fontWeight: 600 }}>Текущий план</h3>
          <span className="badge badge-indigo">Standard</span>
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
          Использовано <strong>12 из 30</strong> оптимизаций в этом месяце. Следующее списание: 15 февраля 2025.
        </p>
        <div className="progress-bar" style={{ height: 8 }}>
          <div className="progress-fill" style={{ width: '40%' }} />
        </div>
      </div>

      {/* Plans comparison */}
      <h3 style={{ fontWeight: 600, marginBottom: '1rem' }}>Все планы</h3>
      <div className="pricing-grid">
        {PLANS.map(plan => (
          <div key={plan.id} className={`card pricing-card${plan.current ? ' popular' : ''}`} style={{ padding: '1.5rem' }}>
            {plan.current && <div className="pricing-popular-badge">Текущий</div>}
            <h4 style={{ fontWeight: 600, marginBottom: '0.5rem' }}>{plan.name}</h4>
            <div style={{ fontSize: '2rem', fontWeight: 700 }}>
              {plan.price === '0' ? 'Бесплатно' : `${plan.price} ₽`}
              {plan.period && <span style={{ fontSize: '0.85rem', fontWeight: 400, color: 'var(--text-secondary)' }}>{plan.period}</span>}
            </div>
            <ul style={{ listStyle: 'none', padding: 0, margin: '1.25rem 0' }}>
              {plan.features.map(f => (
                <li key={f} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.35rem 0', fontSize: '0.85rem' }}>
                  <Check size={14} style={{ color: 'var(--success)', flexShrink: 0 }} /> {f}
                </li>
              ))}
            </ul>
            <button className={`btn btn-block ${plan.current ? 'btn-secondary' : 'btn-primary'}`} disabled={plan.current}>
              {plan.current ? 'Текущий план' : plan.id === 'free' ? 'Понизить' : 'Повысить'}
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}

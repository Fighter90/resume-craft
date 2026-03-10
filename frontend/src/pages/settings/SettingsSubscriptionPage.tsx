import { Check, CreditCard, Clock } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'

interface Plan {
  id: string
  name: string
  price: string
  period: string
  features: string[]
}

const PLANS: Plan[] = [
  {
    id: 'free', name: 'Free', price: '0', period: '',
    features: [
      '5 оптимизаций/мес',
      'Все AI-модели (BYOK)',
      'Экспорт DOCX, PDF и TXT',
      'История оптимизаций',
      'Базовый скоринг',
    ],
  },
  {
    id: 'standard', name: 'Standard', price: '490', period: '/мес',
    features: [
      '30 оптимизаций/мес',
      'Все AI-модели (BYOK)',
      'Экспорт DOCX, PDF и TXT',
      'ATS-рейтинг',
      'Приоритетная поддержка',
    ],
  },
  {
    id: 'pro', name: 'Pro', price: '1 490', period: '/мес',
    features: [
      'Безлимит оптимизаций',
      'Все AI-модели (BYOK) + API-доступ',
      'Интеграция с hh.ru',
      'Выделенная поддержка',
      'Ранний доступ',
    ],
  },
]

const PLAN_LIMITS: Record<string, number> = { free: 5, standard: 30, pro: 999 }

export default function SettingsSubscriptionPage() {
  const { user } = useAuth()
  const currentPlan = user?.plan || 'free'
  const optimizationsUsed = user?.optimizations_used ?? 0

  const currentPlanData = PLANS.find(p => p.id === currentPlan)!
  const limit = PLAN_LIMITS[currentPlan]
  const usagePercent = Math.round((optimizationsUsed / limit) * 100)

  const getButtonLabel = (planId: string) => {
    if (planId === currentPlan) return 'Текущий план'
    return 'Скоро'
  }

  return (
    <div>
      {/* Current plan */}
      <div className="card" style={{ padding: '1.5rem', marginBottom: '2rem', background: 'var(--primary-bg)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <CreditCard size={20} style={{ color: 'var(--primary)' }} />
          <h3 style={{ fontWeight: 600 }}>Текущий план</h3>
          <span className="badge badge-indigo">{currentPlanData.name}</span>
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
          Использовано <strong>{optimizationsUsed} из {limit === 999 ? '∞' : limit}</strong> оптимизаций в этом месяце.
        </p>
        <div className="progress-bar" style={{ height: 8 }}>
          <div className="progress-fill" style={{ width: `${Math.min(usagePercent, 100)}%` }} />
        </div>
      </div>

      {/* Payment coming soon info */}
      <div className="card" style={{ padding: '1rem 1.25rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem', border: '1px solid var(--border)', background: '#FEF3C7' }}>
        <div style={{ width: 36, height: 36, borderRadius: 8, background: '#FDE68A', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
          <Clock size={16} style={{ color: '#92400E' }} />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 600, fontSize: '0.9rem', color: '#92400E' }}>Платные тарифы скоро</div>
          <div style={{ fontSize: '0.8rem', color: '#78350F' }}>Оплата через Робокассу будет доступна в ближайшем обновлении. Сейчас доступен бесплатный план.</div>
        </div>
      </div>

      {/* Plans comparison */}
      <h3 style={{ fontWeight: 600, marginBottom: '1rem' }}>Все планы</h3>
      <div className="pricing-grid">
        {PLANS.map(plan => {
          const isCurrent = plan.id === currentPlan
          return (
            <div key={plan.id} className={`card pricing-card${isCurrent ? ' popular' : ''}`} style={{ padding: '1.5rem' }}>
              {isCurrent && <div className="pricing-popular-badge">Текущий</div>}
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
              <button
                className={`btn btn-block ${isCurrent ? 'btn-secondary' : 'btn-primary'}`}
                disabled={true}
                style={!isCurrent ? { opacity: 0.5, cursor: 'not-allowed' } : undefined}
              >
                {getButtonLabel(plan.id)}
              </button>
            </div>
          )
        })}
      </div>
    </div>
  )
}

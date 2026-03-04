import { useState } from 'react'
import { Check, CreditCard, ExternalLink } from 'lucide-react'
import { generatePaymentUrl, PLAN_PRICES, generateInvoiceId } from '../../utils/robokassa'
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
    features: ['5 оптимизаций/мес', '1 AI-модель (GigaChat)', 'Экспорт DOCX', 'Базовый скоринг'],
  },
  {
    id: 'standard', name: 'Standard', price: '490', period: '/мес',
    features: ['30 оптимизаций/мес', '2 AI-модели', 'Все форматы экспорта', 'ATS-рейтинг', 'Приоритетная поддержка'],
  },
  {
    id: 'pro', name: 'Pro', price: '1 490', period: '/мес',
    features: ['Безлимит оптимизаций', 'Все AI-модели', 'API-доступ', 'Интеграция с hh.ru', 'Выделенная поддержка', 'Ранний доступ'],
  },
]

const PLAN_LIMITS: Record<string, number> = { free: 5, standard: 30, pro: 999 }

export default function SettingsSubscriptionPage() {
  const { user } = useAuth()
  const [currentPlan, setCurrentPlan] = useState<string>(user?.plan || 'free')
  const optimizationsUsed = user?.optimizations_used ?? 0
  const [paymentLoading, setPaymentLoading] = useState<string | null>(null)
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null)

  const currentPlanData = PLANS.find(p => p.id === currentPlan)!
  const limit = PLAN_LIMITS[currentPlan]
  const usagePercent = Math.round((optimizationsUsed / limit) * 100)

  const handlePlanChange = async (planId: string) => {
    if (planId === currentPlan) return

    // Downgrade to free — instant
    if (planId === 'free') {
      setCurrentPlan('free')
      setMessage({ type: 'success', text: 'Тариф изменён на Free' })
      setTimeout(() => setMessage(null), 3000)
      return
    }

    // Upgrade to paid plan — Robokassa payment
    const price = PLAN_PRICES[planId]
    if (!price) return

    setPaymentLoading(planId)
    try {
      const paymentUrl = await generatePaymentUrl({
        amount: price,
        invoiceId: generateInvoiceId(),
        description: `ResumeCraft ${planId === 'standard' ? 'Standard' : 'Pro'} — подписка на 1 месяц`,
        planId,
      })

      // In demo mode — simulate successful payment
      if (import.meta.env.VITE_ROBOKASSA_TEST_MODE !== 'false') {
        window.open(paymentUrl, '_blank', 'width=800,height=600')
        setTimeout(() => {
          setCurrentPlan(planId)
          setMessage({ type: 'success', text: `Тариф ${planId === 'standard' ? 'Standard' : 'Pro'} активирован!` })
          setPaymentLoading(null)
          setTimeout(() => setMessage(null), 3000)
        }, 1000)
      } else {
        window.location.href = paymentUrl
      }
    } catch {
      setMessage({ type: 'error', text: 'Ошибка создания платежа. Попробуйте позже.' })
      setPaymentLoading(null)
      setTimeout(() => setMessage(null), 3000)
    }
  }

  const getButtonLabel = (planId: string) => {
    if (planId === currentPlan) return 'Текущий план'
    if (paymentLoading === planId) return 'Перенаправление...'
    if (PLANS.findIndex(p => p.id === planId) < PLANS.findIndex(p => p.id === currentPlan)) return 'Понизить'
    return planId === 'free' ? 'Понизить' : 'Повысить'
  }

  return (
    <div>
      {/* Status message */}
      {message && (
        <div style={{
          padding: '0.75rem 1rem', borderRadius: 8, marginBottom: '1rem', fontSize: '0.9rem',
          background: message.type === 'success' ? 'var(--success-light, #D1FAE5)' : message.type === 'error' ? 'var(--danger-light, #FEF2F2)' : '#EEF2FF',
          color: message.type === 'success' ? 'var(--success, #059669)' : message.type === 'error' ? 'var(--danger, #EF4444)' : 'var(--primary)',
        }}>
          {message.text}
        </div>
      )}

      {/* Current plan */}
      <div className="card" style={{ padding: '1.5rem', marginBottom: '2rem', background: 'var(--primary-bg)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <CreditCard size={20} style={{ color: 'var(--primary)' }} />
          <h3 style={{ fontWeight: 600 }}>Текущий план</h3>
          <span className="badge badge-indigo">{currentPlanData.name}</span>
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
          Использовано <strong>{optimizationsUsed} из {limit === 999 ? '∞' : limit}</strong> оптимизаций в этом месяце.
          {currentPlan !== 'free' && ' Оплата через Робокассу.'}
        </p>
        <div className="progress-bar" style={{ height: 8 }}>
          <div className="progress-fill" style={{ width: `${Math.min(usagePercent, 100)}%` }} />
        </div>
      </div>

      {/* Robokassa info */}
      <div className="card" style={{ padding: '1rem 1.25rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem', border: '1px solid var(--border)' }}>
        <div style={{ width: 36, height: 36, borderRadius: 8, background: '#F3F4F6', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
          <ExternalLink size={16} style={{ color: 'var(--text-secondary)' }} />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>Оплата через Робокассу</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Банковские карты, СБП, ЮMoney, QIWI и другие способы оплаты</div>
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
                disabled={isCurrent || paymentLoading === plan.id}
                onClick={() => handlePlanChange(plan.id)}
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

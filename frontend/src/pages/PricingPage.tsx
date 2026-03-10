import { Link } from 'react-router-dom'
import { Check } from 'lucide-react'

export default function PricingPage() {
  const plans = [
    {
      name: 'Free',
      badge: 'gray',
      price: '0 ₽',
      period: 'навсегда',
      desc: 'Для знакомства с сервисом',
      features: [
        '5 оптимизаций/мес',
        'Все AI-модели (BYOK)',
        'Экспорт DOCX, PDF и TXT',
        '1 шаблон (Minimal)',
        'Поиск hh.ru',
        'Email поддержка',
      ],
      featured: false,
    },
    {
      name: 'Standard',
      badge: 'indigo',
      price: '490 ₽',
      period: '/мес',
      desc: 'Для активного поиска работы',
      features: [
        '30 оптимизаций/мес',
        'Все AI-модели (BYOK)',
        'Экспорт DOCX, PDF и TXT',
        '3 шаблона',
        'Поиск hh.ru',
        'Email + чат',
      ],
      year: '3 990 ₽/год (−32%)',
      featured: true,
    },
    {
      name: 'Pro',
      badge: 'green',
      price: '1 490 ₽',
      period: '/мес',
      desc: 'Для профессионалов и рекрутеров',
      features: [
        'Безлимит оптимизаций',
        'Все AI-модели (BYOK) + API-доступ',
        'Экспорт DOCX, PDF и TXT + hh.ru',
        'Все шаблоны + кастомные',
        'API доступ',
        'Приоритет 24/7',
      ],
      year: '11 990 ₽/год (−33%)',
      featured: false,
    },
  ]

  return (
    <>
      <section style={{ textAlign: 'center', padding: '3rem 1rem' }}>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 700, marginBottom: '0.75rem' }}>Выберите подходящий план</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.05rem', marginBottom: '0.5rem' }}>
          Начните бесплатно, обновите когда будете готовы
        </p>
        <p style={{ color: 'var(--text-tertiary)', fontSize: '0.9rem', marginBottom: '2.5rem' }}>
          Годовая подписка экономит до 33%. Оплата картой или через Робокассу.
        </p>
        <div className="pricing-grid">
          {plans.map(p => (
            <div key={p.name} className={`card pricing-card${p.featured ? ' featured' : ''}`} style={{ padding: '2rem', display: 'flex', flexDirection: 'column' }}>
              {p.featured && <div className="pricing-popular"><span className="badge badge-indigo">Популярный</span></div>}
              <span className={`badge badge-${p.badge}`} style={{ alignSelf: 'flex-start', marginBottom: '0.5rem' }}>{p.name}</span>
              <div className="price">{p.price}<span>{p.period}</span></div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>{p.desc}</p>
              <ul style={{ listStyle: 'none', padding: 0, flex: 1 }}>
                {p.features.map(f => (
                  <li key={f} style={{ padding: '0.5rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                    <Check size={16} style={{ color: 'var(--success)', flexShrink: 0 }} /> {f}
                  </li>
                ))}
              </ul>
              {p.year && <p style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', margin: '0.75rem 0' }}>{p.year}</p>}
              <Link to="/auth?tab=register" className={`btn ${p.featured ? 'btn-primary' : 'btn-secondary'} btn-block`}>
                {p.name === 'Free' ? 'Текущий план' : 'Выбрать план'}
              </Link>
            </div>
          ))}
        </div>
      </section>
    </>
  )
}

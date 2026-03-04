import { Link } from 'react-router-dom'
import { Upload, Search, BarChart3, Shield, FileText, Cpu, Check, ChevronDown, Star, Zap } from 'lucide-react'
import { useState } from 'react'

const FAQ_DATA = [
  { q: 'Как работает AI-оптимизация?', a: 'Наша система анализирует ваше резюме и целевую вакансию, выявляет пробелы и с помощью AI переписывает текст, добавляя релевантные ключевые слова и метрики достижений.' },
  { q: 'Безопасно ли загружать резюме?', a: 'Да. Все данные хранятся на серверах в России (ФЗ-152), передаются по зашифрованному каналу. Вы можете удалить все данные в любой момент.' },
  { q: 'Какие форматы поддерживаются?', a: 'PDF и DOCX для загрузки. Экспорт доступен в DOCX (все планы) и PDF (Standard+).' },
  { q: 'Можно ли использовать бесплатно?', a: 'Да! Бесплатный план включает 5 оптимизаций в месяц с моделью Llama 3.' },
  { q: 'Чем отличается от конкурентов?', a: 'ResumeCraft — единственный сервис с интеграцией hh.ru API, мультимодельным AI и специализацией на российском рынке.' },
  { q: 'Как считается Match Score?', a: 'Match Score — взвешенная оценка: ключевые слова (40%) + релевантность опыта (25%) + структура (20%) + читаемость (15%).' },
]

export default function LandingPage() {
  const [openFaq, setOpenFaq] = useState<number | null>(null)

  return (
    <>
      {/* Hero */}
      <section style={{ textAlign: 'center', padding: '4rem 1rem 3rem' }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          <h1 className="hero-title" style={{ fontSize: '3rem', fontWeight: 800, lineHeight: 1.1, marginBottom: '1.5rem' }}>
            AI-оптимизация резюме<br />
            <span className="hero-gradient">для российского рынка</span>
          </h1>
          <p style={{ fontSize: '1.2rem', color: 'var(--text-secondary)', maxWidth: 600, margin: '0 auto 2rem' }}>
            Загрузите резюме, выберите вакансию на hh.ru — получите идеально адаптированную версию за 30 секунд
          </p>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link to="/auth?tab=register" className="btn btn-primary btn-lg">Начать бесплатно</Link>
            <a href="#how-it-works" className="btn btn-secondary btn-lg">Как это работает</a>
          </div>
          <div className="hero-stats" style={{ marginTop: '3rem' }}>
            {[
              { value: '93 млн', label: 'резюме на hh.ru' },
              { value: '4.9/5', label: 'средняя оценка' },
              { value: '30 сек', label: 'время оптимизации' },
            ].map(s => (
              <div key={s.label} style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--primary)' }}>{s.value}</div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Problem */}
      <section className="landing-section-alt">
        <div className="landing-section-inner">
          <h2 style={{ fontSize: '2rem', fontWeight: 700, textAlign: 'center', marginBottom: '2.5rem' }}>Проблема</h2>
          <div className="problem-stats-grid" style={{ maxWidth: 600, margin: '0 auto' }}>
            <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
              <div style={{ fontSize: '3rem', fontWeight: 700, color: 'var(--danger)', lineHeight: 1 }}>75%</div>
              <div style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>резюме отсеиваются ATS-фильтрами автоматически</div>
            </div>
            <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
              <div style={{ fontSize: '3rem', fontWeight: 700, color: 'var(--warning)', lineHeight: 1 }}>5.9</div>
              <div style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>конкурентов на одну вакансию (индекс hh.ru)</div>
            </div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="landing-section" id="how-it-works">
        <div className="landing-section-inner">
          <h2 style={{ fontSize: '2rem', fontWeight: 700, textAlign: 'center', marginBottom: '0.5rem' }}>Как это работает</h2>
          <p className="section-subtitle" style={{ color: 'var(--text-secondary)', textAlign: 'center', marginBottom: '2.5rem' }}>
            Три простых шага до идеального резюме
          </p>
          <div className="steps-grid">
            {[
              { num: 1, icon: Upload, title: 'Загрузите резюме', desc: 'PDF или DOCX — система извлечёт текст автоматически' },
              { num: 2, icon: Search, title: 'Выберите вакансию', desc: 'Найдите на hh.ru, вставьте ссылку или введите вручную' },
              { num: 3, icon: Zap, title: 'Получите результат', desc: 'AI оптимизирует резюме за 30 секунд с Match Score' },
            ].map(s => (
              <div key={s.num} className="card" style={{ textAlign: 'center', padding: '2rem' }}>
                <div className="step-number">{s.num}</div>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 600, marginBottom: '0.5rem' }}>{s.title}</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="landing-section-alt">
        <div className="landing-section-inner">
          <h2 style={{ fontSize: '2rem', fontWeight: 700, textAlign: 'center', marginBottom: '0.5rem' }}>Возможности</h2>
          <p style={{ color: 'var(--text-secondary)', textAlign: 'center', marginBottom: '2.5rem' }}>
            Всё необходимое для идеального резюме
          </p>
          <div className="features-grid">
            {[
              { icon: Cpu, title: 'AI-реврайтинг', desc: 'Глубокая переработка текста с учётом вакансии и ATS-требований' },
              { icon: Search, title: 'Интеграция hh.ru', desc: 'Поиск вакансий, импорт по URL, автоанализ требований' },
              { icon: BarChart3, title: 'Match Score', desc: 'Оценка соответствия 0–100% по 4 компонентам' },
              { icon: Shield, title: 'ATS-оптимизация', desc: 'Рейтинг A+ – D, ключевые слова, структура' },
              { icon: FileText, title: 'Мультиформат', desc: 'Экспорт в DOCX и PDF с профессиональными шаблонами' },
              { icon: Star, title: 'Выбор AI-модели', desc: 'GigaChat Pro, GPT-4o, Llama 3 — под вашу задачу' },
            ].map(f => (
              <div key={f.title} className="card" style={{ padding: '1.5rem' }}>
                <div style={{
                  width: 48, height: 48, borderRadius: 12,
                  background: 'var(--primary-light)', display: 'flex',
                  alignItems: 'center', justifyContent: 'center', color: 'var(--primary)',
                  marginBottom: '1rem'
                }}>
                  <f.icon size={24} />
                </div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 600, marginBottom: '0.5rem' }}>{f.title}</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.5 }}>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="landing-section" id="pricing">
        <div className="landing-section-inner">
          <h2 style={{ fontSize: '2rem', fontWeight: 700, textAlign: 'center', marginBottom: '0.5rem' }}>Тарифные планы</h2>
          <p style={{ color: 'var(--text-secondary)', textAlign: 'center', marginBottom: '2.5rem' }}>
            Начните бесплатно, обновите когда будете готовы
          </p>
          <div className="pricing-grid">
            {[
              { name: 'Free', price: '0 ₽', period: 'навсегда', desc: 'Для знакомства', features: ['5 оптимизаций/мес', 'Llama 3', 'DOCX экспорт', '1 шаблон', 'Поиск hh.ru'], featured: false },
              { name: 'Standard', price: '490 ₽', period: '/мес', desc: 'Для активного поиска', features: ['30 оптимизаций/мес', 'GigaChat Pro + Llama 3', 'PDF + DOCX', '3 шаблона', 'Email + чат'], year: '3 990 ₽/год (−32%)', featured: true },
              { name: 'Pro', price: '1 490 ₽', period: '/мес', desc: 'Для профессионалов', features: ['Безлимит оптимизаций', 'Все модели + GPT-4o', 'Все форматы + hh.ru', 'Все шаблоны', 'Приоритет 24/7'], year: '11 990 ₽/год (−33%)', featured: false },
            ].map(p => (
              <div key={p.name} className={`card pricing-card${p.featured ? ' featured' : ''}`} style={{ padding: '2rem', display: 'flex', flexDirection: 'column' }}>
                {p.featured && <div className="pricing-popular"><span className="badge badge-indigo">Популярный</span></div>}
                <div className="badge badge-gray" style={{ alignSelf: 'flex-start', marginBottom: '0.5rem' }}>{p.name}</div>
                <div className="price">{p.price}<span>{p.period}</span></div>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1rem' }}>{p.desc}</p>
                <ul style={{ listStyle: 'none', padding: 0, flex: 1 }}>
                  {p.features.map(f => (
                    <li key={f} style={{ padding: '0.5rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                      <Check size={16} style={{ color: 'var(--success)', flexShrink: 0 }} /> {f}
                    </li>
                  ))}
                </ul>
                {p.year && <p style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', margin: '0.5rem 0' }}>{p.year}</p>}
                <Link to="/auth?tab=register" className={`btn ${p.featured ? 'btn-primary' : 'btn-secondary'} btn-block`} style={{ marginTop: '1rem' }}>
                  {p.name === 'Free' ? 'Начать бесплатно' : 'Выбрать план'}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="landing-section-alt" id="faq">
        <div className="landing-section-inner" style={{ maxWidth: 700, margin: '0 auto' }}>
          <h2 style={{ fontSize: '2rem', fontWeight: 700, textAlign: 'center', marginBottom: '2rem' }}>Частые вопросы</h2>
          {FAQ_DATA.map((item, i) => (
            <div key={i} className={`faq-item${openFaq === i ? ' open' : ''}`} onClick={() => setOpenFaq(openFaq === i ? null : i)}>
              <div className="faq-question">
                {item.q}
                <ChevronDown size={20} style={{ transform: openFaq === i ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} />
              </div>
              {openFaq === i && <div className="faq-answer" style={{ display: 'block' }}>{item.a}</div>}
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="landing-cta">
        <h2>Готовы улучшить резюме?</h2>
        <p>Присоединяйтесь к тысячам соискателей, которые уже нашли работу мечты</p>
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
          <Link to="/auth?tab=register" className="btn btn-lg" style={{ background: 'white', color: 'var(--primary)' }}>Начать бесплатно</Link>
          <Link to="/pricing" className="btn btn-lg" style={{ background: 'rgba(255,255,255,0.2)', color: 'white', border: '1px solid rgba(255,255,255,0.3)' }}>Тарифы</Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="landing-footer-grid">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <div style={{ width: 24, height: 24, background: 'var(--primary-gradient)', borderRadius: 6, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white' }}>
                <FileText size={12} />
              </div>
              <span style={{ fontWeight: 700 }}>ResumeCraft</span>
            </div>
            <p style={{ color: '#9CA3AF', fontSize: '0.85rem', lineHeight: 1.6 }}>
              AI-оптимизация резюме для российского рынка труда. Интеграция с hh.ru.
            </p>
          </div>
          <div>
            <h4>Продукт</h4>
            <a href="#how-it-works">Как работает</a>
            <Link to="/pricing">Тарифы</Link>
            <a href="#faq">FAQ</a>
          </div>
          <div>
            <h4>Компания</h4>
            <a href="#">О нас</a>
            <a href="#">Блог</a>
            <a href="#">Контакты</a>
          </div>
          <div>
            <h4>Поддержка</h4>
            <a href="mailto:support@resumecraft.ru">Email</a>
            <a href="#">Telegram</a>
            <a href="#">Документация</a>
          </div>
        </div>
      </footer>
    </>
  )
}

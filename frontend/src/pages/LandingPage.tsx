import { Link } from 'react-router-dom'
import { Upload, Search, BarChart3, Shield, FileText, Cpu, Check, ChevronDown, Star, Zap, Users, User, ArrowRight, Globe, Clock } from 'lucide-react'
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
          <h2 style={{ fontSize: '2rem', fontWeight: 700, textAlign: 'center', marginBottom: '0.5rem' }}>Почему ваши отклики остаются без ответа?</h2>
          <p className="section-subtitle" style={{ color: 'var(--text-secondary)', textAlign: 'center', marginBottom: '2.5rem' }}>
            Конкуренция на рынке труда растёт с каждым годом. Без оптимизации резюме вы систематически теряете возможности.
          </p>
          <div className="problem-stats-grid" style={{ maxWidth: 600, margin: '0 auto', marginBottom: '2rem' }}>
            <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
              <div style={{ fontSize: '3rem', fontWeight: 700, color: 'var(--danger)', lineHeight: 1 }}>75%</div>
              <div style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>резюме отсеиваются ATS-фильтрами<br/>ещё до того, как их увидит рекрутер</div>
            </div>
            <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
              <div style={{ fontSize: '3rem', fontWeight: 700, color: 'var(--warning)', lineHeight: 1 }}>5.9</div>
              <div style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>конкурентов в среднем<br/>на каждую вакансию на hh.ru</div>
            </div>
          </div>
          <div className="card" style={{ maxWidth: 800, margin: '0 auto', padding: '2rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem', textAlign: 'center' }}>Что происходит с вашим резюме на самом деле</h3>
            <p style={{ color: 'var(--text-secondary)', lineHeight: 1.7, marginBottom: '1rem' }}>
              Большинство крупных компаний в России — Яндекс, Сбер, Тинькофф, VK, Ozon — используют автоматизированные системы отбора кандидатов (ATS). Это такие платформы, как Huntflow, Поток, Талантикс и Skillaz. Когда вы отправляете резюме, оно сначала проходит через алгоритм, который ищет совпадения с описанием вакансии.
            </p>
            <p style={{ color: 'var(--text-secondary)', lineHeight: 1.7, marginBottom: '1rem' }}>
              Если алгоритм не находит достаточно совпадений, ваше резюме попросту не доходит до живого рекрутера. Вы можете быть идеальным кандидатом, но если в вашем резюме написано «управлял проектами» вместо «руководил портфелем из 5 проектов с бюджетом 12 млн рублей», ATS оценит вас ниже конкурента.
            </p>
            <p style={{ color: 'var(--text-secondary)', lineHeight: 1.7 }}>
              ResumeCraft решает именно эту проблему. Наш AI анализирует требования конкретной вакансии, сопоставляет их с вашим опытом и переписывает формулировки так, чтобы они максимально совпадали с тем, что ищет работодатель — при этом сохраняя полную достоверность информации.
            </p>
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

      {/* Before/After — matches prototype */}
      <section className="landing-section">
        <div className="landing-section-inner">
          <h2 style={{ fontSize: '2rem', fontWeight: 700, textAlign: 'center', marginBottom: '0.5rem' }}>До и после оптимизации</h2>
          <p style={{ color: 'var(--text-secondary)', textAlign: 'center', marginBottom: '2.5rem' }}>
            Посмотрите, как AI трансформирует резюме
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', maxWidth: 800, margin: '0 auto' }}>
            <div className="card" style={{ padding: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                <span className="badge badge-gray">До</span>
                <span style={{ fontSize: '0.8rem', color: 'var(--danger)' }}>53% Match Score</span>
              </div>
              <div style={{ fontSize: '0.85rem', lineHeight: 1.7, color: 'var(--text-secondary)' }}>
                <p><mark style={{ background: 'rgba(239,68,68,0.12)', color: 'inherit', borderRadius: 3, padding: '1px 3px' }}>Менеджер по продукту</mark></p>
                <p>Опыт работы в IT. Занимался запуском продуктов и управлением командой.</p>
                <p><mark style={{ background: 'rgba(239,68,68,0.12)', color: 'inherit', borderRadius: 3, padding: '1px 3px' }}>Работал с аналитикой</mark> и проводил исследования.</p>
              </div>
            </div>
            <div className="card" style={{ padding: '1.5rem', borderColor: 'var(--success)', borderWidth: 2 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                <span className="badge badge-green">После</span>
                <span style={{ fontSize: '0.8rem', color: 'var(--success)' }}>87% Match Score</span>
              </div>
              <div style={{ fontSize: '0.85rem', lineHeight: 1.7, color: 'var(--text-secondary)' }}>
                <p><mark style={{ background: 'rgba(16,185,129,0.12)', color: 'inherit', borderRadius: 3, padding: '1px 3px' }}>Senior Product Manager</mark> с 6+ лет опыта (DAU 500K+)</p>
                <p>Руководил запуском 3 продуктовых линеек, каждая — <mark style={{ background: 'rgba(16,185,129,0.12)', color: 'inherit', borderRadius: 3, padding: '1px 3px' }}>100K+ MAU за 6 месяцев</mark>.</p>
                <p>Повысил конверсию на <mark style={{ background: 'rgba(16,185,129,0.12)', color: 'inherit', borderRadius: 3, padding: '1px 3px' }}>34% через 120+ A/B тестов</mark>.</p>
              </div>
            </div>
          </div>
          <div style={{ maxWidth: 800, margin: '1.5rem auto 0', fontSize: '0.85rem' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  <th style={{ padding: '0.5rem', textAlign: 'left', color: 'var(--text-secondary)' }}>Параметр</th>
                  <th style={{ padding: '0.5rem', textAlign: 'center', color: 'var(--danger)' }}>До</th>
                  <th style={{ padding: '0.5rem', textAlign: 'center', color: 'var(--success)' }}>После</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { param: 'Ключевые слова', before: '23%', after: '91%' },
                  { param: 'Метрики в достижениях', before: '1 из 5', after: '5 из 5' },
                  { param: 'ATS-совместимость', before: 'D', after: 'A+' },
                  { param: 'Релевантность опыта', before: '45%', after: '82%' },
                  { param: 'Структура', before: '60%', after: '95%' },
                ].map(row => (
                  <tr key={row.param} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '0.5rem' }}>{row.param}</td>
                    <td style={{ padding: '0.5rem', textAlign: 'center', color: 'var(--danger)' }}>{row.before}</td>
                    <td style={{ padding: '0.5rem', textAlign: 'center', color: 'var(--success)', fontWeight: 600 }}>{row.after}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Target Audience — matches prototype */}
      <section className="landing-section-alt">
        <div className="landing-section-inner">
          <h2 style={{ fontSize: '2rem', fontWeight: 700, textAlign: 'center', marginBottom: '0.5rem' }}>Для кого ResumeCraft</h2>
          <p style={{ color: 'var(--text-secondary)', textAlign: 'center', marginBottom: '2.5rem' }}>
            Помогаем специалистам разного уровня
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
            {[
              { icon: User, title: 'Студенты и выпускники', desc: 'Первое резюме без опыта — AI подчеркнёт потенциал, навыки и проекты' },
              { icon: Users, title: 'Опытные специалисты', desc: 'Обновление резюме под конкретную вакансию с оптимальными формулировками' },
              { icon: ArrowRight, title: 'Карьерные переходы', desc: 'Переупаковка опыта из одной отрасли для позиций в другой' },
              { icon: Cpu, title: 'IT-специалисты', desc: 'Технический стек, проекты, метрики — всё в формате, который оценят рекрутеры' },
            ].map(item => (
              <div key={item.title} className="card" style={{ padding: '1.5rem' }}>
                <div style={{
                  width: 48, height: 48, borderRadius: 12,
                  background: 'var(--primary-light)', display: 'flex',
                  alignItems: 'center', justifyContent: 'center', color: 'var(--primary)',
                  marginBottom: '1rem',
                }}>
                  <item.icon size={24} />
                </div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 600, marginBottom: '0.5rem' }}>{item.title}</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.5 }}>{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Why ResumeCraft — matches prototype USP cards */}
      <section className="landing-section">
        <div className="landing-section-inner">
          <h2 style={{ fontSize: '2rem', fontWeight: 700, textAlign: 'center', marginBottom: '0.5rem' }}>Почему именно ResumeCraft</h2>
          <p style={{ color: 'var(--text-secondary)', textAlign: 'center', marginBottom: '2.5rem' }}>
            Уникальные преимущества нашего сервиса
          </p>
          <div className="features-grid">
            {[
              { icon: Globe, title: 'Русскоязычный AI', desc: 'GigaChat Pro — #1 MERA бенчмарк для русского языка. Лучшее понимание рынка труда РФ' },
              { icon: Shield, title: 'Без VPN', desc: 'Все модели доступны из России напрямую, данные не покидают территорию РФ' },
              { icon: FileText, title: 'Данные в России', desc: 'Соответствие ФЗ-152 о персональных данных. Серверы в Yandex Cloud' },
              { icon: Clock, title: 'Скорость 30 сек', desc: 'Полный цикл оптимизации: анализ + переписывание + скоринг за полминуты' },
              { icon: Check, title: 'Достоверность', desc: 'AI не выдумывает факты — только переформулирует ваш реальный опыт с метриками' },
              { icon: Search, title: 'Интеграция hh.ru', desc: 'Единственный сервис с прямым API hh.ru — автоматический импорт вакансий' },
            ].map(f => (
              <div key={f.title} className="card" style={{ padding: '1.5rem' }}>
                <div style={{
                  width: 48, height: 48, borderRadius: 12,
                  background: 'var(--primary-light)', display: 'flex',
                  alignItems: 'center', justifyContent: 'center', color: 'var(--primary)',
                  marginBottom: '1rem',
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

      {/* Social proof / Stats — matches prototype */}
      <section className="landing-section-alt">
        <div className="landing-section-inner">
          <h2 style={{ fontSize: '2rem', fontWeight: 700, textAlign: 'center', marginBottom: '2rem' }}>Цифры говорят сами</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1.5rem', maxWidth: 700, margin: '0 auto 2rem' }}>
            {[
              { value: '93 млн', label: 'резюме на hh.ru' },
              { value: '4.9/5', label: 'средняя оценка' },
              { value: '+34%', label: 'рост Match Score' },
              { value: '30 сек', label: 'время оптимизации' },
            ].map(s => (
              <div key={s.label} className="card" style={{ textAlign: 'center', padding: '1.25rem' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--primary)' }}>{s.value}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>{s.label}</div>
              </div>
            ))}
          </div>
          <div style={{ textAlign: 'center' }}>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
              Совместимо с ATS-системами:
            </p>
            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center', flexWrap: 'wrap' }}>
              {['Huntflow', 'Поток', 'Талантикс', 'Skillaz', 'hh.ru'].map(name => (
                <span key={name} className="badge badge-gray">{name}</span>
              ))}
            </div>
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
            <Link to="/about">О нас</Link>
            <Link to="/privacy">Конфиденциальность</Link>
            <Link to="/terms">Правила сервиса</Link>
          </div>
          <div>
            <h4>Поддержка</h4>
            <a href="mailto:support@resumecraft.ru">Email</a>
            <a href="https://t.me/resumecraft_support" target="_blank" rel="noopener noreferrer">Telegram</a>
            <Link to="/about">Контакты</Link>
          </div>
        </div>
      </footer>
    </>
  )
}

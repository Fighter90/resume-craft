import { Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, Search } from 'lucide-react'
import { useState } from 'react'
import { DEMO_VACANCIES } from '../../data/demo'

export default function VacancyPage() {
  const navigate = useNavigate()
  const [tab, setTab] = useState(0)
  const [selected, setSelected] = useState<string | null>(null)

  return (
    <div className="wizard-container">
      <Link to="/app/upload" className="btn btn-secondary btn-sm" style={{ marginBottom: '1.5rem' }}>
        <ArrowLeft size={16} /> Назад
      </Link>

      <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>Выберите целевую вакансию</h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>Укажите вакансию для адаптации резюме</p>

      {/* Tabs */}
      <div className="tab-bar">
        {['Поиск hh.ru', 'Вставить URL', 'Ввести вручную'].map((label, i) => (
          <div key={i} className={`tab-bar-item${tab === i ? ' active' : ''}`} onClick={() => setTab(i)}>
            {label}
          </div>
        ))}
      </div>

      {/* Tab 0: Search */}
      {tab === 0 && (
        <>
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="input-group" style={{ gridColumn: '1 / -1' }}>
                <label className="input-label">Должность</label>
                <input className="input-field" placeholder="Product Manager" />
              </div>
              <div className="input-group">
                <label className="input-label">Город</label>
                <select className="input-field select-field">
                  <option>Москва</option><option>Санкт-Петербург</option><option>Удалённо</option>
                </select>
              </div>
              <div className="input-group">
                <label className="input-label">Зарплата от</label>
                <select className="input-field select-field">
                  <option>Любая</option><option>от 150 000 ₽</option><option>от 200 000 ₽</option><option>от 300 000 ₽</option>
                </select>
              </div>
              <div className="input-group">
                <label className="input-label">Занятость</label>
                <select className="input-field select-field">
                  <option>Любая</option><option>Полная</option><option>Частичная</option><option>Удалённая</option>
                </select>
              </div>
            </div>
            <button className="btn btn-primary" style={{ marginTop: '1rem', height: 48 }}>
              <Search size={16} /> Найти
            </button>
          </div>

          <div className="vacancy-results" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            {DEMO_VACANCIES.map(v => (
              <div
                key={v.id}
                className={`card vacancy-card${selected === v.id ? ' selected' : ''}`}
                onClick={() => setSelected(v.id)}
                style={{ padding: '1.25rem', cursor: 'pointer' }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.25rem' }}>{v.title}</h3>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{v.company} · {v.city}</p>
                  </div>
                  <span className={`badge ${v.matchScore >= 80 ? 'badge-green' : v.matchScore >= 60 ? 'badge-yellow' : 'badge-gray'}`}>
                    {v.matchScore}%
                  </span>
                </div>
                <div style={{ fontWeight: 600, color: 'var(--success)', margin: '0.5rem 0', fontSize: '0.95rem' }}>{v.salary}</div>
                <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
                  {v.tags.map(t => <span key={t} className="badge badge-indigo">{t}</span>)}
                </div>
              </div>
            ))}
          </div>

          {selected && (
            <button onClick={() => navigate('/app/models')} className="btn btn-primary btn-block" style={{ marginTop: '1.5rem' }}>
              Продолжить с выбранной вакансией
            </button>
          )}
        </>
      )}

      {/* Tab 1: URL */}
      {tab === 1 && (
        <div className="card" style={{ padding: '1.5rem' }}>
          <div className="input-group" style={{ marginBottom: '1rem' }}>
            <label className="input-label">Ссылка на вакансию hh.ru</label>
            <input className="input-field" placeholder="https://hh.ru/vacancy/12345678" />
          </div>
          <button onClick={() => navigate('/app/models')} className="btn btn-primary">Загрузить вакансию</button>
        </div>
      )}

      {/* Tab 2: Manual */}
      {tab === 2 && (
        <div className="card" style={{ padding: '1.5rem' }}>
          <div className="input-group" style={{ marginBottom: '1rem' }}>
            <label className="input-label">Название должности</label>
            <input className="input-field" placeholder="Product Manager" />
          </div>
          <div className="input-group" style={{ marginBottom: '1rem' }}>
            <label className="input-label">Компания</label>
            <input className="input-field" placeholder="Яндекс" />
          </div>
          <div className="input-group" style={{ marginBottom: '1rem' }}>
            <label className="input-label">Описание и требования</label>
            <textarea className="input-field" rows={4} placeholder="Опишите обязанности, требования..." />
          </div>
          <div className="input-group" style={{ marginBottom: '1rem' }}>
            <label className="input-label">Ключевые навыки (через запятую)</label>
            <input className="input-field" placeholder="SQL, Agile, Product Strategy" />
          </div>
          <button onClick={() => navigate('/app/models')} className="btn btn-primary">Продолжить</button>
        </div>
      )}
    </div>
  )
}

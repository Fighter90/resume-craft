import { Link } from 'react-router-dom'
import { Search, Plus, FileText, Download, Trash2, Eye } from 'lucide-react'
import { DEMO_RESUMES } from '../../data/demo'

const statusLabel = (s: string) => {
  switch (s) {
    case 'optimized': return { text: 'Оптимизировано', cls: 'badge-green' }
    case 'draft': return { text: 'Черновик', cls: 'badge-gray' }
    case 'processing': return { text: 'В обработке', cls: 'badge-yellow' }
    default: return { text: s, cls: 'badge-gray' }
  }
}

export default function ResumesPage() {
  return (
    <>
      <div className="page-header">
        <div>
          <h1>Мои резюме</h1>
          <p>Управляйте загруженными резюме</p>
        </div>
        <Link to="/app/upload" className="btn btn-primary"><Plus size={16} /> Загрузить резюме</Link>
      </div>

      {/* Filters */}
      <div className="filter-bar">
        <div className="input-group" style={{ flex: 1, maxWidth: 300 }}>
          <div style={{ position: 'relative' }}>
            <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-tertiary)' }} />
            <input className="input-field" placeholder="Поиск резюме..." style={{ paddingLeft: '2.5rem' }} />
          </div>
        </div>
        <select className="input-field select-field" style={{ maxWidth: 200 }}>
          <option>Все статусы</option>
          <option>Оптимизировано</option>
          <option>Черновик</option>
          <option>В обработке</option>
        </select>
        <select className="input-field select-field" style={{ maxWidth: 200 }}>
          <option>По дате (новые)</option>
          <option>По Match Score</option>
          <option>По названию</option>
        </select>
      </div>

      {/* Desktop Table */}
      <div className="card resumes-desktop-table" style={{ overflow: 'auto' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Название</th>
              <th>Вакансия</th>
              <th>Статус</th>
              <th>Match Score</th>
              <th>AI модель</th>
              <th>Дата</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            {DEMO_RESUMES.map(r => {
              const st = statusLabel(r.status)
              return (
                <tr key={r.id}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <div style={{ width: 36, height: 36, borderRadius: 8, background: '#F3F4F6', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
                        <FileText size={16} />
                      </div>
                      <div>
                        <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{r.title}</div>
                        <div style={{ fontSize: '0.78rem', color: 'var(--text-tertiary)' }}>.{r.file_format}</div>
                      </div>
                    </div>
                  </td>
                  <td style={{ color: r.vacancy ? 'var(--text-main)' : 'var(--text-tertiary)' }}>
                    {r.vacancy || '—'}
                  </td>
                  <td><span className={`badge ${st.cls}`}>{st.text}</span></td>
                  <td>
                    {r.match_score ? (
                      <span style={{ fontWeight: 600, color: r.match_score >= 80 ? 'var(--success)' : r.match_score >= 60 ? '#D97706' : 'var(--text-secondary)' }}>
                        {r.match_score}%
                      </span>
                    ) : '—'}
                  </td>
                  <td>{r.model || '—'}</td>
                  <td style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{r.date}</td>
                  <td>
                    <div className="td-actions">
                      <Link to={`/app/results/${r.id}`} className="btn btn-ghost btn-icon" title="Открыть"><Eye size={16} /></Link>
                      <button className="btn btn-ghost btn-icon" title="Скачать" onClick={() => alert('Загрузка началась...')}><Download size={16} /></button>
                      <button className="btn btn-ghost btn-icon" title="Удалить" style={{ color: 'var(--danger)' }} onClick={() => alert(`Резюме "${r.title}" удалено`)}><Trash2 size={16} /></button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Mobile Cards */}
      <div className="resumes-mobile-cards">
        {DEMO_RESUMES.map(r => {
          const st = statusLabel(r.status)
          return (
            <div key={r.id} className="card" style={{ padding: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <div style={{ width: 36, height: 36, borderRadius: 8, background: '#F3F4F6', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
                    <FileText size={16} />
                  </div>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{r.title}</div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-tertiary)' }}>{r.vacancy || 'Без вакансии'}</div>
                  </div>
                </div>
                <span className={`badge ${st.cls}`}>{st.text}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                <span>
                  {r.match_score ? (
                    <span style={{ fontWeight: 600, color: r.match_score >= 80 ? 'var(--success)' : r.match_score >= 60 ? '#D97706' : 'inherit' }}>
                      Match: {r.match_score}%
                    </span>
                  ) : 'Match: —'}
                </span>
                <span>{r.model || '—'}</span>
                <span>{r.date}</span>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <Link to={`/app/results/${r.id}`} className="btn btn-secondary btn-sm" style={{ flex: 1 }}><Eye size={14} /> Открыть</Link>
                <button className="btn btn-ghost btn-sm" onClick={() => alert('Загрузка началась...')}><Download size={14} /></button>
                <button className="btn btn-ghost btn-sm" style={{ color: 'var(--danger)' }} onClick={() => alert(`Резюме "${r.title}" удалено`)}><Trash2 size={14} /></button>
              </div>
            </div>
          )
        })}
      </div>

      {/* Pagination */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem' }}>
        <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Показано 5 из 12</span>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn btn-secondary btn-sm" disabled>← Назад</button>
          <button className="btn btn-secondary btn-sm">Далее →</button>
        </div>
      </div>
    </>
  )
}

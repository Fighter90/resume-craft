import { Link, useNavigate } from 'react-router-dom'
import { Search, Plus, FileText, Download, Trash2, Eye, Loader, Zap, X, ChevronDown } from 'lucide-react'
import { useEffect, useState, useRef, useCallback } from 'react'
import { api } from '../../services/api'
import ResumeViewerModal from '../../components/ResumeViewerModal'

/* eslint-disable @typescript-eslint/no-explicit-any */

const statusLabel = (s: string) => {
  switch (s) {
    case 'optimized': return { text: 'Оптимизировано', cls: 'badge-green' }
    case 'draft': return { text: 'Черновик', cls: 'badge-gray' }
    case 'processing': return { text: 'В обработке', cls: 'badge-yellow' }
    default: return { text: s, cls: 'badge-gray' }
  }
}

const STATUS_MAP: Record<string, string> = {
  'Все статусы': '',
  'Оптимизировано': 'optimized',
  'Черновик': 'draft',
  'В обработке': 'processing',
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export default function ResumesPage() {
  const navigate = useNavigate()
  const [resumes, setResumes] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('Все статусы')
  const [sortBy, setSortBy] = useState('По дате (новые)')
  // P2-2: Modal delete confirmation state
  const [deleteTarget, setDeleteTarget] = useState<{ id: string; title: string } | null>(null)
  const [deleting, setDeleting] = useState(false)
  // FEATURE-003: Resume viewer modal
  const [viewerId, setViewerId] = useState<string | null>(null)
  // FEATURE-002: Download dropdown
  const [downloadMenuId, setDownloadMenuId] = useState<string | null>(null)
  const [downloadingId, setDownloadingId] = useState<string | null>(null)
  const downloadMenuRef = useRef<HTMLDivElement>(null)

  // Close download menu on outside click
  useEffect(() => {
    if (!downloadMenuId) return
    const handler = (e: MouseEvent) => {
      if (downloadMenuRef.current && !downloadMenuRef.current.contains(e.target as Node)) {
        setDownloadMenuId(null)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [downloadMenuId])

  // Close download menu on Escape
  useEffect(() => {
    if (!downloadMenuId) return
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') setDownloadMenuId(null) }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [downloadMenuId])

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.getResumes()
        setResumes(Array.isArray(res) ? res : [])
      } catch { /* empty */ }
      finally { setLoading(false) }
    }
    load()
  }, [])

  // P2-2: Modal-based delete instead of window.confirm
  const handleDelete = (id: string, title: string) => {
    setDeleteTarget({ id, title })
  }

  const confirmDelete = async () => {
    if (!deleteTarget) return
    setDeleting(true)
    try {
      await api.deleteResume(deleteTarget.id)
      setResumes(prev => prev.filter(r => r.id !== deleteTarget.id))
      setDeleteTarget(null)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Ошибка удаления')
    } finally {
      setDeleting(false)
    }
  }

  const handleOptimize = (r: any) => {
    if (!confirm(`Оптимизировать резюме "${r.title || 'Резюме'}"? Вы перейдёте к выбору вакансии.`)) return
    navigate(`/app/vacancy?resumeId=${r.id}`)
  }

  // FEATURE-003: Open viewer modal
  const handleView = useCallback((r: any) => {
    setViewerId(r.id)
  }, [])

  // FEATURE-002: Download with format selection
  const handleDownloadFormat = async (r: any, format: string) => {
    setDownloadMenuId(null)
    setDownloadingId(r.id)
    try {
      if (r.status === 'optimized') {
        const history = await api.getRewriteHistory()
        const task = (history as any[]).find((h: any) => h.resume_id === r.id && h.status === 'completed')
        if (task) {
          let blob: Blob
          if (format === 'pdf') blob = await api.exportPdf(task.id)
          else if (format === 'txt') blob = await api.exportTxt(task.id)
          else blob = await api.exportDocx(task.id)
          triggerDownload(blob, `${r.title || 'resume'}_optimized.${format}`)
          return
        }
      }
      // Download original
      try {
        const blob = await api.downloadResumeFile(r.id)
        const fmt = (r.file_format || 'bin').toLowerCase()
        triggerDownload(blob, `${r.title || 'resume'}.${fmt}`)
      } catch {
        if (r.raw_text) {
          const blob = new Blob([r.raw_text], { type: 'text/plain;charset=utf-8' })
          triggerDownload(blob, `${r.title || 'resume'}.txt`)
        } else {
          alert('Файл недоступен для скачивания')
        }
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Ошибка скачивания')
    } finally {
      setDownloadingId(null)
    }
  }

  // Filter by search
  let filtered = resumes.filter(r =>
    !searchQuery || (r.title || '').toLowerCase().includes(searchQuery.toLowerCase())
  )

  // Filter by status
  const statusValue = STATUS_MAP[statusFilter] || ''
  if (statusValue) {
    filtered = filtered.filter(r => r.status === statusValue)
  }

  // Sort
  if (sortBy === 'По дате (новые)') {
    filtered.sort((a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime())
  } else if (sortBy === 'По названию') {
    filtered.sort((a, b) => (a.title || '').localeCompare(b.title || ''))
  }
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
          <div style={{ position: 'relative', display: 'flex', gap: '0.5rem' }}>
            <div style={{ position: 'relative', flex: 1 }}>
              <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-tertiary)' }} />
              <input className="input-field" placeholder="Поиск резюме..." style={{ paddingLeft: '2.5rem' }} value={searchQuery} onChange={e => setSearchQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && setSearchQuery(e.currentTarget.value)} />
            </div>
            <button className="btn btn-primary btn-sm" onClick={() => setSearchQuery(searchQuery)} aria-label="Искать">
              <Search size={16} />
            </button>
          </div>
        </div>
        <select className="input-field select-field" style={{ maxWidth: 200 }} value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
          <option>Все статусы</option>
          <option>Оптимизировано</option>
          <option>Черновик</option>
          <option>В обработке</option>
        </select>
        <select className="input-field select-field" style={{ maxWidth: 200 }} value={sortBy} onChange={e => setSortBy(e.target.value)}>
          <option>По дате (новые)</option>
          <option>По названию</option>
        </select>
        <button className="btn btn-primary btn-sm" onClick={() => { /* filters apply on change already, button for UX */ }}>Применить</button>
      </div>

      {/* Desktop Table */}
      <div className="card resumes-desktop-table" style={{ overflowX: 'auto', overflowY: 'visible' }}>
        {loading ? (
          <div style={{ padding: '2rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
            <Loader size={16} className="spin" /> Загрузка...
          </div>
        ) : filtered.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            {searchQuery ? 'Ничего не найдено' : 'Нет загруженных резюме'}
          </div>
        ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Название</th>
              <th>Статус</th>
              <th>Формат</th>
              <th>Дата</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((r: any) => {
              const st = statusLabel(r.status)
              return (
                <tr key={r.id}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }} onClick={() => handleView(r)}>
                      <div style={{ width: 36, height: 36, borderRadius: 8, background: '#F3F4F6', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
                        <FileText size={16} />
                      </div>
                      <div>
                        <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--primary)' }}>{r.title || 'Резюме'}</div>
                        <div style={{ fontSize: '0.78rem', color: 'var(--text-tertiary)' }}>.{r.file_format || '?'}</div>
                      </div>
                    </div>
                  </td>
                  <td><span className={`badge ${st.cls}`}>{st.text}</span></td>
                  <td>{r.file_format?.toUpperCase() || '—'}</td>
                  <td style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{r.created_at ? new Date(r.created_at).toLocaleDateString('ru-RU') : '—'}</td>
                  <td>
                    <div className="td-actions">
                      <button className="btn btn-ghost btn-icon" title="Просмотр" onClick={() => handleView(r)}><Eye size={16} /></button>
                      <button className="btn btn-ghost btn-icon" title="Оптимизировать" style={{ color: 'var(--primary)' }} onClick={() => handleOptimize(r)}><Zap size={16} /></button>
                      <div style={{ position: 'relative' }} ref={downloadMenuId === r.id ? downloadMenuRef : undefined}>
                        <button className="btn btn-ghost btn-icon" title="Скачать"
                          onClick={() => setDownloadMenuId(downloadMenuId === r.id ? null : r.id)}
                          disabled={downloadingId === r.id}>
                          {downloadingId === r.id ? <Loader size={16} className="spin" /> : <><Download size={16} /><ChevronDown size={10} /></>}
                        </button>
                        {downloadMenuId === r.id && (
                          <div style={{
                            position: 'absolute', top: '100%', right: 0, marginTop: 4,
                            background: 'var(--card-bg, #fff)', border: '1px solid var(--border)',
                            borderRadius: 8, boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                            zIndex: 100, minWidth: 180, overflow: 'hidden',
                            animation: 'fadeIn 150ms ease-out',
                          }}>
                            {r.status === 'optimized' ? (
                              <>
                                {[
                                  { fmt: 'docx', label: 'Скачать DOCX', icon: '📄' },
                                  { fmt: 'pdf', label: 'Скачать PDF', icon: '📑' },
                                  { fmt: 'txt', label: 'Скачать TXT', icon: '📝' },
                                ].map(({ fmt: f, label, icon }) => (
                                  <button key={f} onClick={() => handleDownloadFormat(r, f)} style={{
                                    display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.65rem 1rem',
                                    width: '100%', border: 'none', background: 'none', cursor: 'pointer',
                                    fontSize: '0.85rem', textAlign: 'left', color: 'var(--text)',
                                  }}
                                    onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-hover, #F3F4F6)')}
                                    onMouseLeave={e => (e.currentTarget.style.background = 'none')}>
                                    {icon} {label}
                                  </button>
                                ))}
                              </>
                            ) : (
                              <button onClick={() => handleDownloadFormat(r, 'original')} style={{
                                display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.65rem 1rem',
                                width: '100%', border: 'none', background: 'none', cursor: 'pointer',
                                fontSize: '0.85rem', textAlign: 'left', color: 'var(--text)',
                              }}
                                onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-hover, #F3F4F6)')}
                                onMouseLeave={e => (e.currentTarget.style.background = 'none')}>
                                📥 Скачать оригинал
                              </button>
                            )}
                          </div>
                        )}
                      </div>
                      <button className="btn btn-ghost btn-icon" title="Удалить" style={{ color: 'var(--danger)' }} onClick={() => handleDelete(r.id, r.title || 'Резюме')}><Trash2 size={16} /></button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
        )}
      </div>

      {/* Mobile Cards */}
      <div className="resumes-mobile-cards">
        {filtered.map((r: any) => {
          const st = statusLabel(r.status)
          return (
            <div key={r.id} className="card" style={{ padding: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <div style={{ width: 36, height: 36, borderRadius: 8, background: '#F3F4F6', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
                    <FileText size={16} />
                  </div>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{r.title || 'Резюме'}</div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-tertiary)' }}>{r.file_format?.toUpperCase() || ''}</div>
                  </div>
                </div>
                <span className={`badge ${st.cls}`}>{st.text}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                <span>{r.created_at ? new Date(r.created_at).toLocaleDateString('ru-RU') : '—'}</span>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button className="btn btn-secondary btn-sm" style={{ flex: 1 }} onClick={() => handleView(r)}><Eye size={14} /> Открыть</button>
                <button className="btn btn-ghost btn-sm" style={{ color: 'var(--primary)' }} onClick={() => handleOptimize(r)}><Zap size={14} /> Оптимизировать</button>
                <button className="btn btn-ghost btn-sm" onClick={() => handleDownloadFormat(r, r.status === 'optimized' ? 'docx' : 'original')}><Download size={14} /></button>
                <button className="btn btn-ghost btn-sm" style={{ color: 'var(--danger)' }} onClick={() => handleDelete(r.id, r.title || 'Резюме')}><Trash2 size={14} /></button>
              </div>
            </div>
          )
        })}
      </div>

      {/* Count */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem' }}>
        <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Показано {filtered.length} из {resumes.length}</span>
      </div>

      {/* P2-2: Delete confirmation modal */}
      {deleteTarget && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999 }}
          onClick={() => !deleting && setDeleteTarget(null)}>
          <div style={{ background: 'var(--surface)', borderRadius: '1rem', padding: '2rem', maxWidth: 420, width: '90%', boxShadow: '0 20px 60px rgba(0,0,0,0.3)' }}
            onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ margin: 0, fontSize: '1.15rem' }}>Удалить резюме?</h3>
              <button onClick={() => setDeleteTarget(null)} disabled={deleting}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', padding: '0.25rem' }}
                aria-label="Закрыть">
                <X size={20} />
              </button>
            </div>
            <p style={{ color: 'var(--text-secondary)', margin: '0 0 1.5rem', lineHeight: 1.5 }}>
              Резюме <strong>«{deleteTarget.title}»</strong> будет удалено без возможности восстановления.
            </p>
            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
              <button className="btn btn-ghost" onClick={() => setDeleteTarget(null)} disabled={deleting}>Отмена</button>
              <button className="btn" onClick={confirmDelete} disabled={deleting}
                style={{ background: 'var(--danger)', color: '#fff', opacity: deleting ? 0.7 : 1 }}>
                {deleting ? 'Удаление…' : 'Удалить'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* FEATURE-003: Resume viewer modal */}
      {viewerId && (
        <ResumeViewerModal
          resumeId={viewerId}
          onClose={() => setViewerId(null)}
        />
      )}
    </>
  )
}

import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { ArrowLeft, Search, AlertCircle, Loader, X, MapPin, DollarSign, Clock, ExternalLink, Briefcase, Info, CheckCircle, ChevronLeft, ChevronRight } from 'lucide-react'
import { useState, useEffect, useCallback } from 'react'
import DOMPurify from 'dompurify'
import { api } from '../../services/api'
import { useWizard } from '../../contexts/WizardContext'

/* eslint-disable @typescript-eslint/no-explicit-any */

export default function VacancyPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { resumeId, setVacancyId, setResumeId } = useWizard()
  const [tab, setTab] = useState(0)
  const [selected, setSelected] = useState<string | null>(null)

  // Read resumeId from URL query if navigating from resumes page
  useEffect(() => {
    const rid = searchParams.get('resumeId')
    if (rid) setResumeId(rid)
  }, [searchParams, setResumeId])

  // VACANCY-PLACEHOLDER-001: prefill manual title from resume metadata.
  useEffect(() => {
    const loadResumeTitle = async () => {
      if (!resumeId) return
      try {
        const resume = await api.getResume(resumeId)
        const parsed = (resume.parsed_data ?? {}) as Record<string, unknown>
        const fromParsed = [
          parsed.position,
          parsed.target_position,
          parsed.desired_position,
          parsed.current_position,
          parsed.job_title,
          parsed.extracted_position,
          parsed.title,
        ].find((v): v is string => typeof v === 'string' && v.trim().length > 0)

        // V42-FIX: VACANCY-TITLE-002 — filter filename-like values (e.g. "resume.pdf")
        let resumeTitle = typeof resume.title === 'string' ? resume.title.trim() : ''
        if (/\.\w{2,5}$/.test(resumeTitle)) resumeTitle = ''
        const defaultTitle = (fromParsed || resumeTitle || '').trim()
        if (defaultTitle) {
          setManualTitle(defaultTitle)
          setSearchQuery(defaultTitle)
        }
      } catch {
        // Silent fallback: user can still enter title manually.
      }
    }

    void loadResumeTitle()
  }, [resumeId])

  // Search state
  const [searchQuery, setSearchQuery] = useState('')
  const [searchCity, setSearchCity] = useState('Москва')
  const [vacancies, setVacancies] = useState<any[]>([])
  const [searching, setSearching] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)

  // Pagination
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const PER_PAGE = 10

  // Vacancy details modal
  const [detailVacancy, setDetailVacancy] = useState<any>(null)
  const [detailLoading, setDetailLoading] = useState(false)

  // LIVE-001: Закрытие модалки по Escape
  const closeModal = useCallback(() => setDetailVacancy(null), [])
  useEffect(() => {
    if (!detailVacancy) return
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') closeModal() }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [detailVacancy, closeModal])

  // URL state
  const [url, setUrl] = useState('')
  const [urlLoading, setUrlLoading] = useState(false)
  const [urlError, setUrlError] = useState<string | null>(null)

  // Manual state
  const [manualTitle, setManualTitle] = useState('')
  const [manualCompany, setManualCompany] = useState('')
  const [manualDesc, setManualDesc] = useState('')
  const [manualSkills, setManualSkills] = useState('')
  const [manualLoading, setManualLoading] = useState(false)
  const [manualError, setManualError] = useState<string | null>(null)

  const AREA_MAP: Record<string, string> = { 'Москва': '1', 'Санкт-Петербург': '2', 'Удалённо': '113' }

  const handleShowDetails = async (v: any) => {
    setDetailVacancy(v)
    if (!v.description) {
      setDetailLoading(true)
      try {
        const full = await api.getHHVacancyDetail(v.hh_id)
        setDetailVacancy({ ...v, ...full })
      } catch {
        // keep partial data from search
      } finally {
        setDetailLoading(false)
      }
    }
  }

  const handleSearch = async (page = 1) => {
    if (!searchQuery.trim()) return
    setSearching(true)
    setSearchError(null)
    try {
      const params: Record<string, string> = { text: searchQuery, per_page: String(PER_PAGE), page: String(page - 1) }
      if (AREA_MAP[searchCity]) params.area = AREA_MAP[searchCity]
      const response = await api.searchVacancies(params) as any
      const items = response.items || response || []
      setVacancies(items)
      setCurrentPage(page)
      const pages = response.pages || Math.ceil((response.found || items.length) / PER_PAGE) || 1
      setTotalPages(Math.max(1, pages))
      if (items.length === 0) setSearchError('Вакансии не найдены. Попробуйте другой запрос.')
    } catch (err) {
      setSearchError(err instanceof Error ? err.message : 'Ошибка поиска')
    } finally {
      setSearching(false)
    }
  }

  const handleUrlSubmit = async () => {
    if (!url.trim()) return
    setUrlLoading(true)
    setUrlError(null)
    try {
      const res = await api.createVacancyFromUrl(url) as any
      setVacancyId(res.id)
      navigate('/app/models')
    } catch (err) {
      setUrlError(err instanceof Error ? err.message : 'Ошибка загрузки вакансии')
    } finally {
      setUrlLoading(false)
    }
  }

  const handleManualSubmit = async () => {
    if (!manualTitle.trim() || !manualDesc.trim()) return
    setManualLoading(true)
    setManualError(null)
    try {
      const skills = manualSkills.split(',').map(s => s.trim()).filter(Boolean)
      const res = await api.createVacancyManual({
        title: manualTitle,
        company: manualCompany || undefined,
        description: manualDesc,
        key_skills: skills.length > 0 ? skills : undefined,
      }) as any
      setVacancyId(res.id)
      navigate('/app/models')
    } catch (err) {
      setManualError(err instanceof Error ? err.message : 'Ошибка создания вакансии')
    } finally {
      setManualLoading(false)
    }
  }

  const handleSelectVacancy = async () => {
    if (!selected) return
    const vacancy = vacancies.find((v: any) => v.hh_id === selected)
    if (!vacancy) return
    await selectVacancyAndNavigate(vacancy)
  }

  const selectVacancyAndNavigate = async (vacancy: any) => {
    setSearchError(null)
    setSearching(true)
    try {
      const vacUrl = vacancy.url || `https://hh.ru/vacancy/${vacancy.hh_id}`
      const res = await api.createVacancyFromUrl(vacUrl) as any
      setVacancyId(res.id)
      navigate('/app/models')
    } catch (err) {
      setSearchError(err instanceof Error ? err.message : 'Ошибка сохранения вакансии')
    } finally {
      setSearching(false)
    }
  }

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
            <form onSubmit={e => { e.preventDefault(); handleSearch(1) }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="input-group" style={{ gridColumn: '1 / -1' }}>
                  <label className="input-label">Должность</label>
                  <input className="input-field" placeholder="Product Manager" value={searchQuery} onChange={e => setSearchQuery(e.target.value)} />
                </div>
                <div className="input-group">
                  <label className="input-label">Город</label>
                  <select className="input-field select-field" value={searchCity} onChange={e => setSearchCity(e.target.value)}>
                    <option>Москва</option><option>Санкт-Петербург</option><option>Удалённо</option>
                  </select>
                </div>
              </div>
              {searchError && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--error)', marginTop: '0.75rem', fontSize: '0.875rem' }}>
                  <AlertCircle size={16} /> {searchError}
                </div>
              )}
              <button type="submit" className="btn btn-primary" style={{ marginTop: '1rem', height: 48, width: '100%' }} disabled={searching || !searchQuery.trim()}>
                {searching ? <><Loader size={16} className="spin" /> Поиск...</> : <><Search size={16} /> Найти</>}
              </button>
            </form>
          </div>

          <div className="vacancy-results" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            {vacancies.map((v: any) => (
              <div
                key={v.hh_id}
                className={`card vacancy-card${selected === v.hh_id ? ' selected' : ''}`}
                onClick={() => setSelected(v.hh_id)}
                style={{ padding: '1.25rem', cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.25rem' }}>{v.title}</h3>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{v.company || 'Компания не указана'}{v.city ? ` · ${v.city}` : ''}</p>
                  </div>
                  {selected === v.hh_id && <CheckCircle size={18} style={{ color: 'var(--primary)', flexShrink: 0 }} />}
                </div>
                {v.salary_from && (
                  <div style={{ fontWeight: 600, color: 'var(--success)', fontSize: '0.95rem' }}>
                    от {v.salary_from.toLocaleString()} ₽{v.salary_to ? ` до ${v.salary_to.toLocaleString()} ₽` : ''}
                  </div>
                )}
                {v.key_skills && v.key_skills.length > 0 && (
                  <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
                    {v.key_skills.slice(0, 5).map((t: string) => <span key={t} className="badge badge-indigo">{t}</span>)}
                  </div>
                )}
                {/* Per-card action buttons */}
                <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }} onClick={e => e.stopPropagation()}>
                  <button type="button" className="btn btn-secondary btn-sm" style={{ flex: 1 }} onClick={() => handleShowDetails(v)}>
                    <Info size={14} /> Подробнее
                  </button>
                  <button type="button" className="btn btn-primary btn-sm" style={{ flex: 1 }} onClick={() => selectVacancyAndNavigate(v)} disabled={searching}>
                    <CheckCircle size={14} /> Выбрать
                  </button>
                </div>
              </div>
            ))}
          </div>

          {selected && (
            <button onClick={handleSelectVacancy} className="btn btn-primary btn-block" style={{ marginTop: '1.5rem' }}>
              Продолжить с выбранной вакансией
            </button>
          )}

          {/* Pagination */}
          {vacancies.length > 0 && totalPages > 1 && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem', marginTop: '1.5rem' }}>
              <button className="btn btn-secondary btn-sm" disabled={currentPage <= 1 || searching} onClick={() => handleSearch(currentPage - 1)}>
                <ChevronLeft size={16} /> Назад
              </button>
              <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                Страница {currentPage} из {totalPages}
              </span>
              <button className="btn btn-secondary btn-sm" disabled={currentPage >= totalPages || searching} onClick={() => handleSearch(currentPage + 1)}>
                Вперёд <ChevronRight size={16} />
              </button>
            </div>
          )}
        </>
      )}

      {/* Tab 1: URL */}
      {tab === 1 && (
        <div className="card" style={{ padding: '1.5rem' }}>
          <div className="input-group" style={{ marginBottom: '1rem' }}>
            <label className="input-label">Ссылка на вакансию hh.ru</label>
            <input className="input-field" placeholder="https://hh.ru/vacancy/12345678" value={url} onChange={e => setUrl(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleUrlSubmit()} />
          </div>
          {urlError && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--error)', marginBottom: '0.75rem', fontSize: '0.875rem' }}>
              <AlertCircle size={16} /> {urlError}
            </div>
          )}
          <button onClick={handleUrlSubmit} className="btn btn-primary" disabled={urlLoading || !url.trim()}>
            {urlLoading ? 'Загрузка...' : 'Загрузить вакансию'}
          </button>
        </div>
      )}

      {/* Tab 2: Manual */}
      {tab === 2 && (
        <div className="card" style={{ padding: '1.5rem' }}>
          <div className="input-group" style={{ marginBottom: '1rem' }}>
            <label className="input-label">Название должности *</label>
            <input className="input-field" placeholder="Product Manager" value={manualTitle} onChange={e => setManualTitle(e.target.value)} />
          </div>
          <div className="input-group" style={{ marginBottom: '1rem' }}>
            <label className="input-label">Компания</label>
            <input className="input-field" placeholder="Яндекс" value={manualCompany} onChange={e => setManualCompany(e.target.value)} />
          </div>
          <div className="input-group" style={{ marginBottom: '1rem' }}>
            <label className="input-label">Описание и требования *</label>
            <textarea className="input-field" rows={4} placeholder="Опишите обязанности, требования..." value={manualDesc} onChange={e => setManualDesc(e.target.value)} />
          </div>
          <div className="input-group" style={{ marginBottom: '1rem' }}>
            <label className="input-label">Ключевые навыки (через запятую)</label>
            <input className="input-field" placeholder="SQL, Agile, Product Strategy" value={manualSkills} onChange={e => setManualSkills(e.target.value)} />
          </div>
          {manualError && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--error)', marginBottom: '0.75rem', fontSize: '0.875rem' }}>
              <AlertCircle size={16} /> {manualError}
            </div>
          )}
          <button onClick={handleManualSubmit} className="btn btn-primary" disabled={manualLoading || !manualTitle.trim() || !manualDesc.trim()}>
            {manualLoading ? 'Создание...' : 'Продолжить'}
          </button>
        </div>
      )}

      {/* Vacancy Details Modal */}
      {detailVacancy && (
        <div
          className="modal-overlay"
          data-testid="vacancy-detail-modal"
          style={{
            position: 'fixed', inset: 0, zIndex: 1000,
            background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(4px)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            padding: '1rem',
          }}
          onClick={() => setDetailVacancy(null)}
        >
          <div
            className="card"
            style={{
              maxWidth: 640, width: '100%', maxHeight: '85vh', overflow: 'auto',
              padding: '1.5rem', position: 'relative',
            }}
            onClick={e => e.stopPropagation()}
          >
            <button
              onClick={() => setDetailVacancy(null)}
              style={{
                position: 'absolute', top: '1rem', right: '1rem',
                background: 'none', border: 'none', cursor: 'pointer',
                color: 'var(--text-secondary)', padding: '0.25rem',
              }}
              aria-label="Закрыть"
            >
              <X size={20} />
            </button>

            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '1.25rem', paddingRight: '2rem' }}>
              <Briefcase size={18} style={{ verticalAlign: '-3px', marginRight: '0.5rem' }} />
              Подробности вакансии
            </h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>{detailVacancy.title}</h3>
                {detailVacancy.company && (
                  <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>{detailVacancy.company}</div>
                )}
              </div>

              <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', fontSize: '0.85rem' }}>
                {detailVacancy.city && (
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', color: 'var(--text-secondary)' }}>
                    <MapPin size={14} /> {detailVacancy.city}
                  </span>
                )}
                {(detailVacancy.salary_from || detailVacancy.salary_to) && (
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', color: 'var(--success)', fontWeight: 600 }}>
                    <DollarSign size={14} />
                    {detailVacancy.salary_from && detailVacancy.salary_to
                      ? `${detailVacancy.salary_from.toLocaleString('ru-RU')} – ${detailVacancy.salary_to.toLocaleString('ru-RU')} ₽`
                      : detailVacancy.salary_from
                        ? `от ${detailVacancy.salary_from.toLocaleString('ru-RU')} ₽`
                        : `до ${detailVacancy.salary_to.toLocaleString('ru-RU')} ₽`
                    }
                  </span>
                )}
                {detailVacancy.experience && (
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', color: 'var(--text-secondary)' }}>
                    <Clock size={14} /> {detailVacancy.experience}
                  </span>
                )}
              </div>

              {detailVacancy.key_skills?.length > 0 && (
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.85rem', marginBottom: '0.5rem' }}>Ключевые навыки</div>
                  <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
                    {detailVacancy.key_skills.map((s: string) => (
                      <span key={s} className="badge badge-indigo">{s}</span>
                    ))}
                  </div>
                </div>
              )}

              {detailLoading && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                  <Loader size={14} className="spin" /> Загрузка полных данных...
                </div>
              )}

              {detailVacancy.description && (
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.85rem', marginBottom: '0.5rem' }}>Описание</div>
                  <div
                    style={{ fontSize: '0.85rem', lineHeight: 1.7, color: 'var(--text-secondary)', whiteSpace: 'pre-wrap' }}
                    dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(detailVacancy.description) }}
                  />
                </div>
              )}

              {detailVacancy.snippet?.requirement && (
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.85rem', marginBottom: '0.5rem' }}>Требования</div>
                  <div
                    style={{ fontSize: '0.85rem', lineHeight: 1.7, color: 'var(--text-secondary)' }}
                    dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(detailVacancy.snippet.requirement) }}
                  />
                </div>
              )}

              {detailVacancy.snippet?.responsibility && (
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.85rem', marginBottom: '0.5rem' }}>Обязанности</div>
                  <div
                    style={{ fontSize: '0.85rem', lineHeight: 1.7, color: 'var(--text-secondary)' }}
                    dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(detailVacancy.snippet.responsibility) }}
                  />
                </div>
              )}

              {(detailVacancy.url || detailVacancy.hh_id) && (
                <a
                  href={detailVacancy.url || `https://hh.ru/vacancy/${detailVacancy.hh_id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-secondary btn-sm"
                  style={{ alignSelf: 'flex-start', marginTop: '0.25rem' }}
                >
                  <ExternalLink size={14} /> Открыть на hh.ru
                </a>
              )}

              <button className="btn btn-primary" style={{ marginTop: '0.5rem' }}
                onClick={() => { setDetailVacancy(null); selectVacancyAndNavigate(detailVacancy) }}
                disabled={searching}
              >
                <CheckCircle size={16} /> Выбрать эту вакансию
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

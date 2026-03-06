import { useNavigate, useParams } from 'react-router-dom'
import { ArrowRight, Download, TrendingUp, Target, Award, Tag, BookOpen, Cpu, Edit, AlertCircle, Loader, Briefcase, X, MapPin, DollarSign, Clock, ExternalLink } from 'lucide-react'
import DOMPurify from 'dompurify'
import { useWizard } from '../../contexts/WizardContext'
import { useEffect, useState } from 'react'
import { api } from '../../services/api'

/* eslint-disable @typescript-eslint/no-explicit-any */

/** Simple word-level diff for highlighting changes between original and optimized text */
function computeWordDiff(original: string, rewritten: string): { origTokens: { text: string; removed: boolean }[]; newTokens: { text: string; added: boolean }[] } {
  const tokenize = (t: string) => t.split(/(\s+)/).filter(Boolean)
  const origWords = tokenize(original)
  const newWords = tokenize(rewritten)

  const origSet = new Set(origWords.filter(w => w.trim()).map(w => w.trim().toLowerCase()))
  const newSet = new Set(newWords.filter(w => w.trim()).map(w => w.trim().toLowerCase()))

  const origTokens = origWords.map(w => ({
    text: w,
    removed: w.trim() ? !newSet.has(w.trim().toLowerCase()) : false,
  }))
  const newTokens = newWords.map(w => ({
    text: w,
    added: w.trim() ? !origSet.has(w.trim().toLowerCase()) : false,
  }))

  return { origTokens, newTokens }
}

export default function ResultsPage() {
  const navigate = useNavigate()
  const { id: urlId } = useParams<{ id: string }>()
  const { taskId, result, setResult } = useWizard()
  const [loading, setLoading] = useState(!result)
  const [error, setError] = useState<string | null>(null)
  const [vacancyModalOpen, setVacancyModalOpen] = useState(false)
  const [vacancy, setVacancy] = useState<any>(null)
  const [vacancyLoading, setVacancyLoading] = useState(false)

  // Resolve effective ID: wizard taskId → URL param
  const effectiveId = taskId || urlId

  useEffect(() => {
    if (result) { setLoading(false); return }
    if (!effectiveId) { setError('Нет данных для отображения'); setLoading(false); return }
    const fetchResult = async () => {
      try {
        const res = await api.getRewriteResult(effectiveId) as any
        setResult(res)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Ошибка загрузки результатов')
      } finally {
        setLoading(false)
      }
    }
    fetchResult()
  }, [effectiveId]) // eslint-disable-line react-hooks/exhaustive-deps

  const openVacancyModal = async () => {
    if (!result?.vacancy_id) return
    setVacancyModalOpen(true)
    if (vacancy) return // already loaded
    setVacancyLoading(true)
    try {
      const v = await api.getVacancy(result.vacancy_id)
      setVacancy(v)
    } catch {
      setVacancy({ _error: 'Не удалось загрузить данные вакансии' })
    } finally {
      setVacancyLoading(false)
    }
  }

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '40vh', gap: '0.75rem' }}>
      <Loader size={24} className="spin" /> Загрузка результатов...
    </div>
  )
  if (error || !result) return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '40vh', gap: '1rem' }}>
      <AlertCircle size={32} style={{ color: 'var(--error)' }} />
      <p>{error || 'Нет данных'}</p>
      <button onClick={() => navigate('/app/upload')} className="btn btn-primary">Начать заново</button>
    </div>
  )

  const score = result.match_score_after ?? 0
  const scoreBefore = result.match_score_before ?? 0
  const improvement = Math.round(score - scoreBefore)
  const atsRating = result.ats_rating || 'N/A'
  const modelName = result.model_name || 'AI'
  const processingTime = result.processing_time_ms ? Math.round(result.processing_time_ms / 1000) : '—'
  const keywordsAdded: string[] = result.keywords_added || []
  const originalText = result.original_text || ''
  const rewrittenText = result.rewritten_text || ''
  const radius = 54
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference

  return (
    <div>
      {/* Page header — matches prototype */}
      <div className="page-header">
        <div>
          <h1>Результаты оптимизации</h1>
          <p>Оптимизация завершена</p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          {result?.vacancy_id && (
            <button onClick={openVacancyModal} className="btn btn-secondary">
              <Briefcase size={16} /> Вакансия
            </button>
          )}
          <button onClick={() => navigate('/app/editor')} className="btn btn-secondary">
            <Edit size={16} /> Редактировать
          </button>
          <button onClick={() => navigate(`/app/export/${result?.id || effectiveId || ''}`)} className="btn btn-primary">
            <Download size={16} /> Экспорт
          </button>
        </div>
      </div>

      {/* Score cards — 4 cards like prototype */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        {/* Main Match Score */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '1.5rem' }}>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Match Score</div>
          <svg width={100} height={100} viewBox="0 0 128 128" className="score-circle">
            <circle cx="64" cy="64" r={radius} fill="none" stroke="var(--border)" strokeWidth="10" />
            <circle
              cx="64" cy="64" r={radius} fill="none"
              stroke="url(#scoreGrad)" strokeWidth="10" strokeLinecap="round"
              strokeDasharray={circumference} strokeDashoffset={offset}
              transform="rotate(-90 64 64)"
            />
            <defs>
              <linearGradient id="scoreGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="var(--primary)" />
                <stop offset="100%" stopColor="#7C3AED" />
              </linearGradient>
            </defs>
            <text x="64" y="60" textAnchor="middle" fontSize="28" fontWeight="700" fill="var(--text-primary)">{score}</text>
            <text x="64" y="78" textAnchor="middle" fontSize="11" fill="var(--text-secondary)">%</text>
          </svg>
          <div style={{ marginTop: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.85rem', color: 'var(--success)', fontWeight: 600 }}>
            <TrendingUp size={14} />
            +{improvement} пунктов
          </div>
        </div>

        {/* ATS card — separate like prototype */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '1.5rem' }}>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>ATS совместимость</div>
          <div style={{
            width: 64, height: 64, borderRadius: 16, display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '1.75rem', fontWeight: 700, color: 'var(--success)',
            background: 'rgba(16,185,129,0.1)', marginBottom: '0.5rem',
          }}>
            {atsRating}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Отлично</div>
        </div>

        {/* AI Model card — matches prototype */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '1.5rem' }}>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>AI-модель</div>
          <div style={{
            width: 64, height: 64, borderRadius: 16, display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: 'rgba(86,90,221,0.1)', marginBottom: '0.5rem',
          }}>
            <Cpu size={28} style={{ color: 'var(--primary)' }} />
          </div>
          <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{modelName}</div>
        </div>

        {/* Processing time */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '1.5rem' }}>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Время обработки</div>
          <div style={{ fontSize: '2rem', fontWeight: 700 }}>{processingTime}<span style={{ fontSize: '1rem', fontWeight: 400, color: 'var(--text-secondary)' }}> сек</span></div>
        </div>
      </div>

      {/* Metrics breakdown — 4 components per prototype (Keywords 40% + Experience 25% + Structure 20% + Readability 15%) */}
      <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>Компоненты Match Score</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        {[
          { icon: Target, label: 'Ключевые слова', value: Math.round((result.score_breakdown?.keywords ?? score / 100) * 100), weight: '40%', color: 'var(--primary)' },
          { icon: TrendingUp, label: 'Опыт', value: Math.round((result.score_breakdown?.experience ?? score / 100) * 100), weight: '25%', color: 'var(--success)' },
          { icon: Award, label: 'Структура', value: Math.round((result.score_breakdown?.structure ?? score / 100) * 100), weight: '20%', color: 'var(--info)' },
          { icon: BookOpen, label: 'Читаемость', value: Math.round((result.score_breakdown?.readability ?? score / 100) * 100), weight: '15%', color: '#D97706' },
        ].map((m, i) => (
          <div key={i} className="card" style={{ padding: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <m.icon size={20} style={{ color: m.color }} />
              <span className="badge badge-gray">{m.weight}</span>
            </div>
            <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{m.value}%</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>{m.label}</div>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${m.value}%`, background: m.color }} />
            </div>
          </div>
        ))}
      </div>

      {/* Keywords */}
      <div className="card" style={{ padding: '1.25rem', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <Tag size={16} />
          <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Добавленные ключевые слова</h3>
          <span className="badge badge-indigo">{keywordsAdded.length}</span>
        </div>
        <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
          {keywordsAdded.map(kw => (
            <span key={kw} className="badge badge-green">{kw}</span>
          ))}
        </div>
      </div>

      {/* Diff comparison with highlighting */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Сравнение версий</h3>
        <div style={{ display: 'flex', gap: '1rem', fontSize: '0.8rem' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span style={{ width: 12, height: 12, borderRadius: 3, background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)' }} />
            Слабые формулировки
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span style={{ width: 12, height: 12, borderRadius: 3, background: 'rgba(16,185,129,0.15)', border: '1px solid rgba(16,185,129,0.3)' }} />
            Улучшения AI
          </span>
        </div>
      </div>
      <div className="diff-container">
        <div className="diff-panel">
          <div className="diff-header">
            <span style={{ fontWeight: 600 }}>Оригинал</span>
            <span className="badge badge-gray">{Math.round(scoreBefore)} баллов</span>
          </div>
          <div className="diff-content" style={{ fontSize: '0.85rem', lineHeight: 1.7, padding: '1rem' }}>
            {originalText && rewrittenText ? (
              computeWordDiff(originalText, rewrittenText).origTokens.map((t, i) =>
                t.removed ? (
                  <span key={i} style={{ background: 'rgba(239,68,68,0.15)', borderRadius: 2, padding: '0 1px', textDecoration: 'line-through', textDecorationColor: 'rgba(239,68,68,0.5)' }}>{t.text}</span>
                ) : (
                  <span key={i}>{t.text}</span>
                )
              )
            ) : (
              <span style={{ whiteSpace: 'pre-wrap' }}>{originalText || 'Текст оригинала недоступен'}</span>
            )}
          </div>
        </div>
        <div className="diff-panel">
          <div className="diff-header">
            <span style={{ fontWeight: 600 }}>Оптимизировано</span>
            <span className="badge badge-green">{Math.round(score)} баллов</span>
          </div>
          <div className="diff-content" style={{ fontSize: '0.85rem', lineHeight: 1.7, padding: '1rem' }}>
            {originalText && rewrittenText ? (
              computeWordDiff(originalText, rewrittenText).newTokens.map((t, i) =>
                t.added ? (
                  <span key={i} style={{ background: 'rgba(16,185,129,0.15)', borderRadius: 2, padding: '0 1px' }}>{t.text}</span>
                ) : (
                  <span key={i}>{t.text}</span>
                )
              )
            ) : (
              <span style={{ whiteSpace: 'pre-wrap' }}>{rewrittenText || 'Оптимизированный текст недоступен'}</span>
            )}
          </div>
        </div>
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
        <button onClick={() => navigate('/app/editor')} className="btn btn-primary" style={{ flex: 1 }}>
          Редактировать <ArrowRight size={16} />
        </button>
        <button onClick={() => navigate(`/app/export/${result?.id || effectiveId || ''}`)} className="btn btn-secondary" style={{ flex: 1 }}>
          <Download size={16} /> Экспорт
        </button>
      </div>

      {/* Vacancy Details Modal */}
      {vacancyModalOpen && (
        <div
          className="modal-overlay"
          style={{
            position: 'fixed', inset: 0, zIndex: 1000,
            background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(4px)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            padding: '1rem',
          }}
          onClick={() => setVacancyModalOpen(false)}
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
              onClick={() => setVacancyModalOpen(false)}
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

            {vacancyLoading ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', padding: '2rem', color: 'var(--text-secondary)' }}>
                <Loader size={18} className="spin" /> Загрузка...
              </div>
            ) : vacancy?._error ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--error)', padding: '1rem' }}>
                <AlertCircle size={16} /> {vacancy._error}
              </div>
            ) : vacancy ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>{vacancy.title}</h3>
                  {vacancy.company && (
                    <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>{vacancy.company}</div>
                  )}
                </div>

                <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', fontSize: '0.85rem' }}>
                  {vacancy.city && (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', color: 'var(--text-secondary)' }}>
                      <MapPin size={14} /> {vacancy.city}
                    </span>
                  )}
                  {(vacancy.salary_from || vacancy.salary_to) && (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', color: 'var(--success)', fontWeight: 600 }}>
                      <DollarSign size={14} />
                      {vacancy.salary_from && vacancy.salary_to
                        ? `${vacancy.salary_from.toLocaleString('ru-RU')} – ${vacancy.salary_to.toLocaleString('ru-RU')} ₽`
                        : vacancy.salary_from
                          ? `от ${vacancy.salary_from.toLocaleString('ru-RU')} ₽`
                          : `до ${vacancy.salary_to.toLocaleString('ru-RU')} ₽`
                      }
                    </span>
                  )}
                  {vacancy.experience && (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', color: 'var(--text-secondary)' }}>
                      <Clock size={14} /> {vacancy.experience}
                    </span>
                  )}
                </div>

                {vacancy.key_skills?.length > 0 && (
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.85rem', marginBottom: '0.5rem' }}>Ключевые навыки</div>
                    <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
                      {vacancy.key_skills.map((s: string) => (
                        <span key={s} className="badge badge-indigo">{s}</span>
                      ))}
                    </div>
                  </div>
                )}

                {vacancy.requirements && Object.keys(vacancy.requirements).length > 0 && (
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.85rem', marginBottom: '0.5rem' }}>Требования</div>
                    <div style={{ fontSize: '0.85rem', lineHeight: 1.7, color: 'var(--text-secondary)' }}>
                      {typeof vacancy.requirements === 'string'
                        ? vacancy.requirements
                        : Object.entries(vacancy.requirements).map(([k, v]) => (
                            <div key={k} style={{ marginBottom: '0.25rem' }}>
                              <strong>{k}:</strong> {String(v)}
                            </div>
                          ))
                      }
                    </div>
                  </div>
                )}

                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.85rem', marginBottom: '0.5rem' }}>Описание</div>
                  <div
                    style={{ fontSize: '0.85rem', lineHeight: 1.7, color: 'var(--text-secondary)', whiteSpace: 'pre-wrap' }}
                    dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(vacancy.description) }}
                  />
                </div>

                {vacancy.source_url && (
                  <a
                    href={vacancy.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-secondary btn-sm"
                    style={{ alignSelf: 'flex-start', marginTop: '0.5rem' }}
                  >
                    <ExternalLink size={14} /> Открыть на hh.ru
                  </a>
                )}
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  )
}

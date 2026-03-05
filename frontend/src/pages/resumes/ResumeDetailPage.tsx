import { useNavigate, useParams, Link } from 'react-router-dom'
import { ArrowLeft, FileText, Calendar, Tag, Loader, AlertCircle, Edit, Trash2, Briefcase } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api } from '../../services/api'

/* eslint-disable @typescript-eslint/no-explicit-any */

const statusLabel = (s: string) => {
  switch (s) {
    case 'optimized': return { text: 'Оптимизировано', cls: 'badge-green' }
    case 'draft': return { text: 'Черновик', cls: 'badge-gray' }
    case 'processing': return { text: 'В обработке', cls: 'badge-yellow' }
    case 'error': return { text: 'Ошибка', cls: 'badge-red' }
    default: return { text: s, cls: 'badge-gray' }
  }
}

export default function ResumeDetailPage() {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const [resume, setResume] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) { setError('ID резюме не указан'); setLoading(false); return }
    const load = async () => {
      try {
        const res = await api.getResume(id)
        setResume(res)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Ошибка загрузки резюме')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  const handleDelete = async () => {
    if (!id || !confirm('Удалить это резюме?')) return
    try {
      await api.deleteResume(id)
      navigate('/app/resumes')
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Ошибка удаления')
    }
  }

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '40vh', gap: '0.75rem' }}>
      <Loader size={24} className="spin" /> Загрузка резюме...
    </div>
  )

  if (error || !resume) return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '40vh', gap: '1rem' }}>
      <AlertCircle size={32} style={{ color: 'var(--error)' }} />
      <p>{error || 'Резюме не найдено'}</p>
      <Link to="/app/resumes" className="btn btn-primary">Назад к резюме</Link>
    </div>
  )

  const st = statusLabel(resume.status || 'draft')
  const parsedData = resume.parsed_data
  const rawText = resume.raw_text

  return (
    <div>
      {/* Header */}
      <div className="page-header">
        <div>
          <Link to="/app/resumes" className="btn btn-secondary btn-sm" style={{ marginBottom: '0.75rem' }}>
            <ArrowLeft size={16} /> Назад
          </Link>
          <h1>{resume.title || 'Резюме'}</h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginTop: '0.25rem' }}>
            <span className={`badge ${st.cls}`}>{st.text}</span>
            {resume.file_format && <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{resume.file_format?.toUpperCase()}</span>}
            {resume.created_at && (
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                <Calendar size={14} /> {new Date(resume.created_at).toLocaleDateString('ru-RU')}
              </span>
            )}
          </div>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <Link to="/app/upload" className="btn btn-secondary">
            <Edit size={16} /> Оптимизировать
          </Link>
          <button className="btn btn-ghost" style={{ color: 'var(--danger)' }} onClick={handleDelete}>
            <Trash2 size={16} /> Удалить
          </button>
        </div>
      </div>

      {/* Parsed data sections */}
      {parsedData && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '2rem' }}>
          {/* Summary */}
          {parsedData.summary && (
            <div className="card" style={{ padding: '1.25rem' }}>
              <h3 style={{ fontWeight: 600, marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Briefcase size={16} /> Профессиональное саммари
              </h3>
              <p style={{ fontSize: '0.9rem', lineHeight: 1.7, color: 'var(--text-secondary)' }}>{parsedData.summary}</p>
            </div>
          )}

          {/* Experience */}
          {parsedData.experience?.length > 0 && (
            <div className="card" style={{ padding: '1.25rem' }}>
              <h3 style={{ fontWeight: 600, marginBottom: '1rem' }}>Опыт работы</h3>
              {parsedData.experience.map((exp: any, i: number) => (
                <div key={i} style={{ marginBottom: i < parsedData.experience.length - 1 ? '1rem' : 0, paddingBottom: i < parsedData.experience.length - 1 ? '1rem' : 0, borderBottom: i < parsedData.experience.length - 1 ? '1px solid var(--border)' : 'none' }}>
                  <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{exp.position}{exp.company ? ` — ${exp.company}` : ''}</div>
                  {exp.period && <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', marginTop: '0.15rem' }}>{exp.period}</div>}
                  {exp.achievements?.length > 0 && (
                    <ul style={{ margin: '0.5rem 0 0 1.25rem', paddingLeft: 0, fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                      {exp.achievements.map((a: string, j: number) => <li key={j}>{a}</li>)}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Education */}
          {parsedData.education?.length > 0 && (
            <div className="card" style={{ padding: '1.25rem' }}>
              <h3 style={{ fontWeight: 600, marginBottom: '0.75rem' }}>Образование</h3>
              {parsedData.education.map((edu: any, i: number) => (
                <div key={i} style={{ marginBottom: i < parsedData.education.length - 1 ? '0.75rem' : 0 }}>
                  <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{edu.institution}</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    {edu.degree}{edu.specialization ? ` — ${edu.specialization}` : ''}{edu.year ? `, ${edu.year}` : ''}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Skills */}
          {parsedData.skills?.length > 0 && (
            <div className="card" style={{ padding: '1.25rem' }}>
              <h3 style={{ fontWeight: 600, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Tag size={16} /> Навыки
              </h3>
              <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
                {parsedData.skills.map((s: string) => <span key={s} className="badge badge-indigo">{s}</span>)}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Raw text fallback */}
      {(!parsedData || Object.keys(parsedData).length === 0) && rawText && (
        <div className="card" style={{ padding: '1.25rem', marginBottom: '2rem' }}>
          <h3 style={{ fontWeight: 600, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FileText size={16} /> Текст резюме
          </h3>
          <div style={{ whiteSpace: 'pre-wrap', fontSize: '0.9rem', lineHeight: 1.7, color: 'var(--text-secondary)' }}>
            {rawText}
          </div>
        </div>
      )}

      {/* No content */}
      {!parsedData && !rawText && (
        <div className="card" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
          <FileText size={32} style={{ margin: '0 auto 0.75rem', opacity: 0.4 }} />
          <p>Текст резюме ещё не извлечён. Запустите оптимизацию для обработки.</p>
          <Link to="/app/upload" className="btn btn-primary" style={{ marginTop: '1rem' }}>Оптимизировать</Link>
        </div>
      )}
    </div>
  )
}

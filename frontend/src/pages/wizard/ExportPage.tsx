import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Download, FileText, FileType, ExternalLink, Check, AlertCircle, Loader } from 'lucide-react'
import { api } from '../../services/api'
import { useWizard } from '../../contexts/WizardContext'

/* eslint-disable @typescript-eslint/no-explicit-any */

const FORMATS = [
  { id: 'docx', icon: FileText, label: 'DOCX', desc: 'Microsoft Word — рекомендуем для hh.ru' },
  { id: 'pdf', icon: FileType, label: 'PDF', desc: 'Универсальный формат для печати' },
  { id: 'hh', icon: ExternalLink, label: 'hh.ru', desc: 'Обновить резюме на hh.ru напрямую' },
]

const TEMPLATES = [
  { id: 'minimal', label: 'Минималистичный', desc: 'Чистый, без лишнего', color: '#565ADD' },
  { id: 'professional', label: 'Профессиональный', desc: 'Структурированный, с акцентами', color: '#059669' },
  { id: 'creative', label: 'Креативный', desc: 'Современный, с элементами дизайна', color: '#7C3AED' },
]

export default function ExportPage() {
  const navigate = useNavigate()
  const { id: urlId } = useParams<{ id: string }>()
  const { result, setResult } = useWizard()
  const [format, setFormat] = useState('docx')
  const [template, setTemplate] = useState('professional')
  const [downloading, setDownloading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loadingResult, setLoadingResult] = useState(false)

  // If result is not in wizard context but we have a URL ID, fetch it
  useEffect(() => {
    if (result || !urlId) return
    setLoadingResult(true)
    const load = async () => {
      try {
        const res = await api.getRewriteResult(urlId) as any
        setResult(res)
      } catch {
        setError('Не удалось загрузить данные для экспорта')
      } finally {
        setLoadingResult(false)
      }
    }
    load()
  }, [urlId]) // eslint-disable-line react-hooks/exhaustive-deps

  const exportId = result?.id || urlId

  const handleDownload = async () => {
    if (!exportId) {
      setError('Нет данных для экспорта. Выполните оптимизацию сначала.')
      return
    }
    setDownloading(true)
    setError(null)
    try {
      let blob: Blob
      if (format === 'pdf') {
        blob = await api.exportPdf(exportId)
      } else if (format === 'docx') {
        blob = await api.exportDocx(exportId)
      } else {
        // hh format — fallback to docx for now
        blob = await api.exportDocx(exportId)
      }
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `resume_optimized.${format === 'hh' ? 'docx' : format}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка скачивания')
    } finally {
      setDownloading(false)
    }
  }

  if (loadingResult) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '40vh', gap: '0.75rem' }}>
        <Loader size={24} className="spin" /> Загрузка данных...
      </div>
    )
  }

  return (
    <div className="wizard-container">
      <button onClick={() => navigate(-1)} className="btn btn-secondary btn-sm" style={{ marginBottom: '1.5rem' }}>
        <ArrowLeft size={16} /> Назад
      </button>

      <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>Экспорт резюме</h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>Скачайте оптимизированное резюме</p>

      {/* Format selection */}
      <h3 style={{ fontWeight: 600, marginBottom: '1rem' }}>Формат файла</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
        {FORMATS.map(f => (
          <div
            key={f.id}
            className={`card${format === f.id ? ' selected' : ''}`}
            onClick={() => setFormat(f.id)}
            style={{ padding: '1.25rem', cursor: 'pointer', textAlign: 'center', position: 'relative' }}
          >
            <f.icon size={28} style={{ color: 'var(--primary)', marginBottom: '0.5rem' }} />
            <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>{f.label}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{f.desc}</div>
            {format === f.id && (
              <div style={{
                position: 'absolute', top: '0.6rem', right: '0.6rem',
                width: 22, height: 22, borderRadius: '50%', background: 'var(--primary)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <Check size={13} color="#fff" />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Template selection */}
      <h3 style={{ fontWeight: 600, marginBottom: '1rem' }}>Шаблон оформления</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
        {TEMPLATES.map(t => (
          <div
            key={t.id}
            className={`card${template === t.id ? ' selected' : ''}`}
            onClick={() => setTemplate(t.id)}
            style={{ padding: '1.25rem', cursor: 'pointer', position: 'relative' }}
          >
            <div style={{ width: '100%', height: 80, borderRadius: 'var(--radius-sm)', marginBottom: '0.75rem', background: `linear-gradient(135deg, ${t.color}22, ${t.color}44)`, border: `2px solid ${t.color}33` }} />
            <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>{t.label}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{t.desc}</div>
            {template === t.id && (
              <div style={{
                position: 'absolute', top: '0.6rem', right: '0.6rem',
                width: 22, height: 22, borderRadius: '50%', background: 'var(--primary)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <Check size={13} color="#fff" />
              </div>
            )}
          </div>
        ))}
      </div>

      {error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--error)', marginBottom: '1rem', fontSize: '0.875rem' }}>
          <AlertCircle size={16} /> {error}
        </div>
      )}

      <button className="btn btn-primary btn-block" style={{ height: 52 }} onClick={handleDownload} disabled={downloading}>
        {downloading ? <><Loader size={18} className="spin" /> Скачивание...</> : <><Download size={18} /> Скачать {format.toUpperCase()}</>}
      </button>

      {/* Ready to download — matches prototype */}
      <div className="card" style={{ padding: '1.25rem', marginTop: '1.5rem' }}>
        <h3 style={{ fontWeight: 600, marginBottom: '1rem' }}>Готово к скачиванию</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', fontSize: '0.85rem' }}>
          <div>
            <span style={{ color: 'var(--text-secondary)' }}>Файл:</span>{' '}
            <span style={{ fontWeight: 500 }}>resume_optimized.{format}</span>
          </div>
          <div>
            <span style={{ color: 'var(--text-secondary)' }}>Шаблон:</span>{' '}
            <span style={{ fontWeight: 500 }}>{TEMPLATES.find(t => t.id === template)?.label}</span>
          </div>
          <div>
            <span style={{ color: 'var(--text-secondary)' }}>Размер:</span>{' '}
            <span style={{ fontWeight: 500 }}>~48 КБ</span>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <span className="badge badge-green">Match {Math.round((result?.match_score_after ?? 0) <= 1 ? (result?.match_score_after ?? 0) * 100 : (result?.match_score_after ?? 0))}%</span>
            <span className="badge badge-green">ATS {result?.ats_rating || '—'}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

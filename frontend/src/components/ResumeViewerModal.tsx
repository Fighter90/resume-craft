import { useEffect, useState, useMemo } from 'react'
import { X, Download, Loader, Eye, FileText, GitCompare, Briefcase, GraduationCap, Wrench, User, AlertCircle } from 'lucide-react'
import mammoth from 'mammoth'
import DOMPurify from 'dompurify'
import { api } from '../services/api'

/* eslint-disable @typescript-eslint/no-explicit-any */

interface ResumeViewerModalProps {
  resumeId: string
  onClose: () => void
}

type TabId = 'original' | 'optimized' | 'comparison'

/** Parse optimized_text JSON into readable sections */
function parseOptimizedJSON(data: any): {
  contacts?: { name?: string; phone?: string; email?: string; city?: string; position?: string }
  summary?: string
  experience?: Array<{ position: string; company: string; period: string; achievements: string[] }>
  education?: Array<{ institution: string; degree: string; specialization?: string; period?: string; year?: number }>
  skills?: string[]
} | null {
  if (!data || typeof data !== 'object') return null
  return data
}

/** Try to parse a text string as JSON */
function tryParseJSON(text: string): any | null {
  const trimmed = text.trim()
  // Check for JSON wrapped in markdown code block
  let jsonStr = trimmed
  if (jsonStr.startsWith('```json')) {
    jsonStr = jsonStr.slice(7)
    const endIdx = jsonStr.lastIndexOf('```')
    if (endIdx > 0) jsonStr = jsonStr.slice(0, endIdx)
    jsonStr = jsonStr.trim()
  } else if (jsonStr.startsWith('```')) {
    jsonStr = jsonStr.slice(3)
    const endIdx = jsonStr.lastIndexOf('```')
    if (endIdx > 0) jsonStr = jsonStr.slice(0, endIdx)
    jsonStr = jsonStr.trim()
  }
  if (jsonStr.startsWith('{') && jsonStr.endsWith('}')) {
    try { return JSON.parse(jsonStr) } catch { /* not JSON */ }
  }
  return null
}

/** Simple word-level diff for comparison tab */
function computeWordDiff(original: string, rewritten: string) {
  const tokenize = (t: string) => t.split(/(\s+)/).filter(Boolean)
  const origWords = tokenize(original)
  const newWords = tokenize(rewritten)
  const origSet = new Set(origWords.filter(w => w.trim()).map(w => w.trim().toLowerCase()))
  const newSet = new Set(newWords.filter(w => w.trim()).map(w => w.trim().toLowerCase()))
  return {
    origTokens: origWords.map(w => ({ text: w, removed: w.trim() ? !newSet.has(w.trim().toLowerCase()) : false })),
    newTokens: newWords.map(w => ({ text: w, added: w.trim() ? !origSet.has(w.trim().toLowerCase()) : false })),
  }
}

/** Convert optimized JSON to readable plaintext for diff */
function jsonToPlainText(data: any): string {
  const parts: string[] = []
  if (data.contacts?.name) parts.push(data.contacts.name)
  if (data.contacts?.position) parts.push(data.contacts.position)
  if (data.summary) { parts.push('', data.summary, '') }
  if (data.experience?.length) {
    parts.push('ОПЫТ РАБОТЫ', '')
    for (const exp of data.experience) {
      parts.push(`${exp.position || ''} — ${exp.company || ''}`)
      if (exp.period || exp.dates) parts.push(exp.period || exp.dates)
      for (const a of (exp.achievements || [])) parts.push(`• ${a}`)
      if (exp.description) parts.push(exp.description)
      parts.push('')
    }
  }
  if (data.education?.length) {
    parts.push('ОБРАЗОВАНИЕ', '')
    for (const edu of data.education) {
      parts.push(`${edu.institution || ''} — ${edu.degree || ''} ${edu.specialization || ''}${edu.year ? `, ${edu.year}` : ''}`)
    }
    parts.push('')
  }
  if (data.skills?.length) parts.push('НАВЫКИ', '', data.skills.join(', '))
  return parts.join('\n')
}

/** Render formatted structured data from JSON */
function FormattedResume({ data }: { data: any }) {
  const parsed = parseOptimizedJSON(data)
  if (!parsed) return <div style={{ color: 'var(--text-secondary)' }}>Нет данных</div>

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      {/* Contacts / Header */}
      {parsed.contacts && (
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          {parsed.contacts.name && (
            <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.25rem' }}>{parsed.contacts.name}</h2>
          )}
          {parsed.contacts.position && (
            <div style={{ fontSize: '1rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>{parsed.contacts.position}</div>
          )}
          <div style={{ fontSize: '0.85rem', color: 'var(--text-tertiary)', display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            {parsed.contacts.phone && <span>{parsed.contacts.phone}</span>}
            {parsed.contacts.email && <span>{parsed.contacts.email}</span>}
            {parsed.contacts.city && <span>{parsed.contacts.city}</span>}
          </div>
          <hr style={{ border: 'none', borderTop: '2px solid var(--border)', margin: '1rem 0' }} />
        </div>
      )}

      {/* Summary */}
      {parsed.summary && (
        <div style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
            <User size={16} style={{ color: 'var(--primary)' }} /> ПРОФЕССИОНАЛЬНОЕ РЕЗЮМЕ
          </h3>
          <p style={{ fontSize: '0.9rem', lineHeight: 1.7, color: 'var(--text-secondary)' }}>{parsed.summary}</p>
        </div>
      )}

      {/* Experience */}
      {parsed.experience && parsed.experience.length > 0 && (
        <div style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', color: 'var(--text-primary)' }}>
            <Briefcase size={16} style={{ color: 'var(--primary)' }} /> ОПЫТ РАБОТЫ
          </h3>
          {parsed.experience.map((exp, i) => (
            <div key={i} style={{
              marginBottom: '1rem', paddingBottom: '1rem',
              borderBottom: i < parsed.experience!.length - 1 ? '1px solid var(--border)' : 'none',
            }}>
              <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{exp.position}</div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                {exp.company}{exp.period ? ` | ${exp.period}` : ''}
              </div>
              {exp.achievements?.length > 0 && (
                <ul style={{ margin: '0.5rem 0 0 1rem', paddingLeft: '0.5rem', fontSize: '0.85rem', lineHeight: 1.7, color: 'var(--text-secondary)' }}>
                  {exp.achievements.map((a, j) => <li key={j}>{a}</li>)}
                </ul>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Education */}
      {parsed.education && parsed.education.length > 0 && (
        <div style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', color: 'var(--text-primary)' }}>
            <GraduationCap size={16} style={{ color: 'var(--primary)' }} /> ОБРАЗОВАНИЕ
          </h3>
          {parsed.education.map((edu, i) => (
            <div key={i} style={{ marginBottom: '0.5rem' }}>
              <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{edu.institution}</div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                {edu.degree}{edu.specialization ? ` — ${edu.specialization}` : ''}{edu.year ? `, ${edu.year}` : ''}{edu.period ? `, ${edu.period}` : ''}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Skills */}
      {parsed.skills && parsed.skills.length > 0 && (
        <div style={{ marginBottom: '1rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', color: 'var(--text-primary)' }}>
            <Wrench size={16} style={{ color: 'var(--primary)' }} /> НАВЫКИ
          </h3>
          <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
            {parsed.skills.map(s => (
              <span key={s} className="badge badge-indigo">{s}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

/** Render plain text with section heading detection */
function FormattedPlainText({ text }: { text: string }) {
  return (
    <div style={{ fontSize: '0.9rem', lineHeight: 1.7, color: 'var(--text-secondary)' }}>
      {text.split('\n').map((line, i) => {
        const trimmed = line.trim()
        if (!trimmed) return <br key={i} />
        const isHeading = trimmed.length > 2 && trimmed.length < 80 && (
          (trimmed === trimmed.toUpperCase() && /[А-ЯA-Z]/.test(trimmed)) ||
          /^(опыт|образование|навыки|проекты|сертификат|достижения|контакт|о себе|summary|experience|education|skills)/i.test(trimmed)
        )
        if (isHeading) return <div key={i} style={{ fontWeight: 700, color: 'var(--text)', marginTop: '0.75rem', marginBottom: '0.25rem', fontSize: '0.95rem' }}>{trimmed}</div>
        if (/^[-•●▪]/.test(trimmed)) return <div key={i} style={{ paddingLeft: '1rem' }}>{trimmed}</div>
        return <div key={i}>{line}</div>
      })}
    </div>
  )
}

export default function ResumeViewerModal({ resumeId, onClose }: ResumeViewerModalProps) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [preview, setPreview] = useState<any>(null)
  const [activeTab, setActiveTab] = useState<TabId>('original')
  const [downloading, setDownloading] = useState(false)
  // File viewer state
  const [fileUrl, setFileUrl] = useState<string | null>(null)
  const [docxHtml, setDocxHtml] = useState<string | null>(null)
  const [fileTab, setFileTab] = useState<'file' | 'text'>('file')

  const hasOptimization = preview?.rewrites?.length > 0
  const latestRewrite = hasOptimization ? preview.rewrites[0] : null
  const fmt = (preview?.format || '').toLowerCase()

  useEffect(() => {
    let blobUrl: string | null = null
    const load = async () => {
      try {
        const data = await api.getResumePreview(resumeId)
        setPreview(data)
        if (data.rewrites?.length > 0) {
          setActiveTab('optimized')
        }

        // Load file preview for PDF/DOCX
        const fileFmt = (data.format || '').toLowerCase()
        if (data.file_url && (fileFmt === 'pdf' || fileFmt === 'docx')) {
          try {
            const blob = await api.downloadResumeFile(resumeId)
            if (fileFmt === 'pdf') {
              blobUrl = URL.createObjectURL(blob)
              setFileUrl(blobUrl)
            } else if (fileFmt === 'docx') {
              const arrayBuffer = await blob.arrayBuffer()
              const result = await mammoth.convertToHtml({ arrayBuffer })
              setDocxHtml(DOMPurify.sanitize(result.value))
            }
          } catch { /* file preview not available, will show text fallback */ }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Ошибка загрузки данных')
      } finally {
        setLoading(false)
      }
    }
    load()
    return () => { if (blobUrl) URL.revokeObjectURL(blobUrl) }
  }, [resumeId])

  // Get optimized content — resolve JSON to structured data
  const optimizedData = useMemo(() => {
    if (!latestRewrite) return null
    if (latestRewrite.rewritten_data && typeof latestRewrite.rewritten_data === 'object') {
      return latestRewrite.rewritten_data
    }
    if (latestRewrite.optimized_text) {
      return tryParseJSON(latestRewrite.optimized_text)
    }
    return null
  }, [latestRewrite])

  const optimizedPlainText = useMemo(() => {
    if (!latestRewrite?.optimized_text) return ''
    const text = latestRewrite.optimized_text
    const parsed = tryParseJSON(text)
    if (parsed) return jsonToPlainText(parsed)
    if (optimizedData) return jsonToPlainText(optimizedData)
    return text
  }, [latestRewrite, optimizedData])

  const handleExport = async (format: string) => {
    if (!latestRewrite?.id) return
    setDownloading(true)
    try {
      let blob: Blob
      if (format === 'pdf') blob = await api.exportPdf(latestRewrite.id)
      else if (format === 'txt') blob = await api.exportTxt(latestRewrite.id)
      else blob = await api.exportDocx(latestRewrite.id)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${preview?.title || 'resume'}_optimized.${format}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Ошибка экспорта')
    } finally {
      setDownloading(false)
    }
  }

  const handleDownloadOriginal = async () => {
    setDownloading(true)
    try {
      const blob = await api.downloadResumeFile(resumeId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${preview?.title || 'resume'}.${preview?.format || 'bin'}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch {
      if (preview?.original_text) {
        const blob = new Blob([preview.original_text], { type: 'text/plain;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${preview?.title || 'resume'}.txt`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
      } else {
        alert('Файл недоступен')
      }
    } finally {
      setDownloading(false)
    }
  }

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  // Determine which tabs to show
  const tabs: { id: TabId; label: string; icon: typeof Eye }[] = []
  tabs.push({ id: 'original', label: 'Оригинал', icon: FileText })
  if (hasOptimization) {
    tabs.push({ id: 'optimized', label: 'Оптимизировано', icon: Eye })
    tabs.push({ id: 'comparison', label: 'Сравнение', icon: GitCompare })
  }

  return (
    <div
      style={{
        position: 'fixed', inset: 0, zIndex: 10000,
        background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(4px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: '1rem', animation: 'fadeIn 150ms ease-out',
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: 'var(--surface, #fff)', borderRadius: '1rem',
          maxWidth: 900, width: '100%', maxHeight: '90vh',
          display: 'flex', flexDirection: 'column',
          boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
          animation: 'slideUp 150ms ease-out',
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '1rem 1.5rem', borderBottom: '1px solid var(--border)',
          flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700, margin: 0 }}>
              Просмотр резюме
            </h2>
            {preview?.format && (
              <span className="badge badge-indigo">{preview.format.toUpperCase()}</span>
            )}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {hasOptimization && (
              <>
                <button className="btn btn-ghost btn-sm" onClick={() => handleExport('docx')} disabled={downloading}
                  title="Скачать DOCX" style={{ fontSize: '0.8rem' }}>
                  <Download size={14} /> DOCX
                </button>
                <button className="btn btn-ghost btn-sm" onClick={() => handleExport('pdf')} disabled={downloading}
                  title="Скачать PDF" style={{ fontSize: '0.8rem' }}>
                  <Download size={14} /> PDF
                </button>
                <button className="btn btn-ghost btn-sm" onClick={() => handleExport('txt')} disabled={downloading}
                  title="Скачать TXT" style={{ fontSize: '0.8rem' }}>
                  <Download size={14} /> TXT
                </button>
              </>
            )}
            <button onClick={onClose}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', padding: '0.25rem' }}
              aria-label="Закрыть">
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div style={{
          display: 'flex', gap: 0, borderBottom: '1px solid var(--border)',
          padding: '0 1.5rem', flexShrink: 0,
        }}>
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: '0.75rem 1rem',
                border: 'none', background: 'none', cursor: 'pointer',
                fontSize: '0.85rem', fontWeight: activeTab === tab.id ? 600 : 400,
                color: activeTab === tab.id ? 'var(--primary)' : 'var(--text-secondary)',
                borderBottom: activeTab === tab.id ? '2px solid var(--primary)' : '2px solid transparent',
                display: 'flex', alignItems: 'center', gap: '0.35rem',
                transition: 'all 150ms',
              }}
            >
              <tab.icon size={15} /> {tab.label}
            </button>
          ))}
          {/* File viewer tabs for PDF/DOCX */}
          {activeTab === 'original' && (fileUrl || docxHtml) && (
            <div style={{ marginLeft: 'auto', display: 'flex', gap: 0 }}>
              <button onClick={() => setFileTab('file')}
                style={{
                  padding: '0.75rem 0.75rem', border: 'none', background: 'none', cursor: 'pointer',
                  fontSize: '0.8rem', fontWeight: fileTab === 'file' ? 600 : 400,
                  color: fileTab === 'file' ? 'var(--primary)' : 'var(--text-tertiary)',
                  borderBottom: fileTab === 'file' ? '2px solid var(--primary)' : '2px solid transparent',
                }}>
                Файл {fmt.toUpperCase()}
              </button>
              <button onClick={() => setFileTab('text')}
                style={{
                  padding: '0.75rem 0.75rem', border: 'none', background: 'none', cursor: 'pointer',
                  fontSize: '0.8rem', fontWeight: fileTab === 'text' ? 600 : 400,
                  color: fileTab === 'text' ? 'var(--primary)' : 'var(--text-tertiary)',
                  borderBottom: fileTab === 'text' ? '2px solid var(--primary)' : '2px solid transparent',
                }}>
                Текст
              </button>
            </div>
          )}
        </div>

        {/* Content */}
        <div style={{ flex: 1, overflow: 'auto', padding: '1.5rem' }}>
          {loading ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '30vh', gap: '0.75rem', color: 'var(--text-secondary)' }}>
              <Loader size={20} className="spin" /> Загрузка...
            </div>
          ) : error ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '30vh', gap: '0.75rem' }}>
              <AlertCircle size={28} style={{ color: 'var(--error)' }} />
              <p style={{ color: 'var(--text-secondary)' }}>{error}</p>
            </div>
          ) : (
            <>
              {/* Tab: Original */}
              {activeTab === 'original' && (
                <div>
                  {/* File viewer for PDF */}
                  {fileUrl && fileTab === 'file' && (
                    <iframe src={fileUrl} title="PDF" style={{ width: '100%', height: '65vh', border: 'none', borderRadius: 8 }} />
                  )}
                  {/* File viewer for DOCX */}
                  {docxHtml && fileTab === 'file' && (
                    <div
                      style={{ padding: '1rem', fontSize: '0.9rem', lineHeight: 1.7, maxHeight: '65vh', overflowY: 'auto' }}
                      dangerouslySetInnerHTML={{ __html: docxHtml }}
                    />
                  )}
                  {/* Text view (default if no file, or second sub-tab) */}
                  {((!fileUrl && !docxHtml) || fileTab === 'text') && (
                    preview?.original_text ? (
                      <FormattedPlainText text={preview.original_text} />
                    ) : (
                      <div style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '3rem' }}>
                        <FileText size={32} style={{ opacity: 0.3, marginBottom: '0.5rem' }} />
                        <p>Текст оригинала недоступен</p>
                        {preview?.file_url && (
                          <button onClick={handleDownloadOriginal} className="btn btn-secondary btn-sm" style={{ marginTop: '0.75rem' }}>
                            <Download size={14} /> Скачать файл
                          </button>
                        )}
                      </div>
                    )
                  )}
                </div>
              )}

              {/* Tab: Optimized */}
              {activeTab === 'optimized' && latestRewrite && (
                <div>
                  {optimizedData ? (
                    <FormattedResume data={optimizedData} />
                  ) : latestRewrite.optimized_text ? (
                    <FormattedPlainText text={latestRewrite.optimized_text} />
                  ) : (
                    <div style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '3rem' }}>
                      Оптимизированный текст недоступен
                    </div>
                  )}
                </div>
              )}

              {/* Tab: Comparison */}
              {activeTab === 'comparison' && latestRewrite && (
                <div className="diff-container" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div style={{ border: '1px solid var(--border)', borderRadius: 8, overflow: 'hidden' }}>
                    <div style={{
                      padding: '0.75rem 1rem', background: '#FEF2F2',
                      borderBottom: '1px solid var(--border)', fontWeight: 600, fontSize: '0.85rem',
                      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    }}>
                      <span>Оригинал</span>
                    </div>
                    <div style={{ padding: '1rem', fontSize: '0.85rem', lineHeight: 1.7, maxHeight: '60vh', overflowY: 'auto' }}>
                      {(() => {
                        const origText = latestRewrite.original_text || preview?.original_text || ''
                        const optText = optimizedPlainText || ''
                        if (origText && optText) {
                          return computeWordDiff(origText, optText).origTokens.map((t, i) =>
                            t.removed ? (
                              <span key={i} style={{ background: 'rgba(239,68,68,0.15)', borderRadius: 2, padding: '0 1px', textDecoration: 'line-through', textDecorationColor: 'rgba(239,68,68,0.5)' }}>{t.text}</span>
                            ) : <span key={i}>{t.text}</span>
                          )
                        }
                        return <span style={{ whiteSpace: 'pre-wrap' }}>{origText || 'Текст недоступен'}</span>
                      })()}
                    </div>
                  </div>
                  <div style={{ border: '1px solid var(--border)', borderRadius: 8, overflow: 'hidden' }}>
                    <div style={{
                      padding: '0.75rem 1rem', background: '#F0FDF4',
                      borderBottom: '1px solid var(--border)', fontWeight: 600, fontSize: '0.85rem',
                      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    }}>
                      <span>Оптимизировано</span>
                    </div>
                    <div style={{ padding: '1rem', fontSize: '0.85rem', lineHeight: 1.7, maxHeight: '60vh', overflowY: 'auto' }}>
                      {(() => {
                        const origText = latestRewrite.original_text || preview?.original_text || ''
                        const optText = optimizedPlainText || ''
                        if (origText && optText) {
                          return computeWordDiff(origText, optText).newTokens.map((t, i) =>
                            t.added ? (
                              <span key={i} style={{ background: 'rgba(16,185,129,0.15)', borderRadius: 2, padding: '0 1px' }}>{t.text}</span>
                            ) : <span key={i}>{t.text}</span>
                          )
                        }
                        return <span style={{ whiteSpace: 'pre-wrap' }}>{optText || 'Текст недоступен'}</span>
                      })()}
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer — match score & ATS info */}
        {latestRewrite && (
          <div style={{
            padding: '0.75rem 1.5rem', borderTop: '1px solid var(--border)',
            display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap',
            fontSize: '0.85rem', color: 'var(--text-secondary)', flexShrink: 0,
          }}>
            {latestRewrite.match_score != null && (
              <span>Match Score: <strong style={{ color: 'var(--success)' }}>{Math.round(latestRewrite.match_score)}%</strong></span>
            )}
            {latestRewrite.ats_grade && (
              <span>ATS: <strong style={{ color: 'var(--success)' }}>{latestRewrite.ats_grade}</strong></span>
            )}
            {latestRewrite.model && (
              <span>Модель: <strong>{latestRewrite.model}</strong></span>
            )}
            {latestRewrite.created_at && (
              <span style={{ marginLeft: 'auto' }}>{new Date(latestRewrite.created_at).toLocaleDateString('ru-RU')}</span>
            )}
          </div>
        )}
      </div>

      <style>{`
        @keyframes fadeIn { from { opacity: 0 } to { opacity: 1 } }
        @keyframes slideUp { from { opacity: 0; transform: translateY(16px) } to { opacity: 1; transform: translateY(0) } }
      `}</style>
    </div>
  )
}

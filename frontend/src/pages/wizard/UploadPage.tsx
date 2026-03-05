import { Link, useNavigate } from 'react-router-dom'
import { Upload, FileText, ArrowLeft, AlertCircle, Link2, ClipboardPaste } from 'lucide-react'
import { useState, useCallback } from 'react'
import { api } from '../../services/api'
import { useWizard } from '../../contexts/WizardContext'

const ALLOWED_EXT = ['pdf', 'docx']
const MAX_SIZE = 10 * 1024 * 1024

export default function UploadPage() {
  const navigate = useNavigate()
  const { setFile: setWizardFile, setResumeId } = useWizard()
  const [tab, setTab] = useState(0)
  const [dragActive, setDragActive] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // hh.ru URL state
  const [hhUrl, setHhUrl] = useState('')

  // Paste text state
  const [pasteText, setPasteText] = useState('')
  const [pasteTitle, setPasteTitle] = useState('')

  const validateFile = (f: File): string | null => {
    const ext = f.name.split('.').pop()?.toLowerCase() || ''
    if (!ALLOWED_EXT.includes(ext)) return `Неподдерживаемый формат .${ext}. Используйте PDF или DOCX.`
    if (f.size > MAX_SIZE) return `Файл слишком большой (${(f.size / 1024 / 1024).toFixed(1)} МБ). Максимум 10 МБ.`
    return null
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
    setError(null)
    const f = e.dataTransfer.files[0]
    if (f) {
      const err = validateFile(f)
      if (err) { setError(err); return }
      setFile(f)
    }
  }, [])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null)
    const f = e.target.files?.[0]
    if (f) {
      const err = validateFile(f)
      if (err) { setError(err); return }
      setFile(f)
    }
  }

  const handleUploadFile = async () => {
    if (!file) return
    setUploading(true)
    setError(null)
    try {
      const res = await api.uploadResume(file)
      setWizardFile(file)
      setResumeId(res.id)
      navigate('/app/vacancy')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка загрузки файла')
    } finally {
      setUploading(false)
    }
  }

  const handlePasteText = async () => {
    if (pasteText.trim().length < 50) {
      setError('Текст слишком короткий. Вставьте полный текст резюме (минимум 50 символов).')
      return
    }
    setUploading(true)
    setError(null)
    try {
      const res = await api.createResumeFromText({
        text: pasteText.trim(),
        title: pasteTitle.trim() || undefined,
        // Only include source_url if user is on Tab 2 AND manually entered something in the title field
        // Completely independent of hh.ru URL tab
      })
      setResumeId(res.id)
      navigate('/app/vacancy')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка создания резюме')
    } finally {
      setUploading(false)
    }
  }

  const handleHhUrlParse = async () => {
    if (!hhUrl.trim()) return
    setUploading(true)
    setError(null)
    try {
      // Try to create resume from hh.ru URL via backend
      const res = await api.createResumeFromText({
        text: '', // Backend will try to parse from URL
        title: 'Резюме с hh.ru',
        source_url: hhUrl.trim(),
      })
      setResumeId(res.id)
      navigate('/app/vacancy')
    } catch {
      // If backend can't parse, guide user to paste text manually
      setError('Не удалось автоматически загрузить резюме с hh.ru. Скопируйте текст резюме вручную на вкладке «Вставить текст».')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="wizard-container">
      <Link to="/app/dashboard" className="btn btn-secondary btn-sm" style={{ marginBottom: '1.5rem' }}>
        <ArrowLeft size={16} /> Назад
      </Link>

      <h2 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.5rem' }}>Загрузите ваше резюме</h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>PDF или DOCX файл, ссылка hh.ru, или вставьте текст</p>

      {/* Tabs */}
      <div className="tab-bar" style={{ marginBottom: '1.5rem' }}>
        {['Загрузить файл', 'Ссылка hh.ru', 'Вставить текст'].map((label, i) => (
          <div key={i} className={`tab-bar-item${tab === i ? ' active' : ''}`} onClick={() => { setTab(i); setError(null) }}>
            {i === 0 && <Upload size={14} style={{ marginRight: 4 }} />}
            {i === 1 && <Link2 size={14} style={{ marginRight: 4 }} />}
            {i === 2 && <ClipboardPaste size={14} style={{ marginRight: 4 }} />}
            {label}
          </div>
        ))}
      </div>

      {/* Tab 0: File upload */}
      {tab === 0 && (
        <>
          <div
            className={`dropzone${dragActive ? ' active' : ''}`}
            style={dragActive ? { borderColor: 'var(--primary)', background: 'var(--primary-light)' } : {}}
            onDragOver={e => { e.preventDefault(); setDragActive(true) }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
            onClick={() => document.getElementById('file-input')?.click()}
          >
            <div style={{
              width: 64, height: 64, borderRadius: 16, background: '#F3F4F6',
              display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem',
              color: 'var(--text-secondary)'
            }}>
              <Upload size={28} />
            </div>
            {file ? (
              <>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.5rem' }}>{file.name}</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{(file.size / 1024).toFixed(0)} КБ</p>
              </>
            ) : (
              <>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.5rem' }}>Перетащите файл сюда</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1rem' }}>или нажмите для выбора файла</p>
                <span className="btn btn-secondary">Выбрать файл</span>
              </>
            )}
            <input id="file-input" type="file" accept=".pdf,.docx" onChange={handleFileChange} style={{ display: 'none' }} />
          </div>

          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', marginTop: '1rem', color: 'var(--text-tertiary)', fontSize: '0.85rem' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}><FileText size={14} /> PDF</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}><FileText size={14} /> DOCX</span>
            <span>до 10 МБ</span>
          </div>

          {file && (
            <button onClick={handleUploadFile} className="btn btn-primary btn-block" style={{ marginTop: '2rem' }} disabled={uploading}>
              {uploading ? 'Загрузка на сервер...' : 'Продолжить'}
            </button>
          )}
        </>
      )}

      {/* Tab 1: hh.ru URL */}
      {tab === 1 && (
        <div className="card" style={{ padding: '1.5rem' }}>
          <div style={{
            background: '#F0F9FF', border: '1px solid #BAE6FD', borderRadius: 12,
            padding: '1rem 1.25rem', marginBottom: '1.5rem', fontSize: '0.9rem', color: '#0369A1', lineHeight: 1.6
          }}>
            <strong>Импорт резюме с hh.ru:</strong>
            <p style={{ margin: '0.5rem 0 0' }}>Вставьте ссылку на ваше резюме для автоматического парсинга. Если автоматический парсинг не удастся, вы можете скопировать текст резюме вручную на вкладке «Вставить текст».</p>
          </div>

          <div className="input-group" style={{ marginBottom: '1rem' }}>
            <label className="input-label">Ссылка на резюме hh.ru</label>
            <input className="input-field" placeholder="https://hh.ru/resume/abc123def4" value={hhUrl} onChange={e => setHhUrl(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleHhUrlParse()} />
          </div>

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button onClick={handleHhUrlParse} className="btn btn-primary" disabled={uploading || !hhUrl.trim()}>
              {uploading ? 'Загрузка...' : 'Загрузить резюме'}
            </button>
            <button onClick={() => { setTab(2); setError(null) }} className="btn btn-secondary">
              <ClipboardPaste size={16} /> Вставить текст вручную
            </button>
          </div>
        </div>
      )}

      {/* Tab 2: Paste text */}
      {tab === 2 && (
        <div className="card" style={{ padding: '1.5rem' }}>
          <div className="input-group" style={{ marginBottom: '1rem' }}>
            <label className="input-label">Название (необязательно)</label>
            <input className="input-field" placeholder="Продакт-менеджер, Senior Developer..." value={pasteTitle} onChange={e => setPasteTitle(e.target.value)} />
          </div>
          <div className="input-group" style={{ marginBottom: '1rem' }}>
            <label className="input-label">Текст резюме *</label>
            <textarea
              className="input-field"
              rows={12}
              placeholder="Вставьте текст резюме сюда...&#10;&#10;Скопируйте текст со страницы hh.ru или из любого другого источника.&#10;Минимум 50 символов."
              value={pasteText}
              onChange={e => setPasteText(e.target.value)}
              style={{ fontFamily: 'inherit', lineHeight: 1.6 }}
            />
            <div style={{ textAlign: 'right', fontSize: '0.8rem', color: pasteText.length < 50 ? 'var(--text-tertiary)' : 'var(--success)', marginTop: '0.25rem' }}>
              {pasteText.length} символов {pasteText.length < 50 ? '(минимум 50)' : '✓'}
            </div>
          </div>
          <button onClick={handlePasteText} className="btn btn-primary btn-block" disabled={uploading || pasteText.trim().length < 50}>
            {uploading ? 'Создание...' : 'Продолжить'}
          </button>
        </div>
      )}

      {error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '1rem', padding: '0.75rem 1rem', borderRadius: 8, background: 'var(--danger-light, #FEF2F2)', color: 'var(--danger, #EF4444)', fontSize: '0.9rem' }}>
          <AlertCircle size={16} /> {error}
        </div>
      )}
    </div>
  )
}

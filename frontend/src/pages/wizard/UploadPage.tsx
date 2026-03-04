import { Link, useNavigate } from 'react-router-dom'
import { Upload, FileText, ArrowLeft } from 'lucide-react'
import { useState, useCallback } from 'react'

export default function UploadPage() {
  const navigate = useNavigate()
  const [dragActive, setDragActive] = useState(false)
  const [file, setFile] = useState<File | null>(null)

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
    const f = e.dataTransfer.files[0]
    if (f) setFile(f)
  }, [])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (f) setFile(f)
  }

  const handleContinue = () => {
    navigate('/app/vacancy')
  }

  return (
    <div className="wizard-container">
      <Link to="/app/dashboard" className="btn btn-secondary btn-sm" style={{ marginBottom: '1.5rem' }}>
        <ArrowLeft size={16} /> Назад
      </Link>

      <h2 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.5rem' }}>Загрузите ваше резюме</h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>Мы поддерживаем форматы PDF и DOCX до 10 МБ</p>

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
        <button onClick={handleContinue} className="btn btn-primary btn-block" style={{ marginTop: '2rem' }}>
          Продолжить
        </button>
      )}
    </div>
  )
}

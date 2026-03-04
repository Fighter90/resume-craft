import { useEffect, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Loader, FileText, Search, Sparkles, CheckCircle, AlertCircle } from 'lucide-react'
import { api } from '../../services/api'
import { useWizard } from '../../contexts/WizardContext'

/* eslint-disable @typescript-eslint/no-explicit-any */

const STEPS = [
  { icon: FileText, label: 'Загрузка документа', desc: 'Парсинг и извлечение текста' },
  { icon: Search, label: 'Анализ вакансии', desc: 'Определение требований и ключевых слов' },
  { icon: Sparkles, label: 'AI оптимизация', desc: 'Генерация улучшенного текста резюме' },
  { icon: CheckCircle, label: 'Финализация', desc: 'Скоринг, проверка качества, ATS-рейтинг' },
]

const STEP_MAP: Record<string, number> = {
  'extracting': 0, 'parsing': 0,
  'analyzing': 1, 'matching': 1,
  'rewriting': 2, 'optimizing': 2, 'generating': 2,
  'scoring': 3, 'finalizing': 3, 'validating': 3,
}

export default function ProcessingPage() {
  const navigate = useNavigate()
  const { taskId, setResult } = useWizard()
  const [current, setCurrent] = useState(0)
  const [progress, setProgress] = useState(0)
  const [done, setDone] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (!taskId) {
      setError('Нет задачи для отслеживания. Вернитесь к выбору модели.')
      return
    }

    const poll = async () => {
      try {
        const status = await api.getRewriteStatus(taskId) as any
        // Update progress and step
        if (status.progress !== undefined) {
          setProgress(Math.min(status.progress, 100))
        }
        if (status.step) {
          const stepIdx = STEP_MAP[status.step.toLowerCase()] ?? current
          setCurrent(stepIdx)
        }
        // Check if done
        if (status.status === 'completed') {
          setProgress(100)
          setCurrent(3)
          if (pollingRef.current) clearInterval(pollingRef.current)
          // Fetch result
          try {
            const result = await api.getRewriteResult(taskId) as any
            setResult(result)
          } catch { /* result will be fetched on results page */ }
          setDone(true)
        } else if (status.status === 'failed') {
          if (pollingRef.current) clearInterval(pollingRef.current)
          setError(status.error_message || 'Ошибка обработки')
        }
      } catch (err) {
        // Don't stop on transient errors, keep polling
        console.warn('Polling error:', err)
      }
    }

    poll() // initial call
    pollingRef.current = setInterval(poll, 3000)
    return () => { if (pollingRef.current) clearInterval(pollingRef.current) }
  }, [taskId]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', padding: '2rem', textAlign: 'center' }}>
      {/* Spinner */}
      <div style={{ position: 'relative', marginBottom: '2rem' }}>
        <div className="processing-spinner">
          <Loader size={48} className="spinning" style={{ color: 'var(--primary)' }} />
        </div>
      </div>

      <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>
        {error ? 'Ошибка обработки' : done ? 'Оптимизация завершена!' : 'Оптимизируем ваше резюме...'}
      </h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>
        {error ? '' : done ? 'Ваше резюме готово к просмотру' : 'AI анализирует и улучшает ваше резюме · Обычно 10–30 секунд'}
      </p>

      {error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--error)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
          <AlertCircle size={18} /> {error}
        </div>
      )}

      {/* Progress bar */}
      <div style={{ width: '100%', maxWidth: 400, marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.5rem' }}>
          <span>{progress}%</span>
          <span>~{Math.max(0, Math.round((100 - progress) * 0.15))} сек</span>
        </div>
        <div className="progress-bar" style={{ height: 8 }}>
          <div className="progress-fill" style={{ width: `${progress}%`, transition: 'width 0.1s linear' }} />
        </div>
      </div>

      {/* Steps */}
      <div style={{ width: '100%', maxWidth: 400 }}>
        {STEPS.map((s, i) => {
          const Icon = s.icon
          const done = i < current
          const active = i === current
          return (
            <div key={i} style={{
              display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.75rem',
              borderRadius: 'var(--radius-sm)',
              opacity: done || active ? 1 : 0.4,
              background: active ? 'var(--primary-bg)' : 'transparent',
              transition: 'all 0.3s',
            }}>
              <Icon size={20} style={{ color: done ? 'var(--success)' : active ? 'var(--primary)' : 'var(--text-secondary)' }} />
              <div style={{ textAlign: 'left' }}>
                <div style={{ fontSize: '0.9rem', fontWeight: 600, color: done ? 'var(--success)' : undefined }}>{s.label}</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>{s.desc}</div>
              </div>
              {done && <CheckCircle size={16} style={{ marginLeft: 'auto', color: 'var(--success)' }} />}
            </div>
          )
        })}
      </div>

      {done && (
        <button onClick={() => navigate('/app/results')} className="btn btn-primary" style={{ marginTop: '2rem' }}>
          Посмотреть результат
        </button>
      )}
    </div>
  )
}

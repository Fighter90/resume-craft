import { useEffect, useState, useRef } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Loader, FileText, Search, Sparkles, CheckCircle, AlertCircle, RotateCcw, Settings } from 'lucide-react'
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

function isAuthError(msg: string): boolean {
  const lower = msg.toLowerCase()
  return lower.includes('api-ключ') || lower.includes('не настроен') || lower.includes('unauthorized') || lower.includes('auth') || lower.includes('провайдер all') || lower.includes('provider all') || lower.includes('unavailable')
}

function friendlyError(msg: string): string {
  if (/провайдер all|provider all|unavailable/i.test(msg)) {
    return 'Ни один LLM-провайдер не настроен. Перейдите в настройки AI и добавьте API-ключ хотя бы для одного провайдера (OpenAI, Anthropic, OpenRouter или GigaChat).'
  }
  if (/payment|402|billing/i.test(msg)) {
    return 'Ошибка тарификации у поставщика модели. Проверьте баланс аккаунта или выберите другую модель.'
  }
  return msg
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
        if (status.progress !== undefined) {
          setProgress(Math.min(status.progress, 100))
        }
        if (status.step) {
          const stepIdx = STEP_MAP[status.step.toLowerCase()] ?? current
          setCurrent(stepIdx)
        }
        if (status.status === 'completed') {
          setProgress(100)
          setCurrent(3)
          if (pollingRef.current) clearInterval(pollingRef.current)
          try {
            const result = await api.getRewriteResult(taskId) as any
            setResult(result)
          } catch { /* result will be fetched on results page */ }
          setDone(true)
        } else if (status.status === 'failed') {
          if (pollingRef.current) clearInterval(pollingRef.current)
          setError(status.error_message || 'Ошибка обработки. Попробуйте выбрать другую модель.')
        }
      } catch (err) {
        console.warn('Polling error:', err)
      }
    }

    poll()
    pollingRef.current = setInterval(poll, 3000)
    return () => { if (pollingRef.current) clearInterval(pollingRef.current) }
  }, [taskId]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', padding: '2rem', textAlign: 'center' }}>
      {/* Spinner */}
      {!error && !done && (
        <div style={{ position: 'relative', marginBottom: '2rem' }}>
          <div className="processing-spinner">
            <Loader size={48} className="spinning" style={{ color: 'var(--primary)' }} />
          </div>
        </div>
      )}

      <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>
        {error ? 'Ошибка обработки' : done ? 'Оптимизация завершена!' : 'Оптимизируем ваше резюме...'}
      </h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>
        {error ? '' : done ? 'Ваше резюме готово к просмотру' : 'AI анализирует и улучшает ваше резюме · Обычно 10–30 секунд'}
      </p>

      {error && (
        <div style={{
          maxWidth: 500, width: '100%', marginBottom: '1.5rem', padding: '1.25rem',
          borderRadius: 12, background: '#FEF2F2', border: '1px solid #FECACA',
          textAlign: 'left',
        }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem', marginBottom: '0.75rem' }}>
            <AlertCircle size={20} color="#DC2626" style={{ flexShrink: 0, marginTop: 1 }} />
            <span style={{ color: '#991B1B', fontWeight: 600, fontSize: '0.95rem' }}>
              {isAuthError(error) ? 'API-ключ не настроен' : 'Произошла ошибка'}
            </span>
          </div>
          <p style={{ color: '#7F1D1D', fontSize: '0.875rem', margin: '0 0 1rem', lineHeight: 1.5 }}>
            {friendlyError(error)}
          </p>
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <button onClick={() => navigate('/app/models')} className="btn btn-primary btn-sm">
              <RotateCcw size={14} /> Выбрать другую модель
            </button>
            <Link to="/app/settings/ai" className="btn btn-secondary btn-sm">
              <Settings size={14} /> Настроить ключи
            </Link>
          </div>
        </div>
      )}

      {/* Progress bar */}
      {!error && (
        <div style={{ width: '100%', maxWidth: 400, marginBottom: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.5rem' }}>
            <span>{progress}%</span>
            <span>~{Math.max(0, Math.round((100 - progress) * 0.15))} сек</span>
          </div>
          <div className="progress-bar" style={{ height: 8 }}>
            <div className="progress-fill" style={{ width: `${progress}%`, transition: 'width 0.1s linear' }} />
          </div>
        </div>
      )}

      {/* Steps */}
      {!error && (
        <div style={{ width: '100%', maxWidth: 400 }}>
          {STEPS.map((s, i) => {
            const Icon = s.icon
            const stepDone = i < current
            const active = i === current
            return (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.75rem',
                borderRadius: 'var(--radius-sm)',
                opacity: stepDone || active ? 1 : 0.4,
                background: active ? 'var(--primary-bg)' : 'transparent',
                transition: 'all 0.3s',
              }}>
                <Icon size={20} style={{ color: stepDone ? 'var(--success)' : active ? 'var(--primary)' : 'var(--text-secondary)' }} />
                <div style={{ textAlign: 'left' }}>
                  <div style={{ fontSize: '0.9rem', fontWeight: 600, color: stepDone ? 'var(--success)' : undefined }}>{s.label}</div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>{s.desc}</div>
                </div>
                {stepDone && <CheckCircle size={16} style={{ marginLeft: 'auto', color: 'var(--success)' }} />}
              </div>
            )
          })}
        </div>
      )}

      {done && (
        <button onClick={() => navigate('/app/results')} className="btn btn-primary" style={{ marginTop: '2rem' }}>
          Посмотреть результат
        </button>
      )}
    </div>
  )
}

import { Clock, FileText, Loader, ExternalLink } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../../services/api'

/* eslint-disable @typescript-eslint/no-explicit-any */

/** HISTORY-RAW-ERROR-001: strip raw URLs, HTTP codes, JSON from error messages */
function sanitizeErrorMessage(msg: string): string {
  if (/api-ключ.*не настроен/i.test(msg)) return msg.split('.')[0]
  if (/провайдер all|provider all/i.test(msg)) return 'Нет доступных AI-провайдеров'
  if (/URL\(|https?:\/\/|{.*error.*}|status_code|b'|\\x/i.test(msg)) return 'Ошибка AI-провайдера'
  if (/max_tokens|max_completion_tokens|unsupported parameter/i.test(msg)) return 'Ошибка параметров запроса'
  if (/недостаточно средств|billing|quota/i.test(msg)) return 'Недостаточно средств у провайдера'
  if (/rate.?limit|429|too many/i.test(msg)) return 'Превышен лимит запросов'
  if (/временно недоступен/i.test(msg)) return 'AI-провайдер временно недоступен'
  if (msg.length > 80) return msg.slice(0, 77) + '...'
  return msg
}

function titleCaseFromToken(token: string): string {
  return token
    .split(/[-_\s]+/)
    .filter(Boolean)
    .map(part => part[0].toUpperCase() + part.slice(1))
    .join(' ')
}

function formatModelLabel(rawModelName: unknown): string {
  if (typeof rawModelName !== 'string' || !rawModelName.trim()) {
    return 'AI'
  }

  const model = rawModelName.trim()
  const [rawProvider, ...rest] = model.split(':')
  const providerKey = rawProvider.toLowerCase()
  const providerMap: Record<string, string> = {
    gigachat: 'GigaChat',
    'gigachat-pro': 'GigaChat',
    openai: 'OpenAI',
    anthropic: 'Anthropic',
    openrouter: 'OpenRouter',
    groq: 'Groq',
  }

  const provider = providerMap[providerKey] ?? titleCaseFromToken(rawProvider)
  const modelPart = rest.join(':').trim()
  if (!modelPart) {
    if (providerKey === 'gigachat-pro') {
      return 'GigaChat · GigaChat-Pro'
    }
    return provider
  }

  return `${provider} · ${modelPart}`
}

export default function HistoryPage() {
  const navigate = useNavigate()
  const [history, setHistory] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.getRewriteHistory()
        setHistory(Array.isArray(res) ? res : [])
      } catch { /* empty */ }
      finally { setLoading(false) }
    }
    load()
  }, [])

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>История оптимизаций</h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Все ваши оптимизации резюме</p>
        </div>
      </div>

      {loading ? (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', padding: '3rem', color: 'var(--text-secondary)' }}>
          <Loader size={16} className="spin" /> Загрузка...
        </div>
      ) : history.length === 0 ? (
        <div className="card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
          Нет истории оптимизаций
        </div>
      ) : (
        <div className="timeline" style={{ position: 'relative' }}>
          <div style={{ position: 'absolute', left: '1.85rem', top: 0, bottom: 0, width: 2, background: 'var(--border)', zIndex: 0 }} />
          {history.map((item: any, i: number) => (
            <div key={item.id || i} onClick={() => item.status === 'completed' && item.id ? navigate(`/app/results/${item.id}`) : undefined} style={{ display: 'flex', gap: '0.85rem', alignItems: 'flex-start', padding: '0.85rem 1rem', marginBottom: '0.5rem', borderRadius: 'var(--radius-sm)', background: 'var(--card-bg)', border: '1px solid var(--border)', position: 'relative', zIndex: 1, cursor: item.status === 'completed' ? 'pointer' : 'default', transition: 'box-shadow 0.15s' }}
              onMouseEnter={e => { if (item.status === 'completed') e.currentTarget.style.boxShadow = '0 2px 8px rgba(86,90,221,0.12)' }}
              onMouseLeave={e => { e.currentTarget.style.boxShadow = 'none' }}
            >
              <div style={{ width: 36, height: 36, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(86,90,221,0.1)', flexShrink: 0 }}>
                <FileText size={16} style={{ color: 'var(--primary)' }} />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>
                  Оптимизация · {formatModelLabel(item.model_name)}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  {item.status === 'completed' ? (
                    <>Match: {Math.round((item.match_score_before || 0) <= 1 ? (item.match_score_before || 0) * 100 : (item.match_score_before || 0))}% → {Math.round((item.match_score_after || 0) <= 1 ? (item.match_score_after || 0) * 100 : (item.match_score_after || 0))}% · ATS: {item.ats_rating || '—'}</>
                  ) : item.status === 'failed' ? (
                    <span style={{ color: 'var(--error)' }}>⚠️ {sanitizeErrorMessage(item.error_message || 'Неизвестная ошибка')}</span>
                  ) : (
                    <span>Статус: {item.status}</span>
                  )}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                  <Clock size={12} style={{ verticalAlign: '-1px', marginRight: '0.2rem' }} />
                  {item.created_at ? new Date(item.created_at).toLocaleDateString('ru-RU') : '—'}
                </span>
                {item.status === 'completed' && item.id && (
                  <button
                    onClick={() => navigate(`/app/results/${item.id}`)}
                    className="btn btn-secondary btn-sm"
                    style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
                  >
                    <ExternalLink size={12} /> Открыть
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

import { Clock, FileText, Download, Upload, UserCircle, ExternalLink } from 'lucide-react'
import { Link } from 'react-router-dom'
import { DEMO_HISTORY } from '../../data/demo'

const TYPE_MAP: Record<string, { icon: typeof FileText; color: string; link: string }> = {
  optimization: { icon: FileText, color: 'var(--primary)', link: '/app/results/1' },
  upload: { icon: Upload, color: 'var(--success)', link: '/app/resumes' },
  export: { icon: Download, color: 'var(--info)', link: '/app/export' },
  account: { icon: UserCircle, color: 'var(--warning)', link: '/app/settings/profile' },
}

export default function HistoryPage() {
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>История оптимизаций</h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Все действия с вашим аккаунтом</p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <select className="input-field select-field" style={{ width: 160 }}>
            <option>Все типы</option><option>Оптимизации</option><option>Загрузки</option><option>Экспорт</option>
          </select>
        </div>
      </div>

      <div className="timeline" style={{ position: 'relative' }}>
        {/* Vertical timeline line */}
        <div style={{ position: 'absolute', left: '1.85rem', top: 0, bottom: 0, width: 2, background: 'var(--border)', zIndex: 0 }} />
        {DEMO_HISTORY.map(group => (
          <div key={group.date} style={{ marginBottom: '2rem', position: 'relative', zIndex: 1 }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '1rem', paddingLeft: '2rem' }}>
              <Clock size={13} style={{ marginRight: '0.35rem', verticalAlign: '-2px' }} />
              {group.date}
            </div>
            {group.items.map((item, i) => {
              const { icon: Icon, color, link } = TYPE_MAP[item.type] || TYPE_MAP.account
              return (
                <Link key={i} to={link} className="session-item" style={{ display: 'flex', gap: '0.85rem', alignItems: 'flex-start', padding: '0.85rem 1rem', marginBottom: '0.5rem', borderRadius: 'var(--radius-sm)', background: 'var(--card-bg)', border: '1px solid var(--border)', textDecoration: 'none', color: 'inherit', cursor: 'pointer' }}>
                  <div style={{ width: 36, height: 36, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: `${color}18`, flexShrink: 0 }}>
                    <Icon size={16} style={{ color }} />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{item.title}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{item.desc}</div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>{item.time}</span>
                    <ExternalLink size={14} style={{ color: 'var(--text-tertiary)', flexShrink: 0 }} />
                  </div>
                </Link>
              )
            })}
          </div>
        ))}
      </div>
    </div>
  )
}

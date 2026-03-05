import { Link } from 'react-router-dom'
import { ArrowLeft, Mail, MapPin, MessageCircle, FileText } from 'lucide-react'

export default function AboutPage() {
  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '2rem 1rem' }}>
      <Link to="/" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '2rem', textDecoration: 'none' }}>
        <ArrowLeft size={16} /> На главную
      </Link>

      <h1 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '0.5rem' }}>О сервисе ResumeCraft</h1>
      <p style={{ color: 'var(--text-secondary)', fontSize: '1.05rem', marginBottom: '2rem' }}>
        AI-реврайтер резюме для российского рынка труда
      </p>

      <div style={{ lineHeight: 1.8, color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', margin: '1.5rem 0 0.75rem' }}>Наша миссия</h2>
        <p>
          Помочь каждому соискателю представить профессиональный опыт максимально выгодно, повысив шансы на
          приглашение на собеседование. ResumeCraft устраняет барьер между реальными компетенциями кандидата
          и формальными требованиями ATS-фильтров, которые отсеивают до 75% потенциально подходящих резюме.
        </p>

        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', margin: '1.5rem 0 0.75rem' }}>Что мы делаем</h2>
        <ul style={{ paddingLeft: '1.5rem' }}>
          <li>Единственная интеграция с hh.ru API — автоматический анализ требований вакансий</li>
          <li>Мультимодельный AI — GigaChat Pro, OpenAI, Anthropic Claude, OpenRouter для лучшего качества</li>
          <li>Match Score — объективная оценка соответствия резюме вакансии</li>
          <li>ATS-оптимизация — рейтинг от A+ до D</li>
          <li>Соответствие ФЗ-152 — данные хранятся в России</li>
        </ul>

        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', margin: '1.5rem 0 0.75rem' }}>Технологии</h2>
        <p>
          Backend на FastAPI (Python 3.11), PostgreSQL 16 с pgvector, Redis, RabbitMQ.
          Frontend — React 19 + TypeScript. Docker Compose для развёртывания.
          AI: GigaChat Pro (#1 MERA для русского), OpenAI GPT-4o,
          Anthropic Claude, 100+ моделей через OpenRouter.
        </p>

        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', margin: '1.5rem 0 0.75rem' }}>Контакты</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Mail size={18} style={{ color: 'var(--primary)' }} />
            <a href="mailto:support@resumecraft.ru" style={{ color: 'var(--primary)' }}>support@resumecraft.ru</a>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <MessageCircle size={18} style={{ color: 'var(--primary)' }} />
            <a href="https://t.me/resumecraft_support" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--primary)' }}>@resumecraft_support</a>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <MapPin size={18} style={{ color: 'var(--primary)' }} />
            <span>Москва, Россия</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <FileText size={18} style={{ color: 'var(--primary)' }} />
            <Link to="/privacy" style={{ color: 'var(--primary)' }}>Политика конфиденциальности</Link>
          </div>
        </div>
      </div>
    </div>
  )
}

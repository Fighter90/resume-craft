import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'

export default function TermsPage() {
  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '2rem 1rem' }}>
      <Link to="/" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '2rem', textDecoration: 'none' }}>
        <ArrowLeft size={16} /> На главную
      </Link>

      <h1 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '1.5rem' }}>Правила сервиса</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>Последнее обновление: 1 марта 2026 г.</p>

      <div style={{ lineHeight: 1.8, color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', margin: '1.5rem 0 0.75rem' }}>1. Предмет соглашения</h2>
        <p>
          Настоящее Пользовательское соглашение регулирует условия использования веб-сервиса ResumeCraft —
          платформы для AI-оптимизации резюме под вакансии российского рынка труда.
        </p>

        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', margin: '1.5rem 0 0.75rem' }}>2. Описание сервиса</h2>
        <p>ResumeCraft предоставляет следующие услуги:</p>
        <ul style={{ paddingLeft: '1.5rem' }}>
          <li>Загрузка и парсинг резюме в форматах PDF и DOCX</li>
          <li>Поиск вакансий через интеграцию с hh.ru API</li>
          <li>AI-оптимизация текста резюме под целевую вакансию</li>
          <li>Оценка соответствия (Match Score) и ATS-рейтинг</li>
          <li>Экспорт оптимизированного резюме в DOCX</li>
        </ul>

        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', margin: '1.5rem 0 0.75rem' }}>3. Регистрация и аккаунт</h2>
        <ul style={{ paddingLeft: '1.5rem' }}>
          <li>Для использования сервиса необходима регистрация по email</li>
          <li>Пользователь несёт ответственность за конфиденциальность пароля</li>
          <li>Один аккаунт на одного пользователя</li>
          <li>Запрещено передавать доступ к аккаунту третьим лицам</li>
        </ul>

        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', margin: '1.5rem 0 0.75rem' }}>4. Тарифные планы</h2>
        <ul style={{ paddingLeft: '1.5rem' }}>
          <li><strong>Free</strong> — 5 оптимизаций/мес, OpenRouter, DOCX экспорт</li>
          <li><strong>Standard</strong> (490 ₽/мес) — 30 оптимизаций/мес, GigaChat Pro + Claude</li>
          <li><strong>Pro</strong> (1 490 ₽/мес) — безлимит, все модели, все форматы</li>
        </ul>

        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', margin: '1.5rem 0 0.75rem' }}>5. Ограничения AI</h2>
        <ul style={{ paddingLeft: '1.5rem' }}>
          <li>AI не гарантирует трудоустройство</li>
          <li>AI не выдумывает факты и достижения — только переформулирует существующие</li>
          <li>Пользователь обязан проверить результат перед отправкой работодателю</li>
          <li>AI не генерирует дискриминационные маркеры (ТК РФ ст. 3)</li>
        </ul>

        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', margin: '1.5rem 0 0.75rem' }}>6. Загрузка файлов</h2>
        <ul style={{ paddingLeft: '1.5rem' }}>
          <li>Максимальный размер файла: 10 МБ</li>
          <li>Поддерживаемые форматы: PDF, DOCX</li>
          <li>Запрещена загрузка вредоносных файлов</li>
        </ul>

        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', margin: '1.5rem 0 0.75rem' }}>7. Ответственность</h2>
        <p>
          Сервис предоставляется «как есть». ResumeCraft не несёт ответственности за результаты использования
          оптимизированных резюме. Максимальная ответственность ограничена суммой уплаченной подписки.
        </p>

        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', margin: '1.5rem 0 0.75rem' }}>8. Контакты</h2>
        <p>
          Вопросы и предложения: <a href="mailto:support@resumecraft.ru" style={{ color: 'var(--primary)' }}>support@resumecraft.ru</a>
        </p>
      </div>
    </div>
  )
}

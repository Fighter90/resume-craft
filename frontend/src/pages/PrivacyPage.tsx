import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'

export default function PrivacyPage() {
  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '2rem 1rem' }}>
      <Link to="/" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '2rem', textDecoration: 'none' }}>
        <ArrowLeft size={16} /> На главную
      </Link>

      <h1 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '1.5rem' }}>Политика конфиденциальности</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>Последнее обновление: 1 марта 2026 г.</p>

      <div style={{ lineHeight: 1.8, color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', margin: '1.5rem 0 0.75rem' }}>1. Общие положения</h2>
        <p>
          ООО «РезюмеКрафт» (далее — «Оператор») обрабатывает персональные данные пользователей сервиса ResumeCraft
          (далее — «Сервис») в соответствии с Федеральным законом от 27.07.2006 № 152-ФЗ «О персональных данных».
        </p>

        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', margin: '1.5rem 0 0.75rem' }}>2. Какие данные мы собираем</h2>
        <ul style={{ paddingLeft: '1.5rem' }}>
          <li>Имя, фамилия, email, номер телефона — при регистрации</li>
          <li>Содержимое загруженных резюме (PDF/DOCX) — для обработки AI</li>
          <li>Данные о вакансиях — для оптимизации резюме</li>
          <li>Технические данные: IP-адрес, тип браузера, cookies — для работы сервиса</li>
        </ul>

        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', margin: '1.5rem 0 0.75rem' }}>3. Цели обработки</h2>
        <ul style={{ paddingLeft: '1.5rem' }}>
          <li>Предоставление услуг AI-оптимизации резюме</li>
          <li>Идентификация и аутентификация пользователя</li>
          <li>Улучшение качества сервиса</li>
          <li>Исполнение договорных обязательств</li>
        </ul>

        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', margin: '1.5rem 0 0.75rem' }}>4. Хранение данных</h2>
        <p>
          Персональные данные граждан РФ хранятся на серверах, расположенных на территории Российской Федерации
          (Yandex Cloud), в соответствии с требованиями ФЗ-152. Данные передаются по зашифрованному каналу (TLS 1.3).
        </p>

        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', margin: '1.5rem 0 0.75rem' }}>5. AI-обработка данных</h2>
        <p>
          Загруженные резюме обрабатываются AI-моделями (GigaChat, OpenAI, Anthropic, OpenRouter) исключительно для генерации
          оптимизированных версий. Данные не используются для обучения моделей. Основная LLM — GigaChat (Сбер) —
          обрабатывает данные на территории РФ.
        </p>

        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', margin: '1.5rem 0 0.75rem' }}>6. Права пользователя</h2>
        <ul style={{ paddingLeft: '1.5rem' }}>
          <li>Право на доступ к своим персональным данным</li>
          <li>Право на исправление неточных данных</li>
          <li>Право на удаление данных — через «Настройки → Безопасность → Удалить аккаунт»</li>
          <li>Право на отзыв согласия на обработку</li>
        </ul>

        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', margin: '1.5rem 0 0.75rem' }}>7. Cookies</h2>
        <p>
          Сервис использует необходимые cookies для аутентификации (JWT-токены) и аналитические cookies для
          улучшения качества обслуживания. Вы можете отключить cookies в настройках браузера.
        </p>

        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', margin: '1.5rem 0 0.75rem' }}>8. Контакты</h2>
        <p>
          По вопросам обработки персональных данных: <a href="mailto:privacy@resumecraft.ru" style={{ color: 'var(--primary)' }}>privacy@resumecraft.ru</a>
        </p>
      </div>
    </div>
  )
}

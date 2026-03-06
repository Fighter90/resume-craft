import { HelpCircle, Upload, Search, Cpu, Sparkles, Settings, Shield, MessageCircle, FileText, Target, Zap, BookOpen, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

interface FAQItem { q: string; a: string }

const FAQ_ITEMS: FAQItem[] = [
  {
    q: 'Как загрузить резюме?',
    a: 'Перейдите в раздел «Резюме» → «Загрузить». Поддерживаются форматы PDF, DOCX, а также ввод текста вручную или вставка URL. Максимальный размер файла — 10 МБ.',
  },
  {
    q: 'Какие форматы файлов поддерживаются?',
    a: 'Для загрузки: PDF и DOCX. Для скачивания оптимизированного резюме: PDF, DOCX и TXT.',
  },
  {
    q: 'Как выбрать целевую вакансию?',
    a: 'На странице «Вакансия» доступны 3 способа: поиск по hh.ru (по должности и городу), вставка прямой ссылки на вакансию hh.ru, или ручной ввод описания и требований.',
  },
  {
    q: 'Какую AI-модель выбрать?',
    a: 'GigaChat Pro — лучший выбор для русскоязычных резюме, #1 в MERA бенчмарке. Claude Sonnet 4 отлично подходит для длинных текстов (200K контекст). GPT-4o — универсальный вариант. OpenRouter даёт доступ к 100+ моделям.',
  },
  {
    q: 'Что такое Match Score?',
    a: 'Match Score — комплексная оценка соответствия резюме вакансии: Ключевые слова (40%), Опыт (25%), Структура (20%), Читаемость (15%). Чем выше — тем больше шансов пройти ATS-фильтры.',
  },
  {
    q: 'Что такое ATS-совместимость?',
    a: 'ATS (Applicant Tracking System) — система автоматической обработки резюме, которую используют HR-отделы. Рейтинг от A+ до D показывает, насколько хорошо ваше резюме будет прочитано и ранжировано такими системами.',
  },
  {
    q: 'AI выдумывает факты?',
    a: 'Нет. Наш системный промпт прямо запрещает выдумывать факты и достижения. AI переформулирует существующий опыт используя формулу «Действие + Результат + Метрика» и добавляет ключевые слова из вакансии только если навык подтверждается опытом.',
  },
  {
    q: 'Где хранятся мои данные?',
    a: 'Все данные хранятся на серверах в России (Yandex Cloud) в соответствии с ФЗ-152 о персональных данных. При использовании GigaChat данные обрабатываются через Сбер (данные не покидают РФ).',
  },
  {
    q: 'Как настроить API-ключи?',
    a: 'Перейдите в Настройки → AI-модели. Введите API-ключ для желаемого провайдера (OpenAI, Anthropic, OpenRouter или GigaChat). Ключи хранятся только на вашем устройстве в localStorage.',
  },
  {
    q: 'Сколько оптимизаций доступно?',
    a: 'Free — 5 оптимизаций/мес, Standard (490 ₽/мес) — 30 оптимизаций, Pro (1 490 ₽/мес) — безлимит. Количество использованных оптимизаций отображается в профиле.',
  },
  {
    q: 'Ошибка «LLM-провайдер недоступен»?',
    a: 'Эта ошибка означает, что ни один провайдер не настроен. Перейдите в Настройки → AI-модели и добавьте API-ключ хотя бы для одного провайдера. Также проверьте баланс аккаунта у провайдера.',
  },
  {
    q: 'Как удалить мои данные?',
    a: 'Перейдите в Настройки → Безопасность → «Удалить аккаунт». Введите «УДАЛИТЬ» для подтверждения. Все данные, резюме и история будут безвозвратно удалены.',
  },
]

function FAQAccordion({ items }: { items: FAQItem[] }) {
  const [open, setOpen] = useState<number | null>(null)
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      {items.map((item, i) => (
        <div key={i} className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <button
            onClick={() => setOpen(open === i ? null : i)}
            style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              width: '100%', padding: '1rem 1.25rem', border: 'none', background: 'none',
              cursor: 'pointer', textAlign: 'left', fontSize: '0.9rem', fontWeight: 600,
              color: 'var(--text)',
            }}
          >
            {item.q}
            {open === i ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
          {open === i && (
            <div style={{ padding: '0 1.25rem 1rem', fontSize: '0.85rem', lineHeight: 1.7, color: 'var(--text-secondary)' }}>
              {item.a}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

export default function HelpPage() {
  return (
    <div style={{ maxWidth: 800 }}>
      <div className="page-header" style={{ marginBottom: '2rem' }}>
        <div>
          <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <HelpCircle size={28} /> Справка
          </h1>
          <p style={{ color: 'var(--text-secondary)' }}>Руководство по использованию ResumeCraft</p>
        </div>
      </div>

      {/* Quick start guide */}
      <div className="card" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Zap size={20} style={{ color: 'var(--primary)' }} /> Быстрый старт
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
          {[
            { icon: Upload, title: '1. Загрузите резюме', desc: 'PDF, DOCX, текст или URL', link: '/app/upload' },
            { icon: Search, title: '2. Укажите вакансию', desc: 'Поиск hh.ru, URL или вручную', link: '/app/vacancy' },
            { icon: Cpu, title: '3. Выберите модель', desc: 'GigaChat, GPT-4o, Claude и др.', link: '/app/models' },
            { icon: Sparkles, title: '4. Получите результат', desc: 'Match Score, ATS-рейтинг, diff', link: '/app/results' },
          ].map((step, i) => (
            <Link key={i} to={step.link} style={{ textDecoration: 'none', color: 'inherit' }}>
              <div className="card" style={{
                padding: '1rem', display: 'flex', flexDirection: 'column', alignItems: 'center',
                textAlign: 'center', gap: '0.5rem', transition: 'transform 0.15s',
              }}>
                <div style={{
                  width: 48, height: 48, borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center',
                  background: 'var(--primary-bg, rgba(86,90,221,0.1))',
                }}>
                  <step.icon size={22} style={{ color: 'var(--primary)' }} />
                </div>
                <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{step.title}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{step.desc}</div>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Pipeline explanation */}
      <div className="card" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <BookOpen size={20} style={{ color: 'var(--primary)' }} /> Как работает оптимизация
        </h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.9rem', lineHeight: 1.7, color: 'var(--text-secondary)' }}>
          <p><strong>1. Парсинг и извлечение текста</strong> — ResumeCraft извлекает текст из загруженного файла (PyMuPDF для PDF, python-docx для DOCX). Для сканированных PDF используется OCR.</p>
          <p><strong>2. Анализ вакансии</strong> — из вакансии извлекаются ключевые слова, требования, навыки и определяются критерии соответствия.</p>
          <p><strong>3. AI Gap Analysis</strong> — определяются пробелы между резюме и вакансией: недостающие ключевые слова, слабые формулировки, нерелевантные секции.</p>
          <p><strong>4. Стратегия оптимизации</strong> — AI выстраивает план: какие секции усилить, какие ключевые слова добавить, как переформулировать достижения.</p>
          <p><strong>5. AI Rewrite</strong> — резюме переписывается с учётом стратегии. Используется формула «Действие + Результат + Метрика» для каждого достижения.</p>
          <p><strong>6. Валидация</strong> — проверка что AI не добавил вымышленных фактов, сохранил ключевые данные (ФИО, контакты, даты).</p>
          <p><strong>7. Скоринг</strong> — расчёт Match Score (Keywords 40% + Experience 25% + Structure 20% + Readability 15%) и ATS-рейтинга.</p>
          <p><strong>8. Финализация</strong> — генерация diff-сравнения, списка добавленных ключевых слов и итогового отчёта.</p>
        </div>
      </div>

      {/* Features */}
      <div className="card" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Target size={20} style={{ color: 'var(--primary)' }} /> Возможности
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
          {[
            { icon: FileText, title: 'Мультиформат', desc: 'Загрузка PDF, DOCX, текст, URL. Скачивание в PDF, DOCX, TXT.' },
            { icon: Search, title: 'Интеграция hh.ru', desc: 'Поиск вакансий, автоматический парсинг требований и навыков.' },
            { icon: Cpu, title: 'Мультимодельный AI', desc: 'GigaChat Pro, GPT-4o, Claude Sonnet 4, OpenRouter (100+ моделей).' },
            { icon: Target, title: 'Match Score', desc: '4-компонентная оценка соответствия: слова, опыт, структура, читаемость.' },
            { icon: Shield, title: 'ATS-совместимость', desc: 'Рейтинг A+ – D с рекомендациями по улучшению.' },
            { icon: Sparkles, title: 'Diff с подсветкой', desc: 'Наглядное сравнение оригинала и оптимизированной версии.' },
          ].map((f, i) => (
            <div key={i} style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
              <f.icon size={20} style={{ color: 'var(--primary)', flexShrink: 0, marginTop: 2 }} />
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{f.title}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{f.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Tariff plans */}
      <div className="card" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Settings size={20} style={{ color: 'var(--primary)' }} /> Тарифные планы
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
          {[
            { name: 'Free', price: '0 ₽', features: ['5 оптимизаций/мес', 'Все модели', 'PDF/DOCX экспорт'] },
            { name: 'Standard', price: '490 ₽/мес', features: ['30 оптимизаций/мес', 'Приоритетная обработка', 'История оптимизаций'] },
            { name: 'Pro', price: '1 490 ₽/мес', features: ['Безлимит', 'API-доступ', 'Персональная поддержка'] },
          ].map((plan, i) => (
            <div key={i} className="card" style={{ padding: '1rem', textAlign: 'center' }}>
              <div style={{ fontWeight: 700, fontSize: '1rem', marginBottom: '0.25rem' }}>{plan.name}</div>
              <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--primary)', marginBottom: '0.75rem' }}>{plan.price}</div>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '0.8rem', color: 'var(--text-secondary)', textAlign: 'left' }}>
                {plan.features.map((f, j) => <li key={j} style={{ padding: '0.2rem 0' }}>✓ {f}</li>)}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* FAQ */}
      <h2 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <MessageCircle size={20} style={{ color: 'var(--primary)' }} /> Часто задаваемые вопросы
      </h2>
      <FAQAccordion items={FAQ_ITEMS} />

      {/* Contact / feedback */}
      <div className="card" style={{ padding: '1.5rem', marginTop: '2rem', textAlign: 'center' }}>
        <h3 style={{ fontWeight: 600, marginBottom: '0.5rem' }}>Не нашли ответ?</h3>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
          Напишите нам, и мы поможем разобраться
        </p>
        <a href="mailto:support@resumecraft.ru" className="btn btn-primary">
          <MessageCircle size={16} /> support@resumecraft.ru
        </a>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginTop: '1rem' }}>
          <a href="https://github.com/Sensi44/ResumeCraft" target="_blank" rel="noopener noreferrer" style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <ExternalLink size={12} /> GitHub
          </a>
        </div>
      </div>
    </div>
  )
}

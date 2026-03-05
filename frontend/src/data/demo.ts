// Demo data for UI rendering (mirrors streamlit_app/demo_data.py)

export const DEMO_USER = {
  id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
  email: 'alex@example.com',
  full_name: 'Александр Петров',
  plan: 'free' as const,
  optimizations_used: 2,
  is_active: true,
}

export const DEMO_RESUMES = [
  {
    id: '1', title: 'Product Manager @ Yandex', file_format: 'pdf',
    status: 'optimized', match_score: 92, ats_rating: 'A+', model: 'GigaChat Pro',
    vacancy: 'Senior PM @ Яндекс', date: '20 мин назад',
    tags: ['Product Strategy', 'A/B Testing', 'SQL', 'Agile'],
  },
  {
    id: '2', title: 'Product Manager @ Тинькофф', file_format: 'pdf',
    status: 'optimized', match_score: 87, ats_rating: 'A', model: 'GPT-4o',
    vacancy: 'PM @ Тинькофф', date: '2 ч назад',
    tags: ['B2C', 'Fintech', 'Metrics'],
  },
  {
    id: '3', title: 'Frontend Developer', file_format: 'docx',
    status: 'draft', match_score: null, ats_rating: null, model: null,
    vacancy: null, date: '5 ч назад',
    tags: ['React', 'TypeScript'],
  },
  {
    id: '4', title: 'Data Analyst @ Ozon', file_format: 'pdf',
    status: 'optimized', match_score: 68, ats_rating: 'B', model: 'Claude Sonnet 4',
    vacancy: 'Data Analyst @ Ozon', date: '17 фев',
    tags: ['Python', 'SQL', 'Tableau'],
  },
  {
    id: '5', title: 'Marketing Manager', file_format: 'docx',
    status: 'processing', match_score: null, ats_rating: null, model: 'GigaChat Pro',
    vacancy: 'CMO @ Wildberries', date: '12 фев',
    tags: ['Digital', 'SEO', 'Content'],
  },
]

export const DEMO_VACANCIES = [
  {
    id: '1', title: 'Senior Product Manager', company: 'Яндекс', city: 'Москва',
    type: 'Гибрид', salary: 'от 350 000 ₽', matchScore: 92,
    tags: ['Product Strategy', 'A/B Testing', 'SQL', 'Agile'],
  },
  {
    id: '2', title: 'Product Manager', company: 'Тинькофф', city: 'Москва',
    salary: 'от 280 000 ₽', matchScore: 87,
    tags: ['B2C', 'Fintech', 'Metrics'],
  },
  {
    id: '3', title: 'Product Owner', company: 'Ozon', city: 'Удалённо',
    salary: 'от 250 000 ₽', matchScore: 74,
    tags: ['E-commerce', 'Scrum'],
  },
]

export const DEMO_HISTORY = [
  {
    date: 'Сегодня', items: [
      { type: 'optimization', title: 'Оптимизация завершена', desc: 'Resume_PM_v3.pdf → Senior PM @ Яндекс', time: '20 мин назад', match: 92, model: 'GigaChat Pro' },
      { type: 'upload', title: 'Файл загружен', desc: 'Resume_PM_v3.pdf · 245 КБ', time: '35 мин назад' },
      { type: 'optimization', title: 'Оптимизация завершена', desc: 'Resume_PM_Tinkoff.pdf → PM @ Тинькофф', time: '2 ч назад', match: 87, model: 'GPT-4o' },
    ]
  },
  {
    date: 'Вчера', items: [
      { type: 'upload', title: 'Файл загружен', desc: 'Resume_Frontend.docx · 312 КБ', time: '14:30' },
      { type: 'export', title: 'Экспорт PDF', desc: 'Resume_PM_Tinkoff_optimized.pdf', time: '11:15' },
    ]
  },
  {
    date: '17 февраля', items: [
      { type: 'optimization', title: 'Оптимизация завершена', desc: 'Resume_Data_Analyst.pdf → Data Analyst @ Ozon', time: '16:45', match: 68, model: 'Claude Sonnet 4' },
      { type: 'upload', title: 'Файл загружен', desc: 'Resume_Data_Analyst.pdf · 198 КБ', time: '16:30' },
    ]
  },
  {
    date: '12 февраля', items: [
      { type: 'account', title: 'Аккаунт создан', desc: 'Добро пожаловать в ResumeCraft!', time: '10:00' },
    ]
  },
]

export const DEMO_SCORES = {
  matchScore: 87,
  improvement: 34,
  atsRating: 'A+',
  keywordsTotal: 24,
  keywordsAdded: 18,
  model: 'GigaChat Pro',
  breakdown: {
    keywords: 92,
    experience: 85,
    structure: 80,
    readability: 88,
  },
}

export const DEMO_KEYWORDS = [
  'A/B Testing', 'Product Strategy', 'SQL', 'Agile/Scrum', 'B2C SaaS',
  'Data-Driven', 'Amplitude', 'Cross-functional', 'KPI', 'Jira',
  'Backlog', 'MAU', 'Conversion', 'Sprint Delivery', 'B2B',
  'Roadmap', 'User Research', 'Metrics',
]

export const DEMO_ORIGINAL_TEXT = {
  name: 'Александр Петров',
  position: 'Product Manager',
  summary: 'Опытный продакт-менеджер. Работал в нескольких компаниях. Умею управлять командой и запускать продукты.',
  experience: 'Product Manager — TechCorp\n2021–н.в.\nУправлял продуктом. Работал с командой разработки. Запускал новые функции.',
  score: 53,
}

export const DEMO_OPTIMIZED_TEXT = {
  name: 'Александр Петров',
  position: 'Senior Product Manager | B2C & B2B SaaS | Agile & Data-Driven',
  summary: 'Product Manager с 5+ годами опыта в B2C/B2B SaaS. Руководил кросс-функциональными командами до 12 человек. Увеличил ключевые продуктовые метрики на 40% через data-driven подход. Экспертиза: SQL, Amplitude, Jira, Agile/Scrum.',
  experience: 'Senior Product Manager — TechCorp\n2021–н.в.\nРуководил развитием B2C-продукта с MAU 500K+. Повысил конверсию воронки на 35% через систематическое A/B-тестирование (30+ экспериментов). Управлял backlog из 200+ задач, обеспечивая 95% sprint delivery.',
  score: 87,
}

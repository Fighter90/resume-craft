"""Демо-данные для работы без бэкенда."""

from __future__ import annotations

DEMO_RESUME_TEXT = """Иванов Александр Сергеевич
Продакт-менеджер

Опыт работы:
Старший продакт-менеджер, ООО «ТехноСтарт», 2021–2024
- Управлял продуктом с MAU 200K
- Работал с командой разработки
- Запустил новый функционал

Продакт-менеджер, ООО «ДиджиталИнновация», 2019–2021
- Вёл backlog продукта
- Проводил интервью с пользователями
- Подготовил roadmap

Образование:
МГУ им. Ломоносова, Факультет ВМК, Прикладная математика, 2019

Навыки:
Python, SQL, Jira, Product Management, Аналитика"""

DEMO_OPTIMIZED = {
    'summary': (
        'Senior Product Manager с 5+ лет опыта в B2C и B2B SaaS. '
        'Руководил продуктами с MAU 500K+. Увеличил ключевые бизнес-метрики на 40% '
        'через Data-Driven подход и A/B тестирование. Опыт управления кросс-функциональными '
        'командами до 15 человек.'
    ),
    'experience': [
        {
            'position': 'Senior Product Manager',
            'company': 'ООО «ТехноСтарт»',
            'period': '2021–2024',
            'achievements': [
                'Руководил B2C-платформой с MAU 500K+, увеличил конверсию регистрации на 35% '
                'через серию A/B тестов (12 экспериментов за квартал)',
                'Внедрил систему OKR и Data-Driven принятие решений, что сократило Time-to-Market '
                'новых фич на 28% (с 6 до 4.3 недель)',
                'Управлял кросс-функциональной командой из 12 человек '
                '(Backend, Frontend, QA, Design), обеспечив 95% Sprint Delivery Rate',
            ],
        },
        {
            'position': 'Product Manager',
            'company': 'ООО «ДиджиталИнновация»',
            'period': '2019–2021',
            'achievements': [
                'Провёл 50+ Customer Development интервью, выявил 3 ключевых Pain Point, '
                'что привело к росту NPS с 32 до 58',
                'Разработал и реализовал Product Roadmap на 12 месяцев, '
                'приоритизируя по RICE-фреймворку',
                'Запустил MVP нового B2B-модуля за 8 недель, '
                'привлекшего 200+ корпоративных клиентов в первый квартал',
            ],
        },
    ],
    'education': [
        {
            'institution': 'МГУ им. М.В. Ломоносова',
            'degree': 'Специалист',
            'specialization': 'Прикладная математика и информатика',
            'year': 2019,
        },
    ],
    'skills': [
        'Product Strategy', 'A/B Testing', 'SQL', 'Python', 'Agile/Scrum',
        'Jira', 'Amplitude', 'Data-Driven', 'B2C SaaS', 'B2B SaaS',
        'OKR', 'RICE', 'Customer Development', 'Roadmap Planning',
        'Cross-functional Leadership', 'KPI', 'NPS', 'Unit Economics',
    ],
    'keywords_added': [
        'A/B Testing', 'Product Strategy', 'Data-Driven', 'Amplitude',
        'Cross-functional', 'KPI', 'B2C SaaS', 'Agile/Scrum',
        'MAU', 'Conversion', 'Sprint Delivery', 'B2B',
        'Roadmap', 'User Research', 'Metrics', 'OKR',
        'RICE', 'NPS',
    ],
}

DEMO_SCORES = {
    'match_score_before': 53.0,
    'match_score_after': 87.0,
    'ats_rating': 'A+',
    'keywords': {'weight': 40, 'score': 92},
    'experience': {'weight': 25, 'score': 85},
    'structure': {'weight': 20, 'score': 80},
    'readability': {'weight': 15, 'score': 88},
    'model_name': 'GigaChat Pro',
}

DEMO_VACANCY = {
    'title': 'Senior Product Manager',
    'company': 'Яндекс',
    'description': (
        'Мы ищем опытного Product Manager для работы над ключевыми B2C-продуктами. '
        'Вы будете отвечать за стратегию продукта, работу с данными и A/B тестирование. '
        'Требования: 5+ лет опыта в product management, опыт с B2C SaaS, '
        'знание SQL и аналитических инструментов (Amplitude, Mixpanel), '
        'опыт Agile/Scrum, понимание Unit Economics.'
    ),
    'key_skills': [
        'Product Strategy', 'A/B Testing', 'SQL', 'Agile/Scrum',
        'B2C SaaS', 'Amplitude', 'Data-Driven', 'Cross-functional',
    ],
    'city': 'Москва',
    'salary_from': 350000,
}

# Демо-список резюме для страницы «Мои резюме» (07)
DEMO_RESUMES_LIST = [
    {
        'id': 'r1',
        'title': 'Senior_PM_Resume.pdf',
        'vacancy': 'Senior PM @ Яндекс',
        'status': 'optimized',
        'match_score': 87,
        'model': 'GigaChat Pro',
        'date': 'Сегодня, 14:32',
        'format': 'pdf',
    },
    {
        'id': 'r2',
        'title': 'Product_Manager_CV.docx',
        'vacancy': 'Product Manager @ VK',
        'status': 'optimized',
        'match_score': 76,
        'model': 'Llama 3',
        'date': 'Вчера, 10:15',
        'format': 'docx',
    },
    {
        'id': 'r3',
        'title': 'Resume_Draft.pdf',
        'vacancy': None,
        'status': 'draft',
        'match_score': None,
        'model': None,
        'date': '28 февраля',
        'format': 'pdf',
    },
    {
        'id': 'r4',
        'title': 'CV_Analyst.docx',
        'vacancy': 'Data Analyst @ Сбер',
        'status': 'processing',
        'match_score': None,
        'model': 'GigaChat Pro',
        'date': 'Сегодня, 16:45',
        'format': 'docx',
    },
    {
        'id': 'r5',
        'title': 'Backend_Dev.pdf',
        'vacancy': 'Python Developer @ Ozon',
        'status': 'optimized',
        'match_score': 91,
        'model': 'GigaChat Pro',
        'date': '25 февраля',
        'format': 'pdf',
    },
]

# Демо-история для страницы «История» (15)
DEMO_HISTORY = [
    {
        'date': 'Сегодня',
        'events': [
            {
                'type': 'optimization',
                'time': '14:32',
                'title': 'Оптимизация завершена',
                'detail': 'Senior_PM_Resume.pdf → Senior PM @ Яндекс',
                'score': 87,
                'model': 'GigaChat Pro',
            },
            {
                'type': 'upload',
                'time': '14:30',
                'title': 'Файл загружен',
                'detail': 'Senior_PM_Resume.pdf (245 КБ)',
            },
        ],
    },
    {
        'date': 'Вчера',
        'events': [
            {
                'type': 'export',
                'time': '18:05',
                'title': 'Экспорт DOCX',
                'detail': 'Product_Manager_Optimized.docx',
            },
            {
                'type': 'optimization',
                'time': '10:15',
                'title': 'Оптимизация завершена',
                'detail': 'Product_Manager_CV.docx → Product Manager @ VK',
                'score': 76,
                'model': 'Llama 3',
            },
        ],
    },
    {
        'date': '25 февраля',
        'events': [
            {
                'type': 'optimization',
                'time': '09:20',
                'title': 'Оптимизация завершена',
                'detail': 'Backend_Dev.pdf → Python Developer @ Ozon',
                'score': 91,
                'model': 'GigaChat Pro',
            },
            {
                'type': 'upload',
                'time': '09:18',
                'title': 'Файл загружен',
                'detail': 'Backend_Dev.pdf (178 КБ)',
            },
        ],
    },
    {
        'date': '12 февраля',
        'events': [
            {
                'type': 'account',
                'time': '12:00',
                'title': 'Аккаунт создан',
                'detail': 'Добро пожаловать в ResumeCraft!',
            },
        ],
    },
]

# Демо-платежи для страницы настроек подписки (18)
DEMO_PAYMENTS: list[dict[str, str]] = []  # У Free-пользователя нет платежей

# Демо-сессии для настроек безопасности (19)
DEMO_SESSIONS = [
    {
        'device': 'MacBook Pro',
        'browser': 'Chrome',
        'location': 'Москва, Россия',
        'last_active': 'Сейчас',
        'current': True,
        'icon': '💻',
    },
    {
        'device': 'iPhone 15',
        'browser': 'Safari',
        'location': 'Москва, Россия',
        'last_active': '2 часа назад',
        'current': False,
        'icon': '📱',
    },
    {
        'device': 'Windows PC',
        'browser': 'Firefox',
        'location': 'Санкт-Петербург, Россия',
        'last_active': '3 дня назад',
        'current': False,
        'icon': '🖥️',
    },
]

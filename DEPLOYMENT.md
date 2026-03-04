# ResumeCraft — Руководство по развёртыванию

> Гайд по запуску ResumeCraft в трёх режимах: локальная разработка, Docker (staging), продакшен (VPS).

---

## Содержание

1. [Системные требования](#1-системные-требования)
2. [Локальная разработка (без Docker)](#2-локальная-разработка-без-docker)
3. [Docker (staging / локальный)](#3-docker-staging--локальный)
4. [Продакшен (VPS)](#4-продакшен-vps)
5. [Миграции БД](#5-миграции-бд)
6. [Мониторинг и логирование](#6-мониторинг-и-логирование)
7. [Backup и восстановление](#7-backup-и-восстановление)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Системные требования

### 1.1. Минимальные требования

| Компонент | Локальная разработка | Staging (Docker) | Production |
|-----------|---------------------|-----------------|------------|
| **OS** | macOS 13+ / Ubuntu 22.04+ / Windows 11 (WSL2) | Linux / macOS | Ubuntu 24.04 LTS |
| **Python** | 3.11+ | Не требуется (в Docker) | Не требуется |
| **RAM** | 4 ГБ | 4 ГБ | 8 ГБ+ |
| **Диск** | 2 ГБ | 5 ГБ | 20 ГБ+ SSD |
| **CPU** | 2 ядра | 2 ядра | 4 ядра |
| **Docker** | — | 24.0+ | 27.0+ |
| **Docker Compose** | — | v2.20+ | v2.30+ |

### 1.2. Внешние сервисы

| Сервис | Обязателен | Назначение | Получение ключа |
|--------|:----------:|-----------|----------------|
| PostgreSQL 16 | ✅ | Основная БД | Локально или Docker |
| Redis 7 | ⚠️ | Кэш + Celery results | Локально или Docker |
| RabbitMQ 3.13 | ⚠️ | Celery брокер | Локально или Docker |
| GigaChat API | ❌ | LLM (основная) | [developers.sber.ru](https://developers.sber.ru) |
| Groq API | ❌ | LLM (бесплатная) | [console.groq.com](https://console.groq.com) |
| OpenAI API | ❌ | LLM (резервная) | [platform.openai.com](https://platform.openai.com) |
| OpenRouter API | ❌ | LLM (мульти-провайдер) | [openrouter.ai](https://openrouter.ai) |

> ⚠️ Redis и RabbitMQ нужны для Celery. Для разработки без фоновых задач можно пропустить.

---

## 2. Локальная разработка (без Docker)

### 2.1. Установка Python и зависимостей

```bash
# 1. Клонирование
git clone https://github.com/your-org/resumecraft.git
cd resumecraft

# 2. Python виртуальное окружение
python3.11 -m venv .venv
source .venv/bin/activate      # macOS / Linux
# .venv\Scripts\activate       # Windows PowerShell

# 3. Установка всех зависимостей (включая dev)
pip install -r requirements-dev.txt
```

### 2.2. Настройка переменных окружения

```bash
cp .env.example .env
```

Минимальный `.env` для локальной работы:

```dotenv
SECRET_KEY=my-dev-secret-key-at-least-32-chars-long-for-jwt
DATABASE_URL=postgresql+asyncpg://resumecraft:devpassword@localhost:5432/resumecraft
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
CELERY_RESULT_BACKEND=redis://localhost:6379/1
UPLOAD_DIR=./uploads
ENVIRONMENT=development
DEBUG=true
```

### 2.3. Настройка PostgreSQL

```bash
# macOS (Homebrew)
brew install postgresql@16
brew services start postgresql@16

# Ubuntu
sudo apt install postgresql-16 postgresql-16-pgvector

# Создание БД и пользователя
psql -U postgres -c "CREATE USER resumecraft WITH PASSWORD 'devpassword';"
psql -U postgres -c "CREATE DATABASE resumecraft OWNER resumecraft;"
psql -U resumecraft -d resumecraft -c 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'
psql -U resumecraft -d resumecraft -c 'CREATE EXTENSION IF NOT EXISTS "vector";'
```

### 2.4. Настройка Redis и RabbitMQ (опционально)

```bash
# macOS
brew install redis rabbitmq
brew services start redis
brew services start rabbitmq

# Ubuntu
sudo apt install redis-server rabbitmq-server
sudo systemctl start redis-server rabbitmq-server
```

### 2.5. Миграции БД

```bash
alembic upgrade head
```

### 2.6. Запуск сервисов

```bash
# Терминал 1 — FastAPI
uvicorn app.main:app --app-dir src --reload --port 8000

# Терминал 2 — Celery Worker (требует Redis + RabbitMQ)
cd src && celery -A app.core.celery_app:celery_app worker --loglevel=info --concurrency=2

# Терминал 3 — React Frontend (dev mode)
cd frontend && npm run dev -- --port 3000
```

### 2.7. Проверка

```bash
# Health check
curl http://localhost:8000/health
# → {"status": "healthy"}

# Тесты (используют SQLite in-memory, не требуют PostgreSQL)
pytest --cov --cov-report=term-missing

# Линтинг
ruff check src/ tests/

# Типы
mypy src/
```

---

## 3. Docker (staging / локальный)

### 3.1. Подготовка

```bash
# 1. Клонирование
git clone https://github.com/your-org/resumecraft.git
cd resumecraft

# 2. Копирование .env
cp .env.example .env
# Обязательно: задайте SECRET_KEY
```

### 3.2. Запуск

```bash
# Сборка и запуск всех 7 сервисов
docker compose up -d --build

# Проверка статуса
docker compose ps

# Ожидание готовности PostgreSQL (healthcheck ~15 сек)
docker compose logs -f db
```

### 3.3. Инициализация БД

```bash
# Миграции
docker compose exec app alembic upgrade head
```

### 3.4. Сервисы и порты

| Сервис | Контейнер | URL | Назначение |
|--------|-----------|-----|-----------|
| FastAPI | `resumecraft-app` | http://localhost:8000 | REST API |
| Celery Worker | `resumecraft-celery` | — | Фоновые LLM-задачи |
| PostgreSQL | `resumecraft-db` | localhost:5432 | База данных |
| Redis | `resumecraft-redis` | localhost:6379 | Кэш + results |
| RabbitMQ | `resumecraft-rabbitmq` | http://localhost:15672 | Брокер (UI: guest/guest) |
| Flower | `resumecraft-flower` | http://localhost:5555 | Мониторинг Celery |
| Frontend | `resumecraft-frontend` | http://localhost:3000 | React SPA (nginx) |

### 3.5. Полезные команды

```bash
# Логи всех сервисов
docker compose logs -f

# Логи только API
docker compose logs -f app

# Перезапуск одного сервиса
docker compose restart app

# Пересборка после изменений кода
docker compose up -d --build app celery-worker

# Остановка
docker compose down

# Остановка + удаление данных (volumes)
docker compose down -v

# Вход в контейнер
docker compose exec app bash

# Запуск миграций
docker compose exec app alembic upgrade head

# Откат миграции
docker compose exec app alembic downgrade -1
```

### 3.6. Docker Hub заблокирован?

Если Docker Hub недоступен из вашей сети, используйте зеркала:

```bash
# /etc/docker/daemon.json
{
  "registry-mirrors": [
    "https://mirror.gcr.io",
    "https://cr.yandex"
  ]
}

# Перезапуск Docker
sudo systemctl restart docker
```

---

## 4. Продакшен (VPS)

### 4.1. Рекомендуемая конфигурация

| Параметр | Значение |
|----------|----------|
| **VPS** | Yandex Cloud / Selectel / Timeweb |
| **OS** | Ubuntu 24.04 LTS |
| **CPU** | 4 vCPU |
| **RAM** | 8 ГБ |
| **SSD** | 40+ ГБ NVMe |
| **Пропускная способность** | 100 Мбит/с |

### 4.2. Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Установка Docker Compose v2
sudo apt install docker-compose-plugin

# Firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 4.3. Установка Nginx + SSL

```bash
# Nginx
sudo apt install nginx certbot python3-certbot-nginx

# SSL-сертификат (Let's Encrypt)
sudo certbot --nginx -d resumecraft.ru -d www.resumecraft.ru
```

**Nginx конфигурация** (`/etc/nginx/sites-available/resumecraft`):

```nginx
upstream fastapi {
    server 127.0.0.1:8000;
}

upstream frontend {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name resumecraft.ru www.resumecraft.ru;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name resumecraft.ru www.resumecraft.ru;

    ssl_certificate /etc/letsencrypt/live/resumecraft.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/resumecraft.ru/privkey.pem;

    # Security headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Content-Security-Policy "default-src 'self'" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    client_max_body_size 10M;

    # API — все запросы /api/ и /health проксируются на FastAPI
    location /api/ {
        proxy_pass http://fastapi;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    location /health {
        proxy_pass http://fastapi;
        access_log off;
    }

    location /docs {
        proxy_pass http://fastapi;
    }

    location /openapi.json {
        proxy_pass http://fastapi;
    }

    # Frontend — React SPA (обслуживается nginx в контейнере frontend)
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/resumecraft /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 4.4. Production .env

```dotenv
# КРИТИЧНО: сгенерируйте уникальный ключ
SECRET_KEY=<openssl rand -hex 32>

# Database
DATABASE_URL=postgresql+asyncpg://resumecraft:<strong-password>@db:5432/resumecraft
POSTGRES_PASSWORD=<strong-password>

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=amqp://resumecraft:<rabbit-password>@rabbitmq:5672//
CELERY_RESULT_BACKEND=redis://redis:6379/1

# LLM
GIGACHAT_CREDENTIALS=<ваш-ключ-от-developers.sber.ru>
GROQ_API_KEY=<ваш-ключ-от-console.groq.com>
OPENROUTER_API_KEY=<ваш-ключ-от-openrouter.ai>

# Production
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
CORS_ORIGINS=["https://resumecraft.ru"]
UPLOAD_DIR=/data/uploads
```

### 4.5. Запуск

```bash
# Клонирование на сервер
git clone https://github.com/your-org/resumecraft.git /opt/resumecraft
cd /opt/resumecraft

# Настройка .env
cp .env.example .env
nano .env  # Заполнить production-значения

# Сборка и запуск
docker compose up -d --build

# Миграции
docker compose exec app alembic upgrade head

# Проверка
curl https://resumecraft.ru/health
```

### 4.6. Автозапуск при перезагрузке

```bash
# Docker уже настроен с restart: unless-stopped
# Дополнительно можно добавить systemd-сервис:

sudo tee /etc/systemd/system/resumecraft.service << 'EOF'
[Unit]
Description=ResumeCraft Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=true
WorkingDirectory=/opt/resumecraft
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable resumecraft
```

---

## 5. Миграции БД

### 5.1. Обзор

Миграции управляются через **Alembic** (async mode). Конфигурация: `alembic.ini` + `alembic/env.py`.

Текущие миграции:
- `001_initial` — Создание 4 таблиц: `users`, `resumes`, `vacancies`, `rewrite_history` + расширения `uuid-ossp`, `vector`

### 5.2. Основные команды

```bash
# Применить все миграции
alembic upgrade head

# Откатить последнюю
alembic downgrade -1

# Откатить всё
alembic downgrade base

# Показать текущую ревизию
alembic current

# Показать историю
alembic history --verbose

# Создать новую миграцию (autogenerate)
alembic revision --autogenerate -m "add_subscription_table"

# Создать пустую миграцию
alembic revision -m "custom_migration"
```

### 5.3. В Docker

```bash
docker compose exec app alembic upgrade head
docker compose exec app alembic current
docker compose exec app alembic downgrade -1
```

### 5.4. Правила миграций

- Каждая миграция **reversible** (upgrade + downgrade)
- Тестировать: `alembic upgrade head` → `alembic downgrade base` → `alembic upgrade head`
- Не редактировать уже применённые миграции
- Одна миграция = одно логическое изменение

---

## 6. Мониторинг и логирование

### 6.1. Health Check

```bash
# API health
curl http://localhost:8000/health
# → {"status": "healthy"}
```

### 6.2. Flower (Celery мониторинг)

- URL: http://localhost:5555
- Показывает: количество задач, воркеры, статусы, время выполнения

### 6.3. Логи Docker

```bash
# Все сервисы
docker compose logs -f

# Конкретный сервис
docker compose logs -f app --tail=100

# С timestamps
docker compose logs -f --timestamps app celery-worker
```

### 6.4. RabbitMQ Management

- URL: http://localhost:15672
- Login: guest / guest
- Показывает: очереди, сообщения, consumers

---

## 7. Backup и восстановление

### 7.1. PostgreSQL

```bash
# Backup
docker compose exec db pg_dump -U resumecraft resumecraft > backup_$(date +%Y%m%d).sql

# Restore
docker compose exec -T db psql -U resumecraft resumecraft < backup_20250201.sql
```

### 7.2. Upload-файлы

```bash
# Backup volume
docker run --rm -v resumecraft_upload_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/uploads_$(date +%Y%m%d).tar.gz -C /data .

# Restore
docker run --rm -v resumecraft_upload_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/uploads_20250201.tar.gz -C /data
```

### 7.3. Автоматический backup (cron)

```bash
# Добавить в crontab
0 3 * * * cd /opt/resumecraft && docker compose exec -T db pg_dump -U resumecraft resumecraft | gzip > /backups/db_$(date +\%Y\%m\%d).sql.gz
```

---

## 8. Troubleshooting

### 8.1. Частые проблемы

| Проблема | Решение |
|----------|---------|
| `Connection refused` к PostgreSQL | Проверьте `docker compose ps db` и healthcheck |
| `ModuleNotFoundError` | `pip install -r requirements.txt` в правильном venv |
| Docker Hub недоступен | Настройте зеркало (п. 3.6) |
| 401 на API | Проверьте `SECRET_KEY` в .env |
| Celery tasks не выполняются | `docker compose logs celery-worker` + проверьте RabbitMQ |
| `alembic: Target database is not up to date` | `alembic upgrade head` |
| Порт занят | `lsof -i :8000` или `docker compose down` |
| Тесты падают | Тесты используют SQLite — не нужен PostgreSQL |

### 8.2. Проверка сервисов

```bash
# PostgreSQL
docker compose exec db pg_isready -U resumecraft

# Redis
docker compose exec redis redis-cli ping

# RabbitMQ
docker compose exec rabbitmq rabbitmq-diagnostics ping

# Celery workers
docker compose exec celery-worker celery -A app.core.celery_app:celery_app inspect active
```

### 8.3. Сброс и переинициализация

```bash
# Полный сброс (удалит все данные!)
docker compose down -v
docker compose up -d --build
docker compose exec app alembic upgrade head
```

---

## Чеклист перед продакшеном

- [ ] `SECRET_KEY` — уникальный, 64+ символов (`openssl rand -hex 32`)
- [ ] `POSTGRES_PASSWORD` — сложный пароль
- [ ] `DEBUG=false`
- [ ] `CORS_ORIGINS` — только ваш домен
- [ ] SSL-сертификат (Let's Encrypt)
- [ ] Firewall (только 22, 80, 443)
- [ ] Nginx reverse proxy
- [ ] Backup cron настроен
- [ ] Мониторинг (Flower, health endpoint)
- [ ] `.env` не в Git (проверьте `.gitignore`)
- [ ] LLM API-ключи заполнены
- [ ] `alembic upgrade head` выполнен
- [ ] `docker compose ps` — все сервисы healthy

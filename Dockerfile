# ============================================
# ResumeCraft — Multi-stage Dockerfile
# ============================================
FROM python:3.11-slim AS base

# Переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    tesseract-ocr \
    tesseract-ocr-rus \
    && rm -rf /var/lib/apt/lists/*

# ============================================
# Builder stage — установка зависимостей
# ============================================
FROM base AS builder

COPY requirements.txt .
# PyTorch CPU-only (без CUDA ~2.5 ГБ экономии) — GPU не используется в production
RUN pip install --prefix=/install torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --prefix=/install -r requirements.txt

# ============================================
# Production stage
# ============================================
FROM base AS production

# Копирование установленных пакетов
COPY --from=builder /install /usr/local

# Создание non-root пользователя
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

# Копирование исходного кода
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Создание директории для загрузок
RUN mkdir -p /data/uploads && chown -R appuser:appuser /data /app

# Переход на non-root пользователя
USER appuser

# Порт
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Запуск
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--app-dir", "src"]

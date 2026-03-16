# ============================================
# ResumeCraft — Multi-stage Dockerfile
# ============================================
FROM mirror.gcr.io/library/python:3.14-slim AS base

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
# PyTorch CPU-only: --extra-index-url обеспечивает CPU-версию torch
# вместо CUDA-версии (~300 МБ vs ~3 ГБ). Одна RUN для минимизации слоёв.
RUN pip install --prefix=/install \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt \
    && find /install -type d -name "tests" -exec rm -rf {} + 2>/dev/null; \
    find /install -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; \
    find /install -name "*.pyc" -delete 2>/dev/null; true

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

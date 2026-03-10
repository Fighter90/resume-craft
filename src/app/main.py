"""FastAPI application factory — точка входа."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.admin.router import router as admin_router
from app.auth.router import router as auth_router
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.limiter import limiter
from app.core.seed import seed_test_user
from app.export.router import router as export_router
from app.ml.router import router as models_router
from app.resumes.router import router as resumes_router
from app.rewriter.router import router as rewrite_router
from app.settings.router import router as settings_router
from app.vacancies.router import router as vacancies_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup / shutdown lifecycle."""
    logger.info('Starting ResumeCraft API...')
    # Сидирование тестового пользователя (development)
    settings = get_settings()
    if not settings.is_production:
        try:
            await seed_test_user()
        except Exception:
            logger.warning('Seed skipped (DB may not be ready)', exc_info=True)
    yield
    logger.info('Shutting down ResumeCraft API...')


def create_app() -> FastAPI:
    """Фабрика FastAPI-приложения."""
    settings = get_settings()

    # SEC-003/LIVE-011: Отключаем Swagger/ReDoc/OpenAPI в production
    docs_url = '/docs' if not settings.is_production else None
    redoc_url = '/redoc' if not settings.is_production else None
    openapi_url = '/openapi.json' if not settings.is_production else None

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description='AI-реврайтер резюме для российского рынка труда',
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
        lifespan=lifespan,
    )

    # --- Rate Limiting (SEC-005/ARCH-010/LIVE-012) ---
    if settings.environment in ('testing', 'test'):
        limiter.enabled = False
    storage_uri = (
        'memory://'
        if settings.environment in ('testing', 'test')
        else (settings.redis_url or 'memory://')
    )
    limiter._storage_uri = storage_uri
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # --- Middleware ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
        allow_headers=['Authorization', 'Content-Type', 'Accept', 'X-Request-ID'],
    )

    # --- Exception Handlers ---
    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        """Обработчик кастомных ошибок → JSON."""
        content: dict[str, str | None] = {
            'error': exc.error_code,
            'message': exc.message,
        }
        if exc.detail:
            content['detail'] = exc.detail
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(Exception)
    async def general_error_handler(_request: Request, exc: Exception) -> JSONResponse:
        """Обработчик необработанных исключений → 500."""
        logger.exception('Unhandled exception: %s', exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'error': 'INTERNAL_ERROR',
                'message': 'Внутренняя ошибка сервера',
            },
        )

    # --- Routers ---
    api_prefix = settings.api_v1_prefix

    app.include_router(auth_router, prefix=api_prefix)
    app.include_router(resumes_router, prefix=api_prefix)
    app.include_router(vacancies_router, prefix=api_prefix)
    app.include_router(rewrite_router, prefix=api_prefix)
    app.include_router(export_router, prefix=api_prefix)
    app.include_router(models_router, prefix=api_prefix)
    app.include_router(settings_router, prefix=api_prefix)
    app.include_router(admin_router, prefix=api_prefix)

    # --- Static files: uploads (avatars, etc.) ---
    from pathlib import Path

    from starlette.staticfiles import StaticFiles

    uploads_dir = Path(settings.upload_dir).resolve()
    uploads_dir.mkdir(parents=True, exist_ok=True)
    app.mount(f'{api_prefix}/uploads', StaticFiles(directory=str(uploads_dir)), name='uploads')

    # --- Health Check (API-005/LIVE-015: доступен и с префиксом и без) ---
    @app.get('/health', tags=['system'], summary='Health Check')
    @app.get(f'{settings.api_v1_prefix}/health', tags=['system'], include_in_schema=False)
    async def health() -> dict[str, str]:
        return {'status': 'healthy', 'version': settings.app_version}

    # --- Logging ---
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    )

    return app


# Экземпляр приложения (для uvicorn)
app = create_app()

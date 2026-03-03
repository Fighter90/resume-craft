"""FastAPI application factory — точка входа."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.auth.router import router as auth_router
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.export.router import router as export_router
from app.resumes.router import router as resumes_router
from app.rewriter.router import router as rewrite_router
from app.vacancies.router import router as vacancies_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup / shutdown lifecycle."""
    logger.info('Starting ResumeCraft API...')
    yield
    logger.info('Shutting down ResumeCraft API...')


def create_app() -> FastAPI:
    """Фабрика FastAPI-приложения."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description='AI-реврайтер резюме для российского рынка труда',
        docs_url='/docs',
        redoc_url='/redoc',
        lifespan=lifespan,
    )

    # --- Middleware ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
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

    # --- Health Check ---
    @app.get('/health', tags=['system'], summary='Health Check')
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

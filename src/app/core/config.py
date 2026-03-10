"""Конфигурация приложения через pydantic-settings."""

from __future__ import annotations

import logging
from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Настройки приложения. Все секреты загружаются из .env."""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )

    # --- Общие ---
    environment: str = 'development'
    debug: bool = False
    log_level: str = 'INFO'
    app_name: str = 'ResumeCraft'
    app_version: str = '1.21.0'
    api_v1_prefix: str = '/api/v1'

    # --- Database ---
    database_url: str = 'postgresql+asyncpg://resumecraft:devpassword@localhost:5432/resumecraft'
    database_echo: bool = False

    # --- Redis ---
    redis_url: str = 'redis://localhost:6379/0'

    # --- RabbitMQ / Celery ---
    celery_broker_url: str = 'amqp://guest:guest@localhost:5672//'
    celery_result_backend: str = 'redis://localhost:6379/1'

    # --- Auth / Security ---
    secret_key: str  # ОБЯЗАТЕЛЬНО из .env — нет default!
    jwt_algorithm: str = 'HS256'
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    # --- CORS ---
    cors_origins: list[str] = Field(
        default=['http://localhost:3000', 'http://localhost:8000'],
    )

    # --- LLM ---
    gigachat_credentials: str = ''
    gigachat_scope: str = 'GIGACHAT_API_PERS'
    openai_api_key: str = ''
    openrouter_api_key: str = ''
    anthropic_api_key: str = ''
    groq_api_key: str = ''

    # --- hh.ru ---
    hh_user_agent: str = 'ResumeCraft/2.0 (contact@resumecraft.ru)'

    # --- File Storage ---
    upload_dir: str = './uploads'
    max_file_size_mb: int = 10

    # --- QA/Admin ---
    qa_admin_api_key: str = ''

    @property
    def max_file_size_bytes(self) -> int:
        """Максимальный размер файла в байтах."""
        return self.max_file_size_mb * 1024 * 1024

    @property
    def is_production(self) -> bool:
        """Проверка production-окружения."""
        return self.environment == 'production'

    # SEC-002: Валидация SECRET_KEY при запуске
    @model_validator(mode='after')
    def validate_secret_key(self) -> Settings:
        """Отказ запуска если SECRET_KEY содержит placeholder-значение."""
        weak_markers = ('change-me', 'change_me', 'placeholder', 'CHANGE', 'super-secret')
        if any(marker in self.secret_key.lower() for marker in weak_markers):
            if self.is_production:
                msg = (
                    'SECRET_KEY содержит placeholder-значение! '
                    'Сгенерируйте: python -c "import secrets; print(secrets.token_hex(64))"'
                )
                raise ValueError(msg)
            logger.warning(
                'SECRET_KEY содержит placeholder-значение. Не используйте его в production!',
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Фабрика настроек (кэшированная через lru_cache)."""
    return Settings()

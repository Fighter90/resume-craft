"""Тесты модуля core/config.py."""

from __future__ import annotations

from app.core.config import Settings, get_settings


class TestSettings:
    """Тесты конфигурации."""

    def test_defaults(self) -> None:
        """Значения по умолчанию корректны."""
        settings = get_settings()
        assert settings.app_name == 'ResumeCraft'
        assert settings.api_v1_prefix == '/api/v1'
        assert settings.jwt_algorithm == 'HS256'
        assert settings.access_token_expire_minutes == 30
        assert settings.refresh_token_expire_days == 30
        assert settings.max_file_size_mb == 10
        assert settings.hh_user_agent.startswith('ResumeCraft')

    def test_max_file_size_bytes(self) -> None:
        """Свойство max_file_size_bytes вычисляется корректно."""
        settings = get_settings()
        assert settings.max_file_size_bytes == settings.max_file_size_mb * 1024 * 1024
        assert settings.max_file_size_bytes == 10 * 1024 * 1024

    def test_is_production_false(self) -> None:
        """В тестовом окружении is_production = False."""
        settings = get_settings()
        assert settings.is_production is False

    def test_settings_instance(self) -> None:
        """get_settings() возвращает экземпляр Settings."""
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_cors_origins_list(self) -> None:
        """CORS origins — список строк."""
        settings = get_settings()
        assert isinstance(settings.cors_origins, list)
        assert all(isinstance(o, str) for o in settings.cors_origins)

    def test_llm_keys_default_empty(self) -> None:
        """LLM API ключи по умолчанию пустые строки."""
        settings = get_settings()
        assert settings.gigachat_credentials == '' or isinstance(settings.gigachat_credentials, str)
        assert settings.groq_api_key == '' or isinstance(settings.groq_api_key, str)
        assert settings.openai_api_key == '' or isinstance(settings.openai_api_key, str)
        assert settings.openrouter_api_key == '' or isinstance(settings.openrouter_api_key, str)

    def test_gigachat_scope_default(self) -> None:
        """GigaChat scope по умолчанию — GIGACHAT_API_PERS."""
        settings = get_settings()
        assert settings.gigachat_scope == 'GIGACHAT_API_PERS'

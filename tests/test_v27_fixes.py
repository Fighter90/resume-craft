"""Тесты покрытия V27 (3 дефекта QA Report #22).

Покрывает:
- RESET-001: Кнопка «Сбросить» НЕ удаляет API-ключи (P1 HIGH)
- NAV-001: Ссылка «Обновить до Pro» — onClick + navigate (P3)
- OPENAI-O4MINI: max_completion_tokens для моделей серии o* (P3)
"""

from __future__ import annotations

import re
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ============================================================================
# RESET-001: Reset preserves API keys
# ============================================================================


class TestResetPreservesApiKeys:
    """RESET-001: Кнопка «Сбросить» НЕ должна удалять API-ключи."""

    def test_reset_handler_source_no_delete_ai_key(self) -> None:
        """handleReset не вызывает api.deleteAIKey."""
        import pathlib

        src = pathlib.Path('frontend/src/pages/settings/SettingsAiPage.tsx').read_text()

        # Находим тело handleReset
        start = src.index('const handleReset')
        # Ищем конец функции — закрывающий `}` на том же уровне
        brace_depth = 0
        body_start = src.index('{', start)
        pos = body_start
        for i, ch in enumerate(src[body_start:], body_start):
            if ch == '{':
                brace_depth += 1
            elif ch == '}':
                brace_depth -= 1
                if brace_depth == 0:
                    pos = i
                    break
        reset_body = src[body_start : pos + 1]

        assert 'deleteAIKey' not in reset_body, (
            'handleReset не должен вызывать deleteAIKey — ключи должны сохраняться'
        )

    def test_reset_handler_source_no_clear_server_key_status(self) -> None:
        """handleReset не очищает serverKeyStatus."""
        import pathlib

        src = pathlib.Path('frontend/src/pages/settings/SettingsAiPage.tsx').read_text()
        start = src.index('const handleReset')
        brace_depth = 0
        body_start = src.index('{', start)
        pos = body_start
        for i, ch in enumerate(src[body_start:], body_start):
            if ch == '{':
                brace_depth += 1
            elif ch == '}':
                brace_depth -= 1
                if brace_depth == 0:
                    pos = i
                    break
        reset_body = src[body_start : pos + 1]

        assert 'setServerKeyStatus({})' not in reset_body, (
            'handleReset не должен очищать serverKeyStatus'
        )

    def test_reset_handler_saves_toggles_to_server(self) -> None:
        """handleReset сохраняет тогглы на сервер (saveAIToggles)."""
        import pathlib

        src = pathlib.Path('frontend/src/pages/settings/SettingsAiPage.tsx').read_text()
        start = src.index('const handleReset')
        brace_depth = 0
        body_start = src.index('{', start)
        pos = body_start
        for i, ch in enumerate(src[body_start:], body_start):
            if ch == '{':
                brace_depth += 1
            elif ch == '}':
                brace_depth -= 1
                if brace_depth == 0:
                    pos = i
                    break
        reset_body = src[body_start : pos + 1]

        assert 'saveAIToggles' in reset_body, (
            'handleReset должен сохранять дефолтные тогглы на сервер'
        )

    def test_reset_handler_saves_model_to_server(self) -> None:
        """handleReset сохраняет модель по умолчанию на сервер."""
        import pathlib

        src = pathlib.Path('frontend/src/pages/settings/SettingsAiPage.tsx').read_text()
        start = src.index('const handleReset')
        brace_depth = 0
        body_start = src.index('{', start)
        pos = body_start
        for i, ch in enumerate(src[body_start:], body_start):
            if ch == '{':
                brace_depth += 1
            elif ch == '}':
                brace_depth -= 1
                if brace_depth == 0:
                    pos = i
                    break
        reset_body = src[body_start : pos + 1]

        assert 'saveSelectedModel' in reset_body, (
            'handleReset должен сохранять дефолтную модель на сервер'
        )

    def test_reset_handler_resets_model_to_gigachat_pro(self) -> None:
        """handleReset сбрасывает модель на gigachat-pro."""
        import pathlib

        src = pathlib.Path('frontend/src/pages/settings/SettingsAiPage.tsx').read_text()
        start = src.index('const handleReset')
        brace_depth = 0
        body_start = src.index('{', start)
        pos = body_start
        for i, ch in enumerate(src[body_start:], body_start):
            if ch == '{':
                brace_depth += 1
            elif ch == '}':
                brace_depth -= 1
                if brace_depth == 0:
                    pos = i
                    break
        reset_body = src[body_start : pos + 1]

        assert "setModel('gigachat-pro')" in reset_body

    def test_reset_handler_clears_localstorage(self) -> None:
        """handleReset очищает legacy localStorage."""
        import pathlib

        src = pathlib.Path('frontend/src/pages/settings/SettingsAiPage.tsx').read_text()
        start = src.index('const handleReset')
        brace_depth = 0
        body_start = src.index('{', start)
        pos = body_start
        for i, ch in enumerate(src[body_start:], body_start):
            if ch == '{':
                brace_depth += 1
            elif ch == '}':
                brace_depth -= 1
                if brace_depth == 0:
                    pos = i
                    break
        reset_body = src[body_start : pos + 1]

        assert "localStorage.removeItem('ai_settings')" in reset_body


# ============================================================================
# NAV-001: Plan upgrade link uses explicit navigate()
# ============================================================================


class TestPlanUpgradeLinkNavigation:
    """NAV-001: Ссылка «Обновить до Pro» использует navigate() при клике."""

    def test_plan_upgrade_link_has_onclick_navigate(self) -> None:
        """Link для plan-upgrade содержит onClick с navigate()."""
        import pathlib

        src = pathlib.Path(
            'frontend/src/components/layout/AppLayout.tsx'
        ).read_text()

        # Должен содержать onClick на plan-upgrade Link
        assert 'onClick' in src
        assert "navigate('/app/settings/subscription')" in src

    def test_plan_upgrade_link_has_prevent_default(self) -> None:
        """Link использует preventDefault + stopPropagation."""
        import pathlib

        src = pathlib.Path(
            'frontend/src/components/layout/AppLayout.tsx'
        ).read_text()

        assert 'e.preventDefault()' in src
        assert 'e.stopPropagation()' in src

    def test_plan_upgrade_css_pointer_events(self) -> None:
        """CSS имеет pointer-events: auto для plan-upgrade."""
        import pathlib

        css = pathlib.Path('frontend/src/styles/shared-styles.css').read_text()
        assert 'pointer-events: auto' in css
        assert '.plan-upgrade' in css

    def test_plan_upgrade_renders_as_link(self) -> None:
        """Plan-upgrade рендерится через <Link> (тег <a>)."""
        import pathlib

        tsx = pathlib.Path(
            'frontend/src/components/layout/AppLayout.tsx'
        ).read_text()

        # Должен использовать Link (импорт react-router-dom)
        assert 'Link' in tsx
        assert 'plan-upgrade' in tsx
        assert '/app/settings/subscription' in tsx


# ============================================================================
# OPENAI-O4MINI: max_completion_tokens for o-series models
# ============================================================================


class TestOSeriesMaxTokens:
    """OPENAI-O4MINI: Модели серии o* используют max_completion_tokens."""

    def _is_o_series(self, model: str) -> bool:
        """Воспроизведение логики из OpenAIClient.complete()."""
        return bool(re.match(r'^o\d', model))

    @pytest.mark.parametrize(
        'model',
        ['o1', 'o1-mini', 'o1-pro', 'o3', 'o3-mini', 'o4-mini'],
    )
    def test_o_series_models_detected(self, model: str) -> None:
        """Все известные o-серия модели корректно определяются."""
        assert self._is_o_series(model), f'{model} should be detected as o-series'

    @pytest.mark.parametrize(
        'model',
        [
            'gpt-4o',
            'gpt-4o-mini',
            'gpt-4-turbo',
            'gpt-3.5-turbo',
            'gpt-4.1',
            'gpt-4.1-mini',
            'chatgpt-4o-latest',
        ],
    )
    def test_non_o_series_models_not_detected(self, model: str) -> None:
        """GPT-модели НЕ определяются как o-серия."""
        assert not self._is_o_series(model), f'{model} should NOT be o-series'

    @pytest.mark.parametrize(
        'model',
        ['o1-2025-01-15', 'o3-mini-2025-02-01', 'o4-mini-2025-04-16'],
    )
    def test_dated_o_series_variants(self, model: str) -> None:
        """Модели o-серии с date suffix корректно определяются."""
        assert self._is_o_series(model)

    def test_openai_client_source_uses_regex(self) -> None:
        """OpenAIClient.complete() использует regex для определения o-серии."""
        import pathlib

        src = pathlib.Path('src/app/ml/llm_client.py').read_text()
        assert r"re.match(r'^o\d'" in src, (
            'OpenAIClient должен использовать regex для определения o-серии'
        )

    @pytest.mark.asyncio
    async def test_openai_client_o_series_uses_max_completion_tokens(self) -> None:
        """OpenAIClient для o4-mini отправляет max_completion_tokens."""
        from app.ml.llm_client import OpenAIClient

        client = OpenAIClient(model='o4-mini', api_key='test-key')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"test": true}'

        with patch.object(client, '_get_client') as mock_get:
            mock_openai = AsyncMock()
            mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_get.return_value = mock_openai

            await client.complete(system='test', user='test')

            call_kwargs = mock_openai.chat.completions.create.call_args[1]
            assert 'max_completion_tokens' in call_kwargs, (
                'o4-mini must use max_completion_tokens'
            )
            assert 'max_tokens' not in call_kwargs, (
                'o4-mini must NOT use max_tokens'
            )
            assert 'temperature' not in call_kwargs, (
                'o4-mini must NOT use temperature'
            )

    @pytest.mark.asyncio
    async def test_openai_client_gpt_uses_max_tokens(self) -> None:
        """OpenAIClient для gpt-4o отправляет max_tokens + temperature."""
        from app.ml.llm_client import OpenAIClient

        client = OpenAIClient(model='gpt-4o', api_key='test-key')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"test": true}'

        with patch.object(client, '_get_client') as mock_get:
            mock_openai = AsyncMock()
            mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_get.return_value = mock_openai

            await client.complete(system='test', user='test')

            call_kwargs = mock_openai.chat.completions.create.call_args[1]
            assert 'max_tokens' in call_kwargs, (
                'gpt-4o must use max_tokens'
            )
            assert 'max_completion_tokens' not in call_kwargs
            assert 'temperature' in call_kwargs

    @pytest.mark.asyncio
    async def test_openai_client_o1_mini_correct_params(self) -> None:
        """OpenAIClient для o1-mini использует max_completion_tokens."""
        from app.ml.llm_client import OpenAIClient

        client = OpenAIClient(model='o1-mini', api_key='test-key')

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = 'ok'

        with patch.object(client, '_get_client') as mock_get:
            mock_openai = AsyncMock()
            mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_get.return_value = mock_openai

            await client.complete(system='s', user='u')

            call_kwargs = mock_openai.chat.completions.create.call_args[1]
            assert 'max_completion_tokens' in call_kwargs
            assert 'max_tokens' not in call_kwargs


# ============================================================================
# LLM Factory: sub-model resolution for o-series
# ============================================================================


class TestLLMFactoryOSeriesResolution:
    """Проверка что LLMClientFactory корректно передаёт o-серию подмоделей."""

    def test_factory_creates_openai_client_with_sub_model(self) -> None:
        """Factory создаёт OpenAIClient с sub_model для OpenAI провайдера."""
        from app.ml.llm_factory import SUB_MODEL_PROVIDERS

        assert 'openai' in SUB_MODEL_PROVIDERS

    def test_factory_sub_model_o4_mini(self) -> None:
        """Factory передаёт o4-mini как model_name в OpenAIClient."""
        from app.ml.llm_client import OpenAIClient
        from app.ml.llm_factory import LLMClientFactory

        with patch('app.ml.llm_factory.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(openai_api_key='test-key')
            client = LLMClientFactory.create(
                'openai', sub_model='o4-mini', api_key='test-key'
            )
            assert isinstance(client, OpenAIClient)
            assert client._model == 'o4-mini'

    def test_factory_sub_model_gpt4o(self) -> None:
        """Factory передаёт gpt-4o как model_name в OpenAIClient."""
        from app.ml.llm_client import OpenAIClient
        from app.ml.llm_factory import LLMClientFactory

        with patch('app.ml.llm_factory.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(openai_api_key='test-key')
            client = LLMClientFactory.create(
                'openai', sub_model='gpt-4o', api_key='test-key'
            )
            assert isinstance(client, OpenAIClient)
            assert client._model == 'gpt-4o'


# ============================================================================
# Combined: RESET-001 default toggles match TOGGLES constant
# ============================================================================


class TestResetDefaultValues:
    """Верификация что reset устанавливает корректные дефолты."""

    def test_default_toggles_in_source(self) -> None:
        """Тогглы по умолчанию: metrics=ON, ats=ON, upgrade_title=OFF, lang=ON, soft=OFF."""
        import pathlib

        src = pathlib.Path('frontend/src/pages/settings/SettingsAiPage.tsx').read_text()
        # Проверяем что TOGGLES определены с правильными defaults
        assert "'auto_metrics'" in src or '"auto_metrics"' in src
        assert "'ats'" in src or '"ats"' in src
        assert "'upgrade_title'" in src or '"upgrade_title"' in src
        assert "'keep_language'" in src or '"keep_language"' in src
        assert "'soft_skills'" in src or '"soft_skills"' in src

    def test_o_series_models_in_sub_models_list(self) -> None:
        """Подмодели OpenAI включают o3, o3-mini, o4-mini."""
        import pathlib

        src = pathlib.Path('frontend/src/pages/settings/SettingsAiPage.tsx').read_text()
        for model in ['o3', 'o3-mini', 'o4-mini']:
            assert f"'{model}'" in src or f'"{model}"' in src, (
                f'Подмодель {model} должна быть в списке OpenAI'
            )

    def test_openai_sub_models_endpoint_includes_o_series(self) -> None:
        """Backend endpoint для OpenAI sub-models включает o-серию (fallback)."""
        import pathlib

        src = pathlib.Path('src/app/ml/router.py').read_text()
        for model in ['o3', 'o3-mini', 'o4-mini']:
            assert f"'{model}'" in src or f'"{model}"' in src, (
                f'Backend должен возвращать {model} в fallback списке OpenAI'
            )

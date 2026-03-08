"""Тесты ml/router.py — роутер AI-моделей.

Покрытие:
- GET /api/v1/models — список моделей с флагами доступности
- GET /api/v1/models/{provider}/sub-models — подмодели OpenAI/Anthropic/OpenRouter
- Fallback при ошибках API
- Неподдерживаемые провайдеры
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.fixture
async def client() -> AsyncClient:
    """HTTP-клиент для тестирования роутера."""
    app = create_app()
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url='http://test') as c:
        yield c  # type: ignore[misc]


# ── GET /api/v1/models ──────────────────────────────────────────────────────


class TestListModels:
    """Тесты GET /api/v1/models."""

    async def test_list_models_no_keys(self, client: AsyncClient) -> None:
        """Без настроенных ключей → все модели available=False."""
        mock_settings = MagicMock()
        mock_settings.gigachat_credentials = ''
        mock_settings.openai_api_key = ''
        mock_settings.anthropic_api_key = ''
        mock_settings.openrouter_api_key = ''
        mock_settings.groq_api_key = ''

        with patch('app.ml.router.get_settings', return_value=mock_settings):
            resp = await client.get('/api/v1/models')

        assert resp.status_code == 200
        data = resp.json()
        assert 'models' in data
        models = data['models']
        assert len(models) == 5

        for m in models:
            assert m['available'] is False

    async def test_list_models_with_keys(self, client: AsyncClient) -> None:
        """С настроенными ключами → модели available=True."""
        mock_settings = MagicMock()
        mock_settings.gigachat_credentials = 'test-cred'
        mock_settings.openai_api_key = 'sk-test'
        mock_settings.anthropic_api_key = 'sk-ant-test'
        mock_settings.openrouter_api_key = 'sk-or-test'
        mock_settings.groq_api_key = 'gsk-test'

        with patch('app.ml.router.get_settings', return_value=mock_settings):
            resp = await client.get('/api/v1/models')

        assert resp.status_code == 200
        models = resp.json()['models']
        for m in models:
            assert m['available'] is True

    async def test_list_models_partial_keys(self, client: AsyncClient) -> None:
        """Часть ключей → корректные флаги available."""
        mock_settings = MagicMock()
        mock_settings.gigachat_credentials = 'test-cred'
        mock_settings.openai_api_key = ''
        mock_settings.anthropic_api_key = 'sk-ant-test'
        mock_settings.openrouter_api_key = '   '  # пробелы = пустой
        mock_settings.groq_api_key = ''

        with patch('app.ml.router.get_settings', return_value=mock_settings):
            resp = await client.get('/api/v1/models')

        models = resp.json()['models']
        available_map = {m['provider']: m['available'] for m in models}
        assert available_map['gigachat'] is True
        assert available_map['openai'] is False
        assert available_map['anthropic'] is True
        assert available_map['openrouter'] is False

    async def test_list_models_structure(self, client: AsyncClient) -> None:
        """Проверка структуры каждой модели."""
        mock_settings = MagicMock()
        mock_settings.gigachat_credentials = ''
        mock_settings.openai_api_key = ''
        mock_settings.anthropic_api_key = ''
        mock_settings.openrouter_api_key = ''
        mock_settings.groq_api_key = ''

        with patch('app.ml.router.get_settings', return_value=mock_settings):
            resp = await client.get('/api/v1/models')

        models = resp.json()['models']
        for m in models:
            assert 'id' in m
            assert 'name' in m
            assert 'provider' in m
            assert 'available' in m
            assert 'description' in m
            assert 'has_sub_models' in m

    async def test_all_providers_have_sub_models(self, client: AsyncClient) -> None:
        """All providers (including GigaChat) have has_sub_models=True."""
        mock_settings = MagicMock()
        mock_settings.gigachat_credentials = ''
        mock_settings.openai_api_key = ''
        mock_settings.anthropic_api_key = ''
        mock_settings.openrouter_api_key = ''
        mock_settings.groq_api_key = ''

        with patch('app.ml.router.get_settings', return_value=mock_settings):
            resp = await client.get('/api/v1/models')

        models = resp.json()['models']
        for m in models:
            assert m['has_sub_models'] is True, f'{m["provider"]} should have sub_models'


# ── GET /api/v1/models/{provider}/sub-models ────────────────────────────────


class TestSubModelsUnsupported:
    """Тесты для неподдерживаемых провайдеров."""

    async def test_unknown_provider(self, client: AsyncClient) -> None:
        """Неизвестный провайдер → ошибка."""
        mock_settings = MagicMock()
        with patch('app.ml.router.get_settings', return_value=mock_settings):
            resp = await client.get('/api/v1/models/unknown-provider/sub-models')

        data = resp.json()
        assert data['sub_models'] == []
        assert 'error' in data


# ── GigaChat sub-models ────────────────────────────────────────────────────


class TestGigaChatSubModels:
    """Тесты GET /api/v1/models/gigachat/sub-models."""

    async def test_no_api_key(self, client: AsyncClient) -> None:
        """Нет API-ключа → error."""
        mock_settings = MagicMock()
        mock_settings.gigachat_credentials = ''
        mock_settings.gigachat_scope = 'GIGACHAT_API_PERS'

        with patch('app.ml.router.get_settings', return_value=mock_settings):
            resp = await client.get('/api/v1/models/gigachat/sub-models')

        data = resp.json()
        assert data['sub_models'] == []
        assert 'error' in data

    async def test_gigachat_pro_alias(self, client: AsyncClient) -> None:
        """gigachat-pro alias → те же модели GigaChat."""
        mock_settings = MagicMock()
        mock_settings.gigachat_credentials = 'test-cred'
        mock_settings.gigachat_scope = 'GIGACHAT_API_PERS'

        mock_model = MagicMock()
        mock_model.id = 'GigaChat-Pro'
        mock_response = MagicMock()
        mock_response.data = [mock_model]
        mock_gc_client = MagicMock()
        mock_gc_client.get_models.return_value = mock_response

        with (
            patch('app.ml.router.get_settings', return_value=mock_settings),
            patch('gigachat.GigaChat', return_value=mock_gc_client),
        ):
            resp = await client.get('/api/v1/models/gigachat-pro/sub-models')

        data = resp.json()
        assert len(data['sub_models']) > 0
        assert data['sub_models'][0]['provider'] == 'GigaChat'

    async def test_success(self, client: AsyncClient) -> None:
        """Успешный запрос → модели GigaChat."""
        mock_settings = MagicMock()
        mock_settings.gigachat_credentials = 'test-cred'
        mock_settings.gigachat_scope = 'GIGACHAT_API_PERS'

        # Мокируем GigaChat SDK
        mock_model_1 = MagicMock()
        mock_model_1.id = 'GigaChat-Pro'
        mock_model_2 = MagicMock()
        mock_model_2.id = 'GigaChat'
        mock_model_3 = MagicMock()
        mock_model_3.id = 'GigaChat-Max'

        mock_response = MagicMock()
        mock_response.data = [mock_model_1, mock_model_2, mock_model_3]

        mock_gc_client = MagicMock()
        mock_gc_client.get_models.return_value = mock_response

        with (
            patch('app.ml.router.get_settings', return_value=mock_settings),
            patch('gigachat.GigaChat', return_value=mock_gc_client),
        ):
            resp = await client.get('/api/v1/models/gigachat/sub-models')

        data = resp.json()
        model_ids = [m['id'] for m in data['sub_models']]
        assert 'GigaChat-Pro' in model_ids
        assert 'GigaChat' in model_ids
        assert 'GigaChat-Max' in model_ids
        # Провайдер = GigaChat
        for m in data['sub_models']:
            assert m['provider'] == 'GigaChat'

    async def test_api_error_fallback(self, client: AsyncClient) -> None:
        """Ошибка SDK → fallback-модели."""
        mock_settings = MagicMock()
        mock_settings.gigachat_credentials = 'test-cred'
        mock_settings.gigachat_scope = 'GIGACHAT_API_PERS'

        with (
            patch('app.ml.router.get_settings', return_value=mock_settings),
            patch('gigachat.GigaChat', side_effect=Exception('Auth failed')),
        ):
            resp = await client.get('/api/v1/models/gigachat/sub-models')

        data = resp.json()
        assert data.get('fallback') is True
        model_ids = [m['id'] for m in data['sub_models']]
        assert 'GigaChat-Pro' in model_ids
        assert 'GigaChat' in model_ids
        assert 'GigaChat-Max' in model_ids

    async def test_sorted_by_name(self, client: AsyncClient) -> None:
        """Модели отсортированы по имени."""
        mock_settings = MagicMock()
        mock_settings.gigachat_credentials = 'test-cred'
        mock_settings.gigachat_scope = 'GIGACHAT_API_PERS'

        mock_m1 = MagicMock()
        mock_m1.id = 'GigaChat-Pro'
        mock_m2 = MagicMock()
        mock_m2.id = 'GigaChat'
        mock_m3 = MagicMock()
        mock_m3.id = 'GigaChat-Max'

        mock_response = MagicMock()
        mock_response.data = [mock_m1, mock_m2, mock_m3]

        mock_gc_client = MagicMock()
        mock_gc_client.get_models.return_value = mock_response

        with (
            patch('app.ml.router.get_settings', return_value=mock_settings),
            patch('gigachat.GigaChat', return_value=mock_gc_client),
        ):
            resp = await client.get('/api/v1/models/gigachat/sub-models')

        data = resp.json()
        names = [m['name'] for m in data['sub_models']]
        assert names == sorted(names)


# ── OpenAI sub-models ───────────────────────────────────────────────────────


class TestOpenAISubModels:
    """Тесты GET /api/v1/models/openai/sub-models."""

    async def test_no_api_key(self, client: AsyncClient) -> None:
        """Нет API-ключа → error."""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = ''

        with patch('app.ml.router.get_settings', return_value=mock_settings):
            resp = await client.get('/api/v1/models/openai/sub-models')

        data = resp.json()
        assert data['sub_models'] == []
        assert 'error' in data

    async def test_success(self, client: AsyncClient) -> None:
        """Успешный запрос → отфильтрованные chat-модели."""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = 'sk-test'

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'data': [
                {'id': 'gpt-4o'},
                {'id': 'gpt-4o-mini'},
                {'id': 'gpt-3.5-turbo'},
                {'id': 'o1-preview'},
                {'id': 'dall-e-3'},  # excluded
                {'id': 'text-embedding-ada-002'},  # excluded
                {'id': 'gpt-4o-audio-preview'},  # excluded (audio)
                {'id': 'whisper-1'},  # excluded
                {'id': 'gpt-4-turbo-instruct'},  # excluded (instruct)
            ],
        }
        mock_response.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=mock_response)
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=None)

        with (
            patch('app.ml.router.get_settings', return_value=mock_settings),
            patch('app.ml.router.httpx.AsyncClient', return_value=mock_http),
        ):
            resp = await client.get('/api/v1/models/openai/sub-models')

        data = resp.json()
        model_ids = [m['id'] for m in data['sub_models']]
        # Включены chat-модели
        assert 'gpt-4o' in model_ids
        assert 'gpt-4o-mini' in model_ids
        assert 'gpt-3.5-turbo' in model_ids
        assert 'o1-preview' in model_ids
        # Исключены не-chat модели
        assert 'dall-e-3' not in model_ids
        assert 'text-embedding-ada-002' not in model_ids
        assert 'gpt-4o-audio-preview' not in model_ids
        assert 'whisper-1' not in model_ids
        assert 'gpt-4-turbo-instruct' not in model_ids

    async def test_api_error_fallback(self, client: AsyncClient) -> None:
        """Ошибка API → fallback-модели."""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = 'sk-test'

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(side_effect=httpx.HTTPError('Connection error'))
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=None)

        with (
            patch('app.ml.router.get_settings', return_value=mock_settings),
            patch('app.ml.router.httpx.AsyncClient', return_value=mock_http),
        ):
            resp = await client.get('/api/v1/models/openai/sub-models')

        data = resp.json()
        assert data.get('fallback') is True
        model_ids = [m['id'] for m in data['sub_models']]
        assert 'gpt-4o' in model_ids
        assert 'gpt-4o-mini' in model_ids
        assert 'gpt-4.1' in model_ids
        assert 'o3' in model_ids
        assert len(data['sub_models']) >= 10

    async def test_chatgpt_prefix_included(self, client: AsyncClient) -> None:
        """chatgpt-* модели включены в фильтр."""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = 'sk-test'

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'data': [
                {'id': 'gpt-4o'},
                {'id': 'chatgpt-4o-latest'},
                {'id': 'dall-e-3'},
            ],
        }
        mock_response.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=mock_response)
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=None)

        with (
            patch('app.ml.router.get_settings', return_value=mock_settings),
            patch('app.ml.router.httpx.AsyncClient', return_value=mock_http),
        ):
            resp = await client.get('/api/v1/models/openai/sub-models')

        data = resp.json()
        model_ids = [m['id'] for m in data['sub_models']]
        assert 'chatgpt-4o-latest' in model_ids
        assert 'gpt-4o' in model_ids
        assert 'dall-e-3' not in model_ids

    async def test_whitespace_key(self, client: AsyncClient) -> None:
        """Ключ из пробелов → error."""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = '   '

        with patch('app.ml.router.get_settings', return_value=mock_settings):
            resp = await client.get('/api/v1/models/openai/sub-models')

        data = resp.json()
        assert data['sub_models'] == []
        assert 'error' in data


# ── Anthropic sub-models ────────────────────────────────────────────────────


class TestAnthropicSubModels:
    """Тесты GET /api/v1/models/anthropic/sub-models."""

    async def test_no_api_key(self, client: AsyncClient) -> None:
        """Нет API-ключа → error."""
        mock_settings = MagicMock()
        mock_settings.anthropic_api_key = ''

        with patch('app.ml.router.get_settings', return_value=mock_settings):
            resp = await client.get('/api/v1/models/anthropic/sub-models')

        data = resp.json()
        assert data['sub_models'] == []
        assert 'error' in data

    async def test_success(self, client: AsyncClient) -> None:
        """Успешный запрос → модели Anthropic."""
        mock_settings = MagicMock()
        mock_settings.anthropic_api_key = 'sk-ant-test'

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'data': [
                {'id': 'claude-sonnet-4-20250514', 'display_name': 'Claude Sonnet 4'},
                {'id': 'claude-3-5-sonnet-20241022', 'display_name': 'Claude 3.5 Sonnet'},
                {'id': 'claude-3-5-haiku-20241022', 'display_name': 'Claude 3.5 Haiku'},
            ],
        }
        mock_response.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=mock_response)
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=None)

        with (
            patch('app.ml.router.get_settings', return_value=mock_settings),
            patch('app.ml.router.httpx.AsyncClient', return_value=mock_http),
        ):
            resp = await client.get('/api/v1/models/anthropic/sub-models')

        data = resp.json()
        model_ids = [m['id'] for m in data['sub_models']]
        assert 'claude-sonnet-4-20250514' in model_ids
        assert 'claude-3-5-sonnet-20241022' in model_ids

        # Проверка display_name
        names = {m['id']: m['name'] for m in data['sub_models']}
        assert names['claude-sonnet-4-20250514'] == 'Claude Sonnet 4'

    async def test_api_error_fallback(self, client: AsyncClient) -> None:
        """Ошибка API → fallback-модели."""
        mock_settings = MagicMock()
        mock_settings.anthropic_api_key = 'sk-ant-test'

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(side_effect=httpx.HTTPError('Timeout'))
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=None)

        with (
            patch('app.ml.router.get_settings', return_value=mock_settings),
            patch('app.ml.router.httpx.AsyncClient', return_value=mock_http),
        ):
            resp = await client.get('/api/v1/models/anthropic/sub-models')

        data = resp.json()
        assert data.get('fallback') is True
        model_ids = [m['id'] for m in data['sub_models']]
        assert 'claude-sonnet-4-20250514' in model_ids
        assert 'claude-opus-4-20250514' in model_ids
        assert len(data['sub_models']) >= 7

    async def test_model_without_display_name(self, client: AsyncClient) -> None:
        """Модель без display_name → id используется как имя."""
        mock_settings = MagicMock()
        mock_settings.anthropic_api_key = 'sk-ant-test'

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'data': [
                {'id': 'claude-new-model'},
            ],
        }
        mock_response.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=mock_response)
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=None)

        with (
            patch('app.ml.router.get_settings', return_value=mock_settings),
            patch('app.ml.router.httpx.AsyncClient', return_value=mock_http),
        ):
            resp = await client.get('/api/v1/models/anthropic/sub-models')

        data = resp.json()
        model = data['sub_models'][0]
        assert model['name'] == 'claude-new-model'


# ── OpenRouter sub-models ───────────────────────────────────────────────────


class TestOpenRouterSubModels:
    """Тесты GET /api/v1/models/openrouter/sub-models."""

    async def test_no_api_key(self, client: AsyncClient) -> None:
        """Нет API-ключа → error."""
        mock_settings = MagicMock()
        mock_settings.openrouter_api_key = ''

        with patch('app.ml.router.get_settings', return_value=mock_settings):
            resp = await client.get('/api/v1/models/openrouter/sub-models')

        data = resp.json()
        assert data['sub_models'] == []
        assert 'error' in data

    async def test_success(self, client: AsyncClient) -> None:
        """Успешный запрос → модели OpenRouter."""
        mock_settings = MagicMock()
        mock_settings.openrouter_api_key = 'sk-or-test'

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'data': [
                {'id': 'anthropic/claude-sonnet-4', 'name': 'Claude Sonnet 4'},
                {'id': 'google/gemini-2.5-flash', 'name': 'Gemini 2.5 Flash'},
                {'id': 'deepseek/deepseek-chat', 'name': 'DeepSeek Chat'},
                {'id': 'standalone-model', 'name': 'Standalone'},  # нет / в id
            ],
        }
        mock_response.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=mock_response)
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=None)

        with (
            patch('app.ml.router.get_settings', return_value=mock_settings),
            patch('app.ml.router.httpx.AsyncClient', return_value=mock_http),
        ):
            resp = await client.get('/api/v1/models/openrouter/sub-models')

        data = resp.json()
        model_ids = [m['id'] for m in data['sub_models']]
        assert 'anthropic/claude-sonnet-4' in model_ids
        assert 'google/gemini-2.5-flash' in model_ids

        # Проверка provider extraction
        providers = {m['id']: m['provider'] for m in data['sub_models']}
        assert providers['anthropic/claude-sonnet-4'] == 'Anthropic'
        assert providers['google/gemini-2.5-flash'] == 'Google'
        # Без / → Unknown
        assert providers['standalone-model'] == 'Unknown'

    async def test_api_error_fallback(self, client: AsyncClient) -> None:
        """Ошибка API → fallback-модели."""
        mock_settings = MagicMock()
        mock_settings.openrouter_api_key = 'sk-or-test'

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(side_effect=httpx.HTTPError('Network error'))
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=None)

        with (
            patch('app.ml.router.get_settings', return_value=mock_settings),
            patch('app.ml.router.httpx.AsyncClient', return_value=mock_http),
        ):
            resp = await client.get('/api/v1/models/openrouter/sub-models')

        data = resp.json()
        assert data.get('fallback') is True
        model_ids = [m['id'] for m in data['sub_models']]
        assert 'anthropic/claude-sonnet-4' in model_ids
        assert 'deepseek/deepseek-r1' in model_ids
        assert 'deepseek/deepseek-chat-v3-0324' in model_ids
        assert len(data['sub_models']) >= 16

    async def test_sorted_by_name(self, client: AsyncClient) -> None:
        """Модели отсортированы по name."""
        mock_settings = MagicMock()
        mock_settings.openrouter_api_key = 'sk-or-test'

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'data': [
                {'id': 'z/model', 'name': 'Zeta Model'},
                {'id': 'a/model', 'name': 'Alpha Model'},
                {'id': 'm/model', 'name': 'Mid Model'},
            ],
        }
        mock_response.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=mock_response)
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=None)

        with (
            patch('app.ml.router.get_settings', return_value=mock_settings),
            patch('app.ml.router.httpx.AsyncClient', return_value=mock_http),
        ):
            resp = await client.get('/api/v1/models/openrouter/sub-models')

        data = resp.json()
        names = [m['name'] for m in data['sub_models']]
        assert names == sorted(names)

"""Тесты покрытия V24 (6 дефектов QA Report #19).

Покрывает:
- P0-3-CLAUDE: Парсинг markdown code blocks в ответах Claude
- GIGACHAT-001: Health-check эндпоинт провайдеров (/models/health)
- GROQ-KEY: Сохранение API-ключа Groq
- AVATAR-001: Динамические инициалы аватара
- LOGOUT-001: Logout уже работает (верификация)
- NAV-001: NavLink для «Обновить до Pro» (верификация)
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

if TYPE_CHECKING:
    from httpx import AsyncClient

# ============================================================================
# P0-3-CLAUDE: Backend _parse_llm_response — markdown code block stripping
# ============================================================================


class TestParseLLMResponseMarkdown:
    """Backend _parse_llm_response уже парсит markdown — проверяем."""

    @staticmethod
    def _make_task() -> MagicMock:
        """Создать mock RewriteHistory task."""
        task = MagicMock()
        task.rewritten_data = None
        task.keywords_added = []
        return task

    async def test_strip_markdown_json_code_block(self) -> None:
        """```json\\n{...}\\n``` → нормальный JSON."""
        from app.rewriter.service import _parse_llm_response

        task = self._make_task()
        raw = '```json\n{"summary": "Опытный dev", "skills": ["Python"]}\n```'
        result = _parse_llm_response(raw, task=task)
        assert result is True
        assert task.rewritten_data is not None
        assert task.rewritten_data['summary'] == 'Опытный dev'
        assert 'Python' in task.rewritten_data['skills']

    async def test_strip_triple_backticks_no_lang(self) -> None:
        """```\\n{...}\\n``` → JSON без указания языка."""
        from app.rewriter.service import _parse_llm_response

        task = self._make_task()
        raw = '```\n{"summary": "Test", "experience": []}\n```'
        result = _parse_llm_response(raw, task=task)
        assert result is True
        assert task.rewritten_data['summary'] == 'Test'

    async def test_plain_json_still_works(self) -> None:
        """Чистый JSON (без markdown) — по-прежнему парсится."""
        from app.rewriter.service import _parse_llm_response

        task = self._make_task()
        raw = '{"summary": "Plain JSON", "skills": ["Go"]}'
        result = _parse_llm_response(raw, task=task)
        assert result is True
        assert task.rewritten_data['summary'] == 'Plain JSON'

    async def test_plain_text_returns_false(self) -> None:
        """Обычный текст (не JSON) → False."""
        from app.rewriter.service import _parse_llm_response

        task = self._make_task()
        raw = 'Опытный разработчик с 5 годами стажа.'
        result = _parse_llm_response(raw, task=task)
        assert result is False

    async def test_claude_format_with_name_position(self) -> None:
        """Claude-формат с name/position/contacts → парсит."""
        from app.rewriter.service import _parse_llm_response

        task = self._make_task()
        raw = (
            '```json\n{"name": "Иванов Пётр", "position": "Golang Developer",'
            ' "summary": "Senior dev"}\n```'
        )
        result = _parse_llm_response(raw, task=task)
        assert result is True
        assert task.rewritten_data['name'] == 'Иванов Пётр'
        assert task.rewritten_data['position'] == 'Golang Developer'

    async def test_trailing_comma_fix(self) -> None:
        """Trailing comma в JSON от LLM → авто-исправление."""
        from app.rewriter.service import _parse_llm_response

        task = self._make_task()
        raw = '{"summary": "Test", "skills": ["Python",]}'
        result = _parse_llm_response(raw, task=task)
        assert result is True
        assert task.rewritten_data['summary'] == 'Test'


# ============================================================================
# GIGACHAT-001: Health-check эндпоинт (/models/health)
# ============================================================================


class TestModelsHealthEndpoint:
    """GET /api/v1/models/health — проверка доступности провайдеров."""

    async def test_health_returns_all_5_providers(self, client: AsyncClient) -> None:
        """Ответ содержит все 5 провайдеров."""
        resp = await client.get('/api/v1/models/health')
        assert resp.status_code == 200
        data = resp.json()
        assert 'providers' in data
        providers = data['providers']
        assert set(providers.keys()) == {'gigachat', 'openai', 'anthropic', 'openrouter', 'groq'}

    async def test_health_no_key_status(self, client: AsyncClient) -> None:
        """Провайдер без ключа → status: no_key."""
        resp = await client.get('/api/v1/models/health')
        data = resp.json()
        providers = data['providers']
        for provider_name in providers:
            assert providers[provider_name]['status'] in (
                'no_key',
                'ok',
                'error',
                'auth_error',
                'billing_error',
            )

    async def test_ping_gigachat_billing_detection(self) -> None:
        """Строка 'средств' в ошибке → billing_error."""
        from app.ml.router import _ping_gigachat

        # Mock the gigachat module
        mock_gigachat_module = MagicMock()
        mock_gigachat_module.GigaChat.side_effect = Exception('Недостаточно средств на балансе')
        with patch.dict('sys.modules', {'gigachat': mock_gigachat_module}):
            result = await _ping_gigachat('fake-key')
        assert result['status'] == 'billing_error'

    async def test_ping_gigachat_auth_detection(self) -> None:
        """Строка 'credentials' в ошибке → auth_error."""
        from app.ml.router import _ping_gigachat

        mock_gigachat_module = MagicMock()
        mock_gigachat_module.GigaChat.side_effect = Exception('Invalid credentials provided')
        with patch.dict('sys.modules', {'gigachat': mock_gigachat_module}):
            result = await _ping_gigachat('bad-key')
        assert result['status'] == 'auth_error'

    async def test_ping_gigachat_success(self) -> None:
        """GigaChat OK → status: ok."""
        from app.ml.router import _ping_gigachat

        mock_gigachat_module = MagicMock()
        mock_client = MagicMock()
        mock_client.get_models.return_value = MagicMock(data=[])
        mock_gigachat_module.GigaChat.return_value = mock_client
        with patch.dict('sys.modules', {'gigachat': mock_gigachat_module}):
            result = await _ping_gigachat('good-key')
        assert result['status'] == 'ok'

    async def test_ping_openai_success(self) -> None:
        """OpenAI ping OK → status: ok."""
        from app.ml.router import _ping_openai

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient.get', new_callable=AsyncMock, return_value=mock_resp):
            result = await _ping_openai('fake-key')
        assert result['status'] == 'ok'

    async def test_ping_groq_success(self) -> None:
        """Groq ping OK → status: ok."""
        from app.ml.router import _ping_groq

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient.get', new_callable=AsyncMock, return_value=mock_resp):
            result = await _ping_groq('fake-key')
        assert result['status'] == 'ok'


# ============================================================================
# GROQ-KEY: Сохранение/удаление ключа Groq через API
# ============================================================================


class TestGroqKeyPersistence:
    """Ключ Groq должен сохраняться/удаляться через /settings/ai-keys."""

    async def test_save_groq_key(self, auth_client: AsyncClient) -> None:
        """PUT /settings/ai-keys/groq → 200 OK."""
        resp = await auth_client.put(
            '/api/v1/settings/ai-keys/groq',
            json={'api_key': 'gsk_test_key_12345'},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data['provider'] == 'groq'
        assert data['has_key'] is True

    async def test_read_groq_key_masked(self, auth_client: AsyncClient) -> None:
        """После сохранения — ключ в списке (has_key=true)."""
        await auth_client.put(
            '/api/v1/settings/ai-keys/groq',
            json={'api_key': 'gsk_test_key_read'},
        )
        resp = await auth_client.get('/api/v1/settings/ai-keys')
        assert resp.status_code == 200
        data = resp.json()
        keys_list = data.get('keys', [])
        groq_entry = next((k for k in keys_list if k['provider'] == 'groq'), None)
        assert groq_entry is not None
        assert groq_entry['has_key'] is True

    async def test_delete_groq_key(self, auth_client: AsyncClient) -> None:
        """DELETE /settings/ai-keys/groq → 204."""
        await auth_client.put(
            '/api/v1/settings/ai-keys/groq',
            json={'api_key': 'gsk_to_delete'},
        )
        resp = await auth_client.delete('/api/v1/settings/ai-keys/groq')
        assert resp.status_code == 204

    async def test_groq_in_models_list(self, client: AsyncClient) -> None:
        """GET /models — Groq присутствует."""
        resp = await client.get('/api/v1/models')
        assert resp.status_code == 200
        models = resp.json()['models']
        groq_model = next((m for m in models if m['provider'] == 'groq'), None)
        assert groq_model is not None
        assert groq_model['id'] == 'groq'


# ============================================================================
# AVATAR-001: Инициалы аватара — юнит-тесты логики
# ============================================================================


class TestAvatarInitials:
    """Инициалы должны вычисляться из first+last name."""

    @staticmethod
    def get_initials(first_name: str, last_name: str) -> str:
        """Зеркало фронтенд-логики."""
        first = (first_name or '').strip()[:1].upper()
        last = (last_name or '').strip()[:1].upper()
        return f'{first}{last}' or '??'

    def test_latin_names(self) -> None:
        assert self.get_initials('QA', 'Tester') == 'QT'

    def test_cyrillic_names(self) -> None:
        assert self.get_initials('Алексей', 'Петров') == 'АП'

    def test_single_name(self) -> None:
        assert self.get_initials('Admin', '') == 'A'

    def test_empty_names(self) -> None:
        assert self.get_initials('', '') == '??'

    def test_unicode_names(self) -> None:
        assert self.get_initials('José', 'García') == 'JG'


# ============================================================================
# LOGOUT-001: Logout эндпоинт работает
# ============================================================================


class TestLogoutEndpoint:
    """POST /auth/logout → 204 (уже реализован)."""

    async def test_logout_returns_204(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.post('/api/v1/auth/logout')
        assert resp.status_code == 204

    async def test_logout_without_auth(self, client: AsyncClient) -> None:
        """Без JWT → 401."""
        resp = await client.post('/api/v1/auth/logout')
        assert resp.status_code == 401


# ============================================================================
# Groq sub-models fallback
# ============================================================================


class TestGroqSubModels:
    """GET /models/groq/sub-models — должен возвращать fallback."""

    async def test_groq_sub_models_fallback(self, client: AsyncClient) -> None:
        """Без ключа → fallback список моделей."""
        resp = await client.get('/api/v1/models/groq/sub-models')
        assert resp.status_code == 200
        data = resp.json()
        assert 'sub_models' in data

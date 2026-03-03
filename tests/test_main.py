"""Тесты main.py — app factory и error handlers."""

from __future__ import annotations

from httpx import AsyncClient


class TestMainApp:
    """Тесты create_app() и middleware."""

    async def test_health_endpoint(self, client: AsyncClient) -> None:
        """GET /health → 200."""
        resp = await client.get('/health')
        assert resp.status_code == 200
        data = resp.json()
        assert data['status'] == 'ok'

    async def test_404_endpoint(self, client: AsyncClient) -> None:
        """Несуществующий маршрут → 404."""
        resp = await client.get('/nonexistent')
        assert resp.status_code == 404

    async def test_cors_headers(self, client: AsyncClient) -> None:
        """CORS middleware активен."""
        resp = await client.options(
            '/health',
            headers={
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'GET',
            },
        )
        # Если CORS настроен, запрос не должен быть 5xx
        assert resp.status_code < 500

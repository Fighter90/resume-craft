"""Тесты Health Check."""

from __future__ import annotations

from httpx import AsyncClient


class TestHealth:
    """Тесты GET /health."""

    async def test_health_ok(self, client: AsyncClient) -> None:
        """Health check → 200 OK."""
        response = await client.get('/health')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'version' in data

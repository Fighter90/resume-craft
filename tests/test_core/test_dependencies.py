"""Тесты модуля core/dependencies.py."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from httpx import AsyncClient

from app.core.config import get_settings

settings = get_settings()


class TestGetCurrentUser:
    """Тесты зависимости get_current_user (через API)."""

    async def test_valid_token(self, auth_client: AsyncClient) -> None:
        """Валидный access-токен → 200."""
        response = await auth_client.get('/api/v1/auth/me')
        assert response.status_code == 200

    async def test_no_token(self, client: AsyncClient) -> None:
        """Без токена → 401."""
        response = await client.get('/api/v1/auth/me')
        assert response.status_code == 401

    async def test_expired_token(self, client: AsyncClient) -> None:
        """Просроченный токен → 401 TOKEN_EXPIRED."""
        payload = {
            'sub': str(uuid4()),
            'exp': datetime.now(tz=UTC) - timedelta(hours=1),
            'type': 'access',
            'jti': str(uuid4()),
        }
        token = jwt.encode(payload, settings.secret_key, algorithm='HS256')
        response = await client.get(
            '/api/v1/auth/me',
            headers={'Authorization': f'Bearer {token}'},
        )
        assert response.status_code == 401

    async def test_invalid_token(self, client: AsyncClient) -> None:
        """Невалидный токен → 401 TOKEN_INVALID."""
        response = await client.get(
            '/api/v1/auth/me',
            headers={'Authorization': 'Bearer invalid.token.here'},
        )
        assert response.status_code == 401

    async def test_refresh_token_not_accepted(self, client: AsyncClient) -> None:
        """Refresh-токен вместо access → 401."""
        from app.core.security import create_refresh_token

        token = create_refresh_token(uuid4())
        response = await client.get(
            '/api/v1/auth/me',
            headers={'Authorization': f'Bearer {token}'},
        )
        assert response.status_code == 401

    async def test_nonexistent_user_token(self, client: AsyncClient) -> None:
        """Токен для несуществующего пользователя → 401."""
        from app.core.security import create_access_token

        token = create_access_token(uuid4())
        response = await client.get(
            '/api/v1/auth/me',
            headers={'Authorization': f'Bearer {token}'},
        )
        assert response.status_code == 401

    async def test_token_without_sub(self, client: AsyncClient) -> None:
        """Токен без sub → 401."""
        payload = {
            'exp': datetime.now(tz=UTC) + timedelta(hours=1),
            'type': 'access',
            'jti': str(uuid4()),
        }
        token = jwt.encode(payload, settings.secret_key, algorithm='HS256')
        response = await client.get(
            '/api/v1/auth/me',
            headers={'Authorization': f'Bearer {token}'},
        )
        assert response.status_code == 401

    async def test_token_with_invalid_uuid(self, client: AsyncClient) -> None:
        """Токен с невалидным UUID → 401."""
        payload = {
            'sub': 'not-a-uuid',
            'exp': datetime.now(tz=UTC) + timedelta(hours=1),
            'type': 'access',
            'jti': str(uuid4()),
        }
        token = jwt.encode(payload, settings.secret_key, algorithm='HS256')
        response = await client.get(
            '/api/v1/auth/me',
            headers={'Authorization': f'Bearer {token}'},
        )
        assert response.status_code == 401

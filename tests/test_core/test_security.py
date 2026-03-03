"""Тесты модуля core/security.py."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

settings = get_settings()


class TestPasswordHashing:
    """Тесты хэширования паролей."""

    def test_hash_password_returns_hash(self) -> None:
        """hash_password() возвращает bcrypt-хэш."""
        hashed = hash_password('TestPass123')
        assert hashed.startswith('$2b$')
        assert len(hashed) > 50

    def test_verify_correct_password(self) -> None:
        """Корректный пароль → True."""
        hashed = hash_password('MySecret1')
        assert verify_password('MySecret1', hashed) is True

    def test_verify_wrong_password(self) -> None:
        """Неверный пароль → False."""
        hashed = hash_password('MySecret1')
        assert verify_password('WrongPass', hashed) is False

    def test_different_hashes_for_same_password(self) -> None:
        """Одинаковые пароли дают разные хэши (соль)."""
        h1 = hash_password('SamePass1')
        h2 = hash_password('SamePass1')
        assert h1 != h2
        assert verify_password('SamePass1', h1) is True
        assert verify_password('SamePass1', h2) is True


class TestJWTTokens:
    """Тесты JWT-токенов."""

    def test_access_token_valid(self) -> None:
        """Access-токен содержит корректные данные."""
        user_id = uuid4()
        token = create_access_token(user_id)
        payload = decode_token(token)
        assert payload['sub'] == str(user_id)
        assert payload['type'] == 'access'
        assert 'jti' in payload
        assert 'exp' in payload

    def test_refresh_token_valid(self) -> None:
        """Refresh-токен содержит корректные данные."""
        user_id = uuid4()
        token = create_refresh_token(user_id)
        payload = decode_token(token)
        assert payload['sub'] == str(user_id)
        assert payload['type'] == 'refresh'
        assert 'jti' in payload

    def test_access_token_expiry(self) -> None:
        """Access-токен имеет exp ≈ 30 минут от текущего времени."""
        user_id = uuid4()
        token = create_access_token(user_id)
        payload = decode_token(token)
        exp = datetime.fromtimestamp(payload['exp'], tz=UTC)
        now = datetime.now(tz=UTC)
        diff = exp - now
        assert timedelta(minutes=25) < diff < timedelta(minutes=35)

    def test_refresh_token_expiry(self) -> None:
        """Refresh-токен имеет exp ≈ 30 дней."""
        user_id = uuid4()
        token = create_refresh_token(user_id)
        payload = decode_token(token)
        exp = datetime.fromtimestamp(payload['exp'], tz=UTC)
        now = datetime.now(tz=UTC)
        diff = exp - now
        assert timedelta(days=28) < diff < timedelta(days=32)

    def test_decode_expired_token_raises(self) -> None:
        """Просроченный токен → ExpiredSignatureError."""
        user_id = uuid4()
        payload = {
            'sub': str(user_id),
            'exp': datetime.now(tz=UTC) - timedelta(hours=1),
            'type': 'access',
            'jti': str(uuid4()),
        }
        token = jwt.encode(payload, settings.secret_key, algorithm='HS256')
        with pytest.raises(jwt.ExpiredSignatureError):
            decode_token(token)

    def test_decode_invalid_token_raises(self) -> None:
        """Невалидный токен → InvalidTokenError."""
        with pytest.raises(jwt.InvalidTokenError):
            decode_token('invalid.token.here')

    def test_unique_jti(self) -> None:
        """Каждый токен имеет уникальный jti."""
        user_id = uuid4()
        t1 = decode_token(create_access_token(user_id))
        t2 = decode_token(create_access_token(user_id))
        assert t1['jti'] != t2['jti']

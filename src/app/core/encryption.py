"""Шифрование данных (Fernet) для хранения API-ключей."""

from __future__ import annotations

import base64
import hashlib
import logging

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _derive_key(secret: str) -> bytes:
    """Derive a 32-byte Fernet key from SECRET_KEY via SHA-256."""
    digest = hashlib.sha256(secret.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(digest)


def get_fernet() -> Fernet:
    """Get Fernet instance derived from app SECRET_KEY."""
    settings = get_settings()
    key = _derive_key(settings.secret_key)
    return Fernet(key)


def encrypt_value(plaintext: str) -> str:
    """Encrypt a string value → base64-encoded ciphertext."""
    if not plaintext:
        return ''
    f = get_fernet()
    return f.encrypt(plaintext.encode('utf-8')).decode('utf-8')


def decrypt_value(ciphertext: str) -> str:
    """Decrypt a base64-encoded ciphertext → plaintext.

    Returns empty string if decryption fails.
    """
    if not ciphertext:
        return ''
    f = get_fernet()
    try:
        return f.decrypt(ciphertext.encode('utf-8')).decode('utf-8')
    except (InvalidToken, Exception):
        logger.warning('Failed to decrypt value (key may have changed)')
        return ''


def mask_api_key(key: str) -> str:
    """Mask an API key for safe display: 'sk-abc...xyz'."""
    if not key or len(key) < 8:
        return '***' if key else ''
    return f'{key[:4]}...{key[-4:]}'

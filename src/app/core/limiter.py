"""Общий rate limiter для всего приложения (SEC-005)."""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

# Единый экземпляр — импортируется в роутерах и main.py.
# storage_uri настраивается в create_app() через limiter._storage.
limiter = Limiter(key_func=get_remote_address)

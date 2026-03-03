"""API-клиент для взаимодействия с FastAPI-бэкендом."""

from __future__ import annotations

import requests
import streamlit as st

API_BASE = 'http://localhost:8000/api/v1'


def api_headers() -> dict[str, str]:
    """JWT-заголовки."""
    headers: dict[str, str] = {}
    if st.session_state.get('token'):
        headers['Authorization'] = f'Bearer {st.session_state.token}'
    return headers


def api_request(
    method: str,
    path: str,
    *,
    json_data: dict | None = None,
    files: dict | None = None,
) -> dict | None:
    """Обёртка для API-запросов с обработкой ошибок."""
    url = f'{API_BASE}{path}'
    try:
        resp = requests.request(
            method, url,
            headers=api_headers(),
            json=json_data,
            files=files,
            timeout=60,
        )
        if resp.status_code >= 400:
            ct = resp.headers.get('content-type', '')
            error = resp.json() if ct.startswith('application/json') else {}
            st.error(f'Ошибка API: {error.get("message", resp.status_code)}')
            return None
        if resp.status_code == 204:
            return {}
        return resp.json()
    except requests.ConnectionError:
        return None  # Demo mode will handle this

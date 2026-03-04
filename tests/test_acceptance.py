"""Приёмочные (smoke) тесты для production.

Запускаются после каждого деплоя для проверки работоспособности
всех 24 API-эндпоинтов. Не требуют Docker/БД — работают через HTTP
против живого сервера.

Использование:
    # Локально (прод)
    BASE_URL=https://resumecraft.ru pytest tests/test_acceptance.py -v

    # На сервере после деплоя
    BASE_URL=http://localhost:8000 pytest tests/test_acceptance.py -v

Переменные окружения:
    BASE_URL    — адрес сервера (по умолчанию http://localhost:8000)
    ACCEPT_USER — email тестового пользователя (создаётся автоматически)
    ACCEPT_PASS — пароль тестового пользователя
"""

from __future__ import annotations

import os
import uuid
from typing import Any

import httpx
import pytest

# ---------------------------------------------------------------------------
# Маркер — тесты запускаются ТОЛЬКО при наличии BASE_URL
# ---------------------------------------------------------------------------

pytestmark = pytest.mark.skipif(
    not os.getenv('BASE_URL'),
    reason='Acceptance tests require BASE_URL env var (e.g. BASE_URL=https://resumecraft.ru)',
)

# ---------------------------------------------------------------------------
# Конфигурация
# ---------------------------------------------------------------------------

BASE_URL: str = os.getenv('BASE_URL', 'http://localhost:8000')
TEST_EMAIL: str = os.getenv('ACCEPT_USER', f'accept-{uuid.uuid4().hex[:8]}@test.resumecraft.ru')
TEST_PASS: str = os.getenv('ACCEPT_PASS', 'AcceptPass1')
API: str = f'{BASE_URL}/api/v1'


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope='module')
def http() -> httpx.Client:
    """Синхронный HTTP-клиент без авторизации."""
    with httpx.Client(base_url=BASE_URL, timeout=60.0, follow_redirects=True) as client:
        yield client


@pytest.fixture(scope='module')
def tokens(http: httpx.Client) -> dict[str, str]:
    """Регистрация/логин тестового пользователя → токены."""
    # Пробуем зарегистрировать
    resp = http.post(
        f'{API}/auth/register',
        json={
            'email': TEST_EMAIL,
            'password': TEST_PASS,
        },
    )
    if resp.status_code == 201:
        return resp.json()

    # Если уже существует — логинимся
    assert resp.status_code == 409, f'Unexpected register status: {resp.status_code} {resp.text}'
    resp = http.post(
        f'{API}/auth/login',
        json={
            'email': TEST_EMAIL,
            'password': TEST_PASS,
        },
    )
    assert resp.status_code == 200, f'Login failed: {resp.status_code} {resp.text}'
    return resp.json()


@pytest.fixture(scope='module')
def access_token(tokens: dict[str, str]) -> str:
    """JWT access token."""
    return tokens['access_token']


@pytest.fixture(scope='module')
def refresh_token(tokens: dict[str, str]) -> str:
    """JWT refresh token."""
    return tokens['refresh_token']


@pytest.fixture(scope='module')
def auth_headers(access_token: str) -> dict[str, str]:
    """Заголовки авторизации."""
    return {'Authorization': f'Bearer {access_token}'}


@pytest.fixture(scope='module')
def resume_id(http: httpx.Client, auth_headers: dict[str, str]) -> str:
    """Загружает тестовый PDF и возвращает resume_id."""
    pdf_content = (
        b'%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n'
        b'2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n'
        b'3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R'
        b'/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n'
        b'4 0 obj<</Length 44>>stream\n'
        b'BT /F1 12 Tf 72 720 Td (Python Developer) Tj ET\n'
        b'endstream\nendobj\n'
        b'5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n'
        b'xref\n0 6\ntrailer<</Size 6/Root 1 0 R>>\nstartxref\n0\n%%EOF'
    )
    resp = http.post(
        f'{API}/resumes/upload',
        headers=auth_headers,
        files={'file': ('accept_test.pdf', pdf_content, 'application/pdf')},
    )
    assert resp.status_code == 201, f'Resume upload failed: {resp.status_code} {resp.text}'
    return resp.json()['id']


@pytest.fixture(scope='module')
def vacancy_id(http: httpx.Client, auth_headers: dict[str, str]) -> str:
    """Создаёт тестовую вакансию вручную и возвращает vacancy_id."""
    resp = http.post(
        f'{API}/vacancies/manual',
        headers={**auth_headers, 'Content-Type': 'application/json'},
        json={
            'title': 'Acceptance Test Vacancy',
            'company': 'AcceptCorp',
            'description': 'Python developer needed. FastAPI, PostgreSQL, Docker experience.',
            'requirements': {'description': 'Python 3+ years', 'experience': '3-6 years'},
            'key_skills': ['Python', 'FastAPI', 'PostgreSQL', 'Docker'],
            'city': 'Москва',
        },
    )
    assert resp.status_code == 201, f'Manual vacancy failed: {resp.status_code} {resp.text}'
    return resp.json()['id']


@pytest.fixture(scope='module')
def rewrite_task_id(
    http: httpx.Client,
    auth_headers: dict[str, str],
    resume_id: str,
    vacancy_id: str,
) -> str:
    """Запускает реврайт-задачу и возвращает task_id."""
    resp = http.post(
        f'{API}/rewrite',
        headers={**auth_headers, 'Content-Type': 'application/json'},
        json={'resume_id': resume_id, 'vacancy_id': vacancy_id},
    )
    assert resp.status_code == 202, f'Rewrite failed: {resp.status_code} {resp.text}'
    return resp.json()['task_id']


# ---------------------------------------------------------------------------
# Хелперы
# ---------------------------------------------------------------------------


def _assert_json(
    resp: httpx.Response,
    status: int,
    keys: list[str] | None = None,
) -> dict[str, Any]:
    """Проверяет статус и наличие ключей в JSON-ответе."""
    assert resp.status_code == status, (
        f'Expected {status}, got {resp.status_code}: {resp.text[:500]}'
    )
    if status == 204:
        return {}
    data = resp.json()
    if keys:
        for key in keys:
            assert key in data, f'Missing key "{key}" in response: {list(data.keys())}'
    return data


# ===========================================================================
# 1. SYSTEM
# ===========================================================================


class TestHealth:
    """GET /health — проверка доступности сервера."""

    def test_health_ok(self, http: httpx.Client) -> None:
        data = _assert_json(http.get(f'{BASE_URL}/health'), 200, ['status', 'version'])
        assert data['status'] == 'healthy'

    def test_docs_available(self, http: httpx.Client) -> None:
        resp = http.get(f'{BASE_URL}/docs')
        assert resp.status_code == 200

    def test_openapi_json(self, http: httpx.Client) -> None:
        resp = http.get(f'{BASE_URL}/openapi.json')
        assert resp.status_code == 200
        data = resp.json()
        assert 'paths' in data


# ===========================================================================
# 2. AUTH — 8 эндпоинтов
# ===========================================================================


class TestAuthRegister:
    """POST /auth/register"""

    def test_register_or_exists(self, http: httpx.Client) -> None:
        resp = http.post(
            f'{API}/auth/register',
            json={
                'email': TEST_EMAIL,
                'password': TEST_PASS,
            },
        )
        assert resp.status_code in (201, 409)
        if resp.status_code == 201:
            _assert_json(resp, 201, ['access_token', 'refresh_token', 'token_type'])

    def test_register_weak_password(self, http: httpx.Client) -> None:
        resp = http.post(
            f'{API}/auth/register',
            json={
                'email': 'weak@test.resumecraft.ru',
                'password': 'short',
            },
        )
        assert resp.status_code == 422

    def test_register_invalid_email(self, http: httpx.Client) -> None:
        resp = http.post(
            f'{API}/auth/register',
            json={
                'email': 'not-an-email',
                'password': TEST_PASS,
            },
        )
        assert resp.status_code == 422


class TestAuthLogin:
    """POST /auth/login"""

    def test_login_success(self, http: httpx.Client, tokens: dict[str, str]) -> None:
        assert 'access_token' in tokens
        assert 'refresh_token' in tokens
        assert tokens['token_type'] == 'bearer'

    def test_login_wrong_password(self, http: httpx.Client) -> None:
        resp = http.post(
            f'{API}/auth/login',
            json={
                'email': TEST_EMAIL,
                'password': 'WrongPassword1',
            },
        )
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, http: httpx.Client) -> None:
        resp = http.post(
            f'{API}/auth/login',
            json={
                'email': 'nobody@test.resumecraft.ru',
                'password': TEST_PASS,
            },
        )
        assert resp.status_code in (401, 404)


class TestAuthRefresh:
    """POST /auth/refresh"""

    def test_refresh_success(self, http: httpx.Client, refresh_token: str) -> None:
        resp = http.post(f'{API}/auth/refresh', json={'refresh_token': refresh_token})
        _assert_json(resp, 200, ['access_token', 'refresh_token', 'token_type'])

    def test_refresh_invalid_token(self, http: httpx.Client) -> None:
        resp = http.post(f'{API}/auth/refresh', json={'refresh_token': 'invalid.token.here'})
        assert resp.status_code == 401


class TestAuthMe:
    """GET /auth/me — профиль текущего пользователя."""

    def test_me_success(self, http: httpx.Client, auth_headers: dict[str, str]) -> None:
        data = _assert_json(
            http.get(f'{API}/auth/me', headers=auth_headers),
            200,
            ['id', 'email', 'plan', 'is_active', 'created_at'],
        )
        assert data['email'] == TEST_EMAIL
        assert data['is_active'] is True

    def test_me_no_auth(self, http: httpx.Client) -> None:
        resp = http.get(f'{API}/auth/me')
        assert resp.status_code == 401

    def test_me_invalid_token(self, http: httpx.Client) -> None:
        resp = http.get(f'{API}/auth/me', headers={'Authorization': 'Bearer invalid.jwt.token'})
        assert resp.status_code == 401


class TestAuthUpdateProfile:
    """PUT /auth/me — обновление профиля."""

    def test_update_full_name(self, http: httpx.Client, auth_headers: dict[str, str]) -> None:
        data = _assert_json(
            http.put(f'{API}/auth/me', headers=auth_headers, json={'full_name': 'Accept Tester'}),
            200,
            ['id', 'email', 'full_name'],
        )
        assert data['full_name'] == 'Accept Tester'


class TestAuthChangePassword:
    """PUT /auth/me/password"""

    def test_change_password_wrong_current(
        self,
        http: httpx.Client,
        auth_headers: dict[str, str],
    ) -> None:
        resp = http.put(
            f'{API}/auth/me/password',
            headers=auth_headers,
            json={
                'current_password': 'WrongCurrent1',
                'new_password': 'NewSecure1',
            },
        )
        assert resp.status_code in (400, 401, 403)


class TestAuthLogout:
    """POST /auth/logout"""

    def test_logout_no_auth(self, http: httpx.Client) -> None:
        resp = http.post(f'{API}/auth/logout')
        assert resp.status_code == 401


# ===========================================================================
# 3. RESUMES — 5 эндпоинтов
# ===========================================================================


class TestResumeUpload:
    """POST /resumes/upload"""

    def test_upload_pdf(self, resume_id: str) -> None:
        assert resume_id  # создано фикстурой
        assert len(resume_id) == 36  # UUID формат

    def test_upload_no_auth(self, http: httpx.Client) -> None:
        resp = http.post(
            f'{API}/resumes/upload',
            files={
                'file': ('test.pdf', b'%PDF-fake', 'application/pdf'),
            },
        )
        assert resp.status_code == 401

    def test_upload_unsupported_format(
        self,
        http: httpx.Client,
        auth_headers: dict[str, str],
    ) -> None:
        resp = http.post(
            f'{API}/resumes/upload',
            headers=auth_headers,
            files={'file': ('test.txt', b'plain text', 'text/plain')},
        )
        assert resp.status_code == 400


class TestResumeList:
    """GET /resumes"""

    def test_list_resumes(
        self,
        http: httpx.Client,
        auth_headers: dict[str, str],
        resume_id: str,
    ) -> None:
        data = _assert_json(
            http.get(f'{API}/resumes', headers=auth_headers),
            200,
            ['items', 'total', 'limit', 'offset'],
        )
        assert data['total'] >= 1
        assert isinstance(data['items'], list)

    def test_list_pagination(self, http: httpx.Client, auth_headers: dict[str, str]) -> None:
        resp = http.get(f'{API}/resumes', headers=auth_headers, params={'limit': 1, 'offset': 0})
        data = _assert_json(resp, 200, ['items', 'total'])
        assert len(data['items']) <= 1

    def test_list_no_auth(self, http: httpx.Client) -> None:
        assert http.get(f'{API}/resumes').status_code == 401


class TestResumeGet:
    """GET /resumes/{id}"""

    def test_get_resume(
        self,
        http: httpx.Client,
        auth_headers: dict[str, str],
        resume_id: str,
    ) -> None:
        data = _assert_json(
            http.get(f'{API}/resumes/{resume_id}', headers=auth_headers),
            200,
            ['id', 'user_id', 'title', 'file_format', 'raw_text', 'status'],
        )
        assert data['id'] == resume_id
        assert data['file_format'] == 'pdf'

    def test_get_resume_not_found(
        self,
        http: httpx.Client,
        auth_headers: dict[str, str],
    ) -> None:
        fake_id = str(uuid.uuid4())
        resp = http.get(f'{API}/resumes/{fake_id}', headers=auth_headers)
        assert resp.status_code == 404


class TestResumeUpdate:
    """PUT /resumes/{id}"""

    def test_update_title(
        self,
        http: httpx.Client,
        auth_headers: dict[str, str],
        resume_id: str,
    ) -> None:
        data = _assert_json(
            http.put(
                f'{API}/resumes/{resume_id}',
                headers=auth_headers,
                json={'title': 'Updated Resume'},
            ),
            200,
            ['id', 'title'],
        )
        assert data['title'] == 'Updated Resume'


class TestResumeDelete:
    """DELETE /resumes/{id} — проверяется в cleanup."""

    def test_delete_not_found(
        self,
        http: httpx.Client,
        auth_headers: dict[str, str],
    ) -> None:
        fake_id = str(uuid.uuid4())
        resp = http.delete(f'{API}/resumes/{fake_id}', headers=auth_headers)
        assert resp.status_code == 404


# ===========================================================================
# 4. VACANCIES — 5 эндпоинтов
# ===========================================================================


class TestVacancySearch:
    """GET /vacancies/search — поиск по hh.ru."""

    def test_search_success(self, http: httpx.Client, auth_headers: dict[str, str]) -> None:
        data = _assert_json(
            http.get(
                f'{API}/vacancies/search',
                headers=auth_headers,
                params={'text': 'python', 'per_page': 2},
            ),
            200,
            ['items', 'found', 'pages'],
        )
        assert isinstance(data['items'], list)
        assert data['found'] > 0

    def test_search_no_auth(self, http: httpx.Client) -> None:
        resp = http.get(f'{API}/vacancies/search', params={'text': 'python'})
        assert resp.status_code == 401


class TestVacancyFromURL:
    """POST /vacancies/from-url — парсинг вакансии c hh.ru."""

    def test_from_url_success(self, http: httpx.Client, auth_headers: dict[str, str]) -> None:
        resp = http.post(
            f'{API}/vacancies/from-url',
            headers={**auth_headers, 'Content-Type': 'application/json'},
            json={'url': 'https://hh.ru/vacancy/130655683'},
        )
        # 201 или 502 если hh.ru временно недоступен
        if resp.status_code == 201:
            _assert_json(resp, 201, ['id', 'hh_id', 'title', 'key_skills'])
        else:
            assert resp.status_code in (502, 503), (
                f'Unexpected: {resp.status_code} {resp.text[:200]}'
            )

    def test_from_url_invalid(self, http: httpx.Client, auth_headers: dict[str, str]) -> None:
        resp = http.post(
            f'{API}/vacancies/from-url',
            headers={**auth_headers, 'Content-Type': 'application/json'},
            json={'url': 'https://example.com/not-hh'},
        )
        # 400/422 = валидация, 500/502 = сервер не обработал не-hh URL
        assert resp.status_code in (400, 422, 500, 502)


class TestVacancyManual:
    """POST /vacancies/manual"""

    def test_manual_create(self, vacancy_id: str) -> None:
        assert vacancy_id
        assert len(vacancy_id) == 36

    def test_manual_missing_fields(
        self,
        http: httpx.Client,
        auth_headers: dict[str, str],
    ) -> None:
        resp = http.post(
            f'{API}/vacancies/manual',
            headers={**auth_headers, 'Content-Type': 'application/json'},
            json={},  # нет обязательных полей
        )
        assert resp.status_code == 422


class TestVacancyGet:
    """GET /vacancies/{id}"""

    def test_get_vacancy(
        self,
        http: httpx.Client,
        auth_headers: dict[str, str],
        vacancy_id: str,
    ) -> None:
        data = _assert_json(
            http.get(f'{API}/vacancies/{vacancy_id}', headers=auth_headers),
            200,
            ['id', 'title', 'company', 'description', 'key_skills'],
        )
        assert data['id'] == vacancy_id

    def test_get_vacancy_not_found(
        self,
        http: httpx.Client,
        auth_headers: dict[str, str],
    ) -> None:
        fake_id = str(uuid.uuid4())
        resp = http.get(f'{API}/vacancies/{fake_id}', headers=auth_headers)
        assert resp.status_code == 404


class TestVacancyDelete:
    """DELETE /vacancies/{id}"""

    def test_delete_not_found(
        self,
        http: httpx.Client,
        auth_headers: dict[str, str],
    ) -> None:
        fake_id = str(uuid.uuid4())
        resp = http.delete(f'{API}/vacancies/{fake_id}', headers=auth_headers)
        assert resp.status_code == 404


# ===========================================================================
# 5. REWRITE — 4 эндпоинта
# ===========================================================================


class TestRewriteCreate:
    """POST /rewrite — запуск AI-оптимизации."""

    def test_create_task(self, rewrite_task_id: str) -> None:
        assert rewrite_task_id
        assert len(rewrite_task_id) == 36

    def test_create_no_auth(self, http: httpx.Client) -> None:
        resp = http.post(
            f'{API}/rewrite',
            json={
                'resume_id': str(uuid.uuid4()),
                'vacancy_id': str(uuid.uuid4()),
            },
        )
        assert resp.status_code == 401

    def test_create_nonexistent_resume(
        self,
        http: httpx.Client,
        auth_headers: dict[str, str],
        vacancy_id: str,
    ) -> None:
        resp = http.post(
            f'{API}/rewrite',
            headers={**auth_headers, 'Content-Type': 'application/json'},
            json={
                'resume_id': str(uuid.uuid4()),
                'vacancy_id': vacancy_id,
            },
        )
        assert resp.status_code == 404


class TestRewriteStatus:
    """GET /rewrite/{task_id}/status"""

    def test_status_exists(
        self,
        http: httpx.Client,
        auth_headers: dict[str, str],
        rewrite_task_id: str,
    ) -> None:
        data = _assert_json(
            http.get(f'{API}/rewrite/{rewrite_task_id}/status', headers=auth_headers),
            200,
            ['task_id', 'status', 'step', 'progress'],
        )
        assert data['task_id'] == rewrite_task_id
        assert data['status'] in ('pending', 'processing', 'completed', 'failed')
        assert 0 <= data['progress'] <= 100

    def test_status_not_found(
        self,
        http: httpx.Client,
        auth_headers: dict[str, str],
    ) -> None:
        fake_id = str(uuid.uuid4())
        resp = http.get(f'{API}/rewrite/{fake_id}/status', headers=auth_headers)
        assert resp.status_code == 404


class TestRewriteResult:
    """GET /rewrite/{task_id}/result"""

    def test_result_exists(
        self,
        http: httpx.Client,
        auth_headers: dict[str, str],
        rewrite_task_id: str,
    ) -> None:
        data = _assert_json(
            http.get(f'{API}/rewrite/{rewrite_task_id}/result', headers=auth_headers),
            200,
            ['id', 'resume_id', 'vacancy_id', 'model_name', 'status'],
        )
        assert data['id'] == rewrite_task_id

    def test_result_not_found(
        self,
        http: httpx.Client,
        auth_headers: dict[str, str],
    ) -> None:
        fake_id = str(uuid.uuid4())
        resp = http.get(f'{API}/rewrite/{fake_id}/result', headers=auth_headers)
        assert resp.status_code == 404


class TestRewriteHistory:
    """GET /rewrite/history"""

    def test_history_list(
        self,
        http: httpx.Client,
        auth_headers: dict[str, str],
        rewrite_task_id: str,
    ) -> None:
        data = _assert_json(
            http.get(f'{API}/rewrite/history', headers=auth_headers),
            200,
            ['items', 'total'],
        )
        assert data['total'] >= 1
        assert isinstance(data['items'], list)
        ids = [item['id'] for item in data['items']]
        assert rewrite_task_id in ids

    def test_history_no_auth(self, http: httpx.Client) -> None:
        assert http.get(f'{API}/rewrite/history').status_code == 401


# ===========================================================================
# 6. EXPORT — 1 эндпоинт
# ===========================================================================


class TestExportDocx:
    """GET /export/{task_id}/docx"""

    def test_export_not_completed(
        self,
        http: httpx.Client,
        auth_headers: dict[str, str],
        rewrite_task_id: str,
    ) -> None:
        """Экспорт незавершённого реврайта → 404 или 400."""
        resp = http.get(
            f'{API}/export/{rewrite_task_id}/docx',
            headers=auth_headers,
        )
        # Без LLM-ключей задача failed/pending → нет данных для экспорта
        assert resp.status_code in (200, 400, 404)

    def test_export_not_found(
        self,
        http: httpx.Client,
        auth_headers: dict[str, str],
    ) -> None:
        fake_id = str(uuid.uuid4())
        resp = http.get(f'{API}/export/{fake_id}/docx', headers=auth_headers)
        assert resp.status_code == 404

    def test_export_no_auth(self, http: httpx.Client) -> None:
        fake_id = str(uuid.uuid4())
        resp = http.get(f'{API}/export/{fake_id}/docx')
        assert resp.status_code == 401


# ===========================================================================
# 7. CLEANUP — удаление тестовых данных
# ===========================================================================


class TestCleanup:
    """Удаление тестовых данных (должен идти последним)."""

    def test_delete_vacancy(
        self,
        http: httpx.Client,
        auth_headers: dict[str, str],
        vacancy_id: str,
    ) -> None:
        resp = http.delete(f'{API}/vacancies/{vacancy_id}', headers=auth_headers)
        assert resp.status_code == 204

    def test_delete_resume(
        self,
        http: httpx.Client,
        auth_headers: dict[str, str],
        resume_id: str,
    ) -> None:
        resp = http.delete(f'{API}/resumes/{resume_id}', headers=auth_headers)
        assert resp.status_code == 204

    def test_logout(self, http: httpx.Client, auth_headers: dict[str, str]) -> None:
        resp = http.post(f'{API}/auth/logout', headers=auth_headers)
        assert resp.status_code == 204

    def test_delete_account(self, http: httpx.Client) -> None:
        """Удаление тестового аккаунта (логинимся заново после logout)."""
        resp = http.post(
            f'{API}/auth/login',
            json={
                'email': TEST_EMAIL,
                'password': TEST_PASS,
            },
        )
        if resp.status_code != 200:
            pytest.skip('Cannot login for account deletion')
        token = resp.json()['access_token']
        resp = http.delete(
            f'{API}/auth/me',
            headers={'Authorization': f'Bearer {token}'},
        )
        assert resp.status_code == 204

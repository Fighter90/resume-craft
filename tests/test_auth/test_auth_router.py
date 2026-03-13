"""Тесты модуля аутентификации."""

from __future__ import annotations

from httpx import AsyncClient

from app.auth.models import User


class TestRegister:
    """Тесты POST /auth/register."""

    async def test_register_success(self, client: AsyncClient) -> None:
        """Успешная регистрация → 201 + JWT-токены."""
        response = await client.post(
            '/api/v1/auth/register',
            json={
                'email': 'new@example.com',
                'password': 'StrongPass1',
                'full_name': 'Иван Иванов',
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert data['token_type'] == 'bearer'

    async def test_register_weak_password(self, client: AsyncClient) -> None:
        """Слабый пароль (без цифр) → 422."""
        response = await client.post(
            '/api/v1/auth/register',
            json={
                'email': 'weak@example.com',
                'password': 'nodigitshere',
            },
        )
        assert response.status_code == 422

    async def test_register_short_password(self, client: AsyncClient) -> None:
        """Короткий пароль → 422."""
        response = await client.post(
            '/api/v1/auth/register',
            json={
                'email': 'short@example.com',
                'password': 'Sh1',
            },
        )
        assert response.status_code == 422

    async def test_register_invalid_email(self, client: AsyncClient) -> None:
        """Невалидный email → 422."""
        response = await client.post(
            '/api/v1/auth/register',
            json={
                'email': 'not-an-email',
                'password': 'TestPass123',
            },
        )
        assert response.status_code == 422

    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User) -> None:
        """Дублирующий email → 201 с сообщением (LIVE-013: защита от email enumeration)."""
        response = await client.post(
            '/api/v1/auth/register',
            json={
                'email': test_user.email,
                'password': 'AnotherPass1',
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert 'message' in data


class TestLogin:
    """Тесты POST /auth/login."""

    async def test_login_success(self, client: AsyncClient, test_user: User) -> None:
        """Успешная авторизация → 200 + JWT."""
        response = await client.post(
            '/api/v1/auth/login',
            json={
                'email': test_user.email,
                'password': 'TestPass123',
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert data['token_type'] == 'bearer'

    async def test_login_wrong_password(self, client: AsyncClient, test_user: User) -> None:
        """Неверный пароль → 401."""
        response = await client.post(
            '/api/v1/auth/login',
            json={
                'email': test_user.email,
                'password': 'WrongPass1',
            },
        )
        assert response.status_code == 401

    async def test_login_nonexistent_email(self, client: AsyncClient) -> None:
        """Несуществующий email → 401."""
        response = await client.post(
            '/api/v1/auth/login',
            json={
                'email': 'nobody@example.com',
                'password': 'TestPass123',
            },
        )
        assert response.status_code == 401


class TestLoginFormData:
    """P1-4: Тесты POST /auth/login с form-data и form-urlencoded."""

    async def test_login_form_urlencoded(self, client: AsyncClient, test_user: User) -> None:
        """Логин через application/x-www-form-urlencoded → 200."""
        response = await client.post(
            '/api/v1/auth/login',
            data={
                'email': test_user.email,
                'password': 'TestPass123',
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data

    async def test_login_form_oauth2_username_field(
        self,
        client: AsyncClient,
        test_user: User,
    ) -> None:
        """OAuth2 form: поле username вместо email → 200."""
        response = await client.post(
            '/api/v1/auth/login',
            data={
                'username': test_user.email,
                'password': 'TestPass123',
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data

    async def test_login_json_still_works(self, client: AsyncClient, test_user: User) -> None:
        """JSON-логин по-прежнему работает → 200."""
        response = await client.post(
            '/api/v1/auth/login',
            json={
                'email': test_user.email,
                'password': 'TestPass123',
            },
        )
        assert response.status_code == 200


class TestMe:
    """Тесты GET /auth/me."""

    async def test_me_authorized(self, auth_client: AsyncClient, test_user: User) -> None:
        """Авторизованный запрос → 200 + профиль."""
        response = await auth_client.get('/api/v1/auth/me')
        assert response.status_code == 200
        data = response.json()
        assert data['email'] == test_user.email

    async def test_me_unauthorized(self, client: AsyncClient) -> None:
        """Без JWT → 401."""
        response = await client.get('/api/v1/auth/me')
        assert response.status_code == 401


class TestUpdateMe:
    """Тесты PUT /auth/me."""

    async def test_update_full_name(self, auth_client: AsyncClient) -> None:
        """Обновление имени → 200."""
        response = await auth_client.put(
            '/api/v1/auth/me',
            json={
                'full_name': 'Новое Имя',
            },
        )
        assert response.status_code == 200
        assert response.json()['full_name'] == 'Новое Имя'

    async def test_update_no_auth(self, client: AsyncClient) -> None:
        """Без JWT → 401."""
        response = await client.put('/api/v1/auth/me', json={'full_name': 'Test'})
        assert response.status_code == 401


class TestChangePassword:
    """Тесты PUT /auth/me/password."""

    async def test_change_password_success(self, auth_client: AsyncClient) -> None:
        """Успешная смена пароля → 204."""
        response = await auth_client.put(
            '/api/v1/auth/me/password',
            json={
                'current_password': 'TestPass123',
                'new_password': 'NewSecure1',
            },
        )
        assert response.status_code == 204

    async def test_change_password_wrong_current(self, auth_client: AsyncClient) -> None:
        """Неверный текущий пароль → 401."""
        response = await auth_client.put(
            '/api/v1/auth/me/password',
            json={
                'current_password': 'WrongPass1',
                'new_password': 'NewSecure1',
            },
        )
        assert response.status_code == 401

    async def test_change_password_weak_new(self, auth_client: AsyncClient) -> None:
        """Слабый новый пароль → 422."""
        response = await auth_client.put(
            '/api/v1/auth/me/password',
            json={
                'current_password': 'TestPass123',
                'new_password': 'nodigits',
            },
        )
        assert response.status_code == 422

    async def test_change_password_no_auth(self, client: AsyncClient) -> None:
        """Без JWT → 401."""
        response = await client.put(
            '/api/v1/auth/me/password',
            json={
                'current_password': 'TestPass123',
                'new_password': 'NewSecure1',
            },
        )
        assert response.status_code == 401


class TestDeleteMe:
    """Тесты DELETE /auth/me (полное удаление с паролем и подтверждением)."""

    async def test_delete_account_success(self, auth_client: AsyncClient) -> None:
        """Soft-delete аккаунта с подтверждением → 200."""
        response = await auth_client.request(
            'DELETE',
            '/api/v1/auth/me',
            json={'password': 'TestPass123', 'confirmation': 'УДАЛИТЬ'},
        )
        assert response.status_code == 200
        data = response.json()
        assert '30 дней' in data['message']

    async def test_delete_no_password(self, auth_client: AsyncClient) -> None:
        """DELETE без пароля → 422."""
        response = await auth_client.delete('/api/v1/auth/me')
        assert response.status_code == 422

    async def test_delete_wrong_password(self, auth_client: AsyncClient) -> None:
        """DELETE с неверным паролем → 401."""
        response = await auth_client.request(
            'DELETE',
            '/api/v1/auth/me',
            json={'password': 'WrongPass123', 'confirmation': 'УДАЛИТЬ'},
        )
        assert response.status_code == 401

    async def test_delete_no_auth(self, client: AsyncClient) -> None:
        """Без JWT → 401."""
        response = await client.delete('/api/v1/auth/me')
        assert response.status_code == 401


class TestRefresh:
    """Тесты POST /auth/refresh."""

    async def test_refresh_success(self, client: AsyncClient, test_user: User) -> None:
        """Успешное обновление токенов."""
        # Сначала логинимся, чтобы получить refresh_token
        login_resp = await client.post(
            '/api/v1/auth/login',
            json={
                'email': test_user.email,
                'password': 'TestPass123',
            },
        )
        refresh_token = login_resp.json()['refresh_token']

        response = await client.post(
            '/api/v1/auth/refresh',
            json={
                'refresh_token': refresh_token,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert 'refresh_token' in data

    async def test_refresh_invalid_token(self, client: AsyncClient) -> None:
        """Невалидный refresh-токен → 401."""
        response = await client.post(
            '/api/v1/auth/refresh',
            json={
                'refresh_token': 'invalid.token.here',
            },
        )
        assert response.status_code == 401


class TestLogout:
    """Тесты POST /auth/logout."""

    async def test_logout_success(self, auth_client: AsyncClient) -> None:
        """Успешный выход → 204."""
        response = await auth_client.post('/api/v1/auth/logout')
        assert response.status_code == 204

    async def test_logout_no_auth(self, client: AsyncClient) -> None:
        """Без JWT → 401."""
        response = await client.post('/api/v1/auth/logout')
        assert response.status_code == 401

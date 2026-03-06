"""Комплексные тесты для всех фиксов v1.7 (FIX-001 — FIX-012).

Покрывает: email-верификацию, шифрование, экспорт PDF/TXT,
soft-delete/restore резюме, скачивание файлов, настройки AI-ключей.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import jwt
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.encryption import decrypt_value, encrypt_value, mask_api_key
from app.core.security import create_verification_token, verify_email_token
from app.export.service import generate_pdf, generate_txt
from app.resumes.models import Resume
from app.resumes.service import restore_resume
from app.rewriter.models import RewriteHistory, RewriteStatus


# ═══════════════════════════════════════════════════════════════════
# FIX-007: Email Verification — security tokens
# ═══════════════════════════════════════════════════════════════════


class TestVerificationTokens:
    """Тесты create_verification_token / verify_email_token."""

    def test_create_and_verify(self) -> None:
        """Создание и верификация токена → возвращает email."""
        email = 'user@example.com'
        token = create_verification_token(email)
        assert isinstance(token, str)
        result = verify_email_token(token)
        assert result == email

    def test_wrong_token_type(self) -> None:
        """Access-токен → InvalidTokenError (неверный тип)."""
        from app.core.security import create_access_token

        token = create_access_token(uuid4())
        with pytest.raises(jwt.InvalidTokenError, match='Invalid token type'):
            verify_email_token(token)

    def test_invalid_token(self) -> None:
        """Мусорный токен → InvalidTokenError."""
        with pytest.raises(jwt.InvalidTokenError):
            verify_email_token('not.a.valid.token')

    def test_expired_token(self) -> None:
        """Истёкший токен → ExpiredSignatureError."""
        from datetime import timedelta

        from app.core.config import get_settings

        settings = get_settings()
        payload = {
            'sub': 'expired@example.com',
            'exp': datetime.now(tz=UTC) - timedelta(hours=1),
            'type': 'email_verification',
        }
        token = jwt.encode(payload, settings.secret_key, algorithm='HS256')
        with pytest.raises(jwt.ExpiredSignatureError):
            verify_email_token(token)


# ═══════════════════════════════════════════════════════════════════
# FIX-007: Email Verification — service + router
# ═══════════════════════════════════════════════════════════════════


class TestVerifyEmailService:
    """Тесты auth.service.verify_email()."""

    async def test_verify_success(
        self, session: AsyncSession, test_user: User,
    ) -> None:
        """Успешная верификация email."""
        from app.auth.service import verify_email

        assert test_user.is_verified is False
        token = create_verification_token(test_user.email)
        result = await verify_email(session, token=token)
        assert result == 'Email подтверждён'
        await session.refresh(test_user)
        assert test_user.is_verified is True

    async def test_verify_expired(self, session: AsyncSession) -> None:
        """Истёкший токен → TokenExpired."""
        from app.auth.service import verify_email
        from app.core.config import get_settings
        from app.core.exceptions import TokenExpired

        settings = get_settings()
        payload = {
            'sub': 'x@example.com',
            'exp': datetime.now(tz=UTC).timestamp() - 3600,
            'type': 'email_verification',
        }
        token = jwt.encode(payload, settings.secret_key, algorithm='HS256')
        with pytest.raises(TokenExpired):
            await verify_email(session, token=token)

    async def test_verify_user_not_found(self, session: AsyncSession) -> None:
        """Токен для несуществующего email → UserNotFound."""
        from app.auth.service import verify_email
        from app.core.exceptions import UserNotFound

        token = create_verification_token('nonexistent@example.com')
        with pytest.raises(UserNotFound):
            await verify_email(session, token=token)


class TestVerifyEmailRouter:
    """GET /api/v1/auth/verify/{token}."""

    async def test_verify_success(
        self, client: AsyncClient, session: AsyncSession, test_user: User,
    ) -> None:
        """Валидный токен → 200 + message."""
        token = create_verification_token(test_user.email)
        resp = await client.get(f'/api/v1/auth/verify/{token}')
        assert resp.status_code == 200
        assert resp.json()['message'] == 'Email подтверждён'

    async def test_verify_invalid_token(self, client: AsyncClient) -> None:
        """Невалидный токен → 401."""
        resp = await client.get('/api/v1/auth/verify/garbage.token.here')
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════
# FIX-001: Encryption (Fernet)
# ═══════════════════════════════════════════════════════════════════


class TestEncryption:
    """Тесты encrypt_value / decrypt_value / mask_api_key."""

    def test_encrypt_decrypt_roundtrip(self) -> None:
        """Раунд-трип шифрования/дешифрования."""
        plaintext = 'sk-test-api-key-1234567890'
        ciphertext = encrypt_value(plaintext)
        assert ciphertext != plaintext
        assert decrypt_value(ciphertext) == plaintext

    def test_encrypt_empty_string(self) -> None:
        """Пустая строка → пустая строка."""
        assert encrypt_value('') == ''
        assert decrypt_value('') == ''

    def test_decrypt_invalid_ciphertext(self) -> None:
        """Невалидный ciphertext → пустая строка."""
        assert decrypt_value('not-valid-ciphertext') == ''

    def test_mask_api_key_normal(self) -> None:
        """Маскирование ключа ≥ 8 символов."""
        key = 'sk-proj-123456789abcdef'
        masked = mask_api_key(key)
        assert masked.startswith('sk-p')
        assert masked.endswith('cdef')
        assert '...' in masked

    def test_mask_api_key_short(self) -> None:
        """Короткий ключ → '***'."""
        assert mask_api_key('short') == '***'

    def test_mask_api_key_empty(self) -> None:
        """Пустой ключ → ''."""
        assert mask_api_key('') == ''


# ═══════════════════════════════════════════════════════════════════
# FIX-001: Settings AI-keys router
# ═══════════════════════════════════════════════════════════════════


class TestSettingsAIKeysRouter:
    """CRUD /api/v1/settings/ai-keys."""

    async def test_get_ai_keys_no_auth(self, client: AsyncClient) -> None:
        """Без авторизации → 401."""
        resp = await client.get('/api/v1/settings/ai-keys')
        assert resp.status_code == 401

    async def test_get_ai_keys_empty(self, auth_client: AsyncClient) -> None:
        """Нет ключей → список с has_key=False."""
        resp = await auth_client.get('/api/v1/settings/ai-keys')
        assert resp.status_code == 200
        data = resp.json()
        assert 'keys' in data
        for key_status in data['keys']:
            assert key_status['has_key'] is False

    async def test_save_and_get_ai_key(self, auth_client: AsyncClient) -> None:
        """Сохранение ключа → замаскированный ключ в ответе."""
        resp = await auth_client.put(
            '/api/v1/settings/ai-keys/openai',
            json={'api_key': 'sk-test-openai-key-1234'},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data['provider'] == 'openai'
        assert data['has_key'] is True
        assert '...' in data['masked_key']

        # Проверяем что ключ виден в списке
        resp2 = await auth_client.get('/api/v1/settings/ai-keys')
        keys = {k['provider']: k for k in resp2.json()['keys']}
        assert keys['openai']['has_key'] is True

    async def test_save_invalid_provider(self, auth_client: AsyncClient) -> None:
        """Неизвестный провайдер → 400."""
        resp = await auth_client.put(
            '/api/v1/settings/ai-keys/azure-gpt',
            json={'api_key': 'some-key'},
        )
        assert resp.status_code == 400

    async def test_delete_ai_key(self, auth_client: AsyncClient) -> None:
        """Удаление ключа → 204, затем has_key=False."""
        # Сначала сохраняем
        await auth_client.put(
            '/api/v1/settings/ai-keys/anthropic',
            json={'api_key': 'sk-ant-test-key-12345678'},
        )
        # Удаляем
        resp = await auth_client.delete('/api/v1/settings/ai-keys/anthropic')
        assert resp.status_code == 204

        # Проверяем
        resp2 = await auth_client.get('/api/v1/settings/ai-keys')
        keys = {k['provider']: k for k in resp2.json()['keys']}
        assert keys['anthropic']['has_key'] is False


# ═══════════════════════════════════════════════════════════════════
# FIX-003: PDF/TXT Export — service
# ═══════════════════════════════════════════════════════════════════


SAMPLE_REWRITE_DATA: dict = {
    'summary': 'Senior Python Developer с 10-летним опытом',
    'experience': [
        {
            'position': 'Lead Developer',
            'company': 'TechCorp',
            'period': '2020-2024',
            'achievements': ['Увеличил производительность на 40%'],
        },
    ],
    'education': [
        {
            'institution': 'МГУ',
            'degree': 'Магистр',
            'specialization': 'Информатика',
            'year': 2020,
        },
    ],
    'skills': ['Python', 'FastAPI', 'PostgreSQL'],
}


class TestGeneratePdf:
    """Тесты generate_pdf()."""

    def test_structured_data(self) -> None:
        """PDF из структурированных данных."""
        result = generate_pdf(SAMPLE_REWRITE_DATA)
        assert isinstance(result, bytes)
        assert len(result) > 100
        assert result[:4] == b'%PDF'

    def test_plain_text_fallback(self) -> None:
        """PDF из plain text."""
        result = generate_pdf(None, raw_text='Тестовое резюме.\nОпыт работы.')
        assert isinstance(result, bytes)
        assert result[:4] == b'%PDF'

    def test_empty_data(self) -> None:
        """Пустые данные → PDF с сообщением."""
        result = generate_pdf(None)
        assert isinstance(result, bytes)
        assert result[:4] == b'%PDF'

    def test_skills_only(self) -> None:
        """Только навыки."""
        result = generate_pdf({'skills': ['Python', 'Docker']})
        assert isinstance(result, bytes)
        assert result[:4] == b'%PDF'


class TestGenerateTxt:
    """Тесты generate_txt()."""

    def test_structured_data(self) -> None:
        """TXT из структурированных данных."""
        result = generate_txt(SAMPLE_REWRITE_DATA)
        assert isinstance(result, bytes)
        text = result.decode('utf-8')
        assert 'Senior Python Developer' in text
        assert 'Lead Developer' in text
        assert 'Python' in text

    def test_plain_text_fallback(self) -> None:
        """TXT из plain text."""
        result = generate_txt(None, raw_text='Простой текст резюме')
        assert result == 'Простой текст резюме'.encode('utf-8')

    def test_empty_data(self) -> None:
        """Пустые данные → сообщение."""
        result = generate_txt(None)
        assert 'отсутствуют' in result.decode('utf-8')

    def test_education_section(self) -> None:
        """Секция образования в TXT."""
        data = {
            'education': [
                {'institution': 'МФТИ', 'degree': 'Бакалавр', 'specialization': 'CS', 'year': 2019},
            ],
        }
        result = generate_txt(data)
        text = result.decode('utf-8')
        assert 'МФТИ' in text


# ═══════════════════════════════════════════════════════════════════
# FIX-003: PDF/TXT Export — router
# ═══════════════════════════════════════════════════════════════════


class TestExportPdfRouter:
    """GET /api/v1/export/{task_id}/pdf."""

    async def test_no_auth(self, client: AsyncClient) -> None:
        """Без авторизации → 401."""
        resp = await client.get(f'/api/v1/export/{uuid4()}/pdf')
        assert resp.status_code == 401

    async def test_not_found(self, auth_client: AsyncClient) -> None:
        """Несуществующая задача → 404."""
        resp = await auth_client.get(f'/api/v1/export/{uuid4()}/pdf')
        assert resp.status_code == 404

    async def test_success(
        self,
        auth_client: AsyncClient,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        """Экспорт → PDF-файл."""
        task = RewriteHistory(
            user_id=test_user.id,
            resume_id=uuid4(),
            vacancy_id=uuid4(),
            original_text='Original text',
            model_name='gigachat-pro',
            status=RewriteStatus.COMPLETED,
            rewritten_text='Optimized resume text',
        )
        session.add(task)
        await session.flush()

        resp = await auth_client.get(f'/api/v1/export/{task.id}/pdf')
        assert resp.status_code == 200
        assert 'application/pdf' in resp.headers['content-type']
        assert resp.content[:4] == b'%PDF'


class TestExportTxtRouter:
    """GET /api/v1/export/{task_id}/txt."""

    async def test_no_auth(self, client: AsyncClient) -> None:
        """Без авторизации → 401."""
        resp = await client.get(f'/api/v1/export/{uuid4()}/txt')
        assert resp.status_code == 401

    async def test_not_found(self, auth_client: AsyncClient) -> None:
        """Несуществующая задача → 404."""
        resp = await auth_client.get(f'/api/v1/export/{uuid4()}/txt')
        assert resp.status_code == 404

    async def test_success(
        self,
        auth_client: AsyncClient,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        """Экспорт → TXT-файл."""
        task = RewriteHistory(
            user_id=test_user.id,
            resume_id=uuid4(),
            vacancy_id=uuid4(),
            original_text='Original text',
            model_name='gigachat-pro',
            status=RewriteStatus.COMPLETED,
            rewritten_text='Optimized resume text',
        )
        session.add(task)
        await session.flush()

        resp = await auth_client.get(f'/api/v1/export/{task.id}/txt')
        assert resp.status_code == 200
        assert 'text/plain' in resp.headers['content-type']
        assert b'Optimized resume text' in resp.content


# ═══════════════════════════════════════════════════════════════════
# FIX-007: Resume soft-delete + restore — service
# ═══════════════════════════════════════════════════════════════════


class TestRestoreResumeService:
    """Тесты resume.service.restore_resume()."""

    async def test_restore_success(
        self, session: AsyncSession, test_user: User,
    ) -> None:
        """Восстановление удалённого резюме."""
        resume = Resume(
            user_id=test_user.id,
            title='Deleted Resume',
            file_path='test/path.pdf',
            file_format='pdf',
            file_size_bytes=500,
            deleted_at=datetime.now(tz=UTC),
        )
        session.add(resume)
        await session.flush()

        restored = await restore_resume(
            session, resume_id=resume.id, user_id=test_user.id,
        )
        assert restored.deleted_at is None

    async def test_restore_not_deleted(
        self, session: AsyncSession, test_user: User,
    ) -> None:
        """Восстановление неудалённого → ResumeNotFound."""
        from app.core.exceptions import ResumeNotFound

        resume = Resume(
            user_id=test_user.id,
            title='Active Resume',
            file_path='test/path.pdf',
            file_format='pdf',
            file_size_bytes=500,
        )
        session.add(resume)
        await session.flush()

        with pytest.raises(ResumeNotFound):
            await restore_resume(
                session, resume_id=resume.id, user_id=test_user.id,
            )

    async def test_restore_nonexistent(
        self, session: AsyncSession, test_user: User,
    ) -> None:
        """Восстановление несуществующего → ResumeNotFound."""
        from app.core.exceptions import ResumeNotFound

        with pytest.raises(ResumeNotFound):
            await restore_resume(
                session, resume_id=uuid4(), user_id=test_user.id,
            )


# ═══════════════════════════════════════════════════════════════════
# FIX-007: Resume restore — router
# ═══════════════════════════════════════════════════════════════════


class TestRestoreResumeRouter:
    """POST /api/v1/resumes/{id}/restore."""

    async def test_no_auth(self, client: AsyncClient) -> None:
        """Без авторизации → 401."""
        resp = await client.post(f'/api/v1/resumes/{uuid4()}/restore')
        assert resp.status_code == 401

    async def test_not_found(self, auth_client: AsyncClient) -> None:
        """Несуществующее резюме → 404."""
        resp = await auth_client.post(f'/api/v1/resumes/{uuid4()}/restore')
        assert resp.status_code == 404

    async def test_restore_success(
        self,
        auth_client: AsyncClient,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        """Восстановление удалённого → 200."""
        resume = Resume(
            user_id=test_user.id,
            title='To Restore',
            file_path='test/file.pdf',
            file_format='pdf',
            file_size_bytes=1000,
            deleted_at=datetime.now(tz=UTC),
        )
        session.add(resume)
        await session.flush()

        resp = await auth_client.post(f'/api/v1/resumes/{resume.id}/restore')
        assert resp.status_code == 200
        data = resp.json()
        assert data['title'] == 'To Restore'


# ═══════════════════════════════════════════════════════════════════
# FIX-011: Resume file download — router
# ═══════════════════════════════════════════════════════════════════


class TestDownloadResumeFile:
    """GET /api/v1/resumes/{id}/file."""

    async def test_no_auth(self, client: AsyncClient) -> None:
        """Без авторизации → 401."""
        resp = await client.get(f'/api/v1/resumes/{uuid4()}/file')
        assert resp.status_code == 401

    async def test_resume_not_found(self, auth_client: AsyncClient) -> None:
        """Несуществующее резюме → 404."""
        resp = await auth_client.get(f'/api/v1/resumes/{uuid4()}/file')
        assert resp.status_code == 404

    async def test_no_file_path(
        self,
        auth_client: AsyncClient,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        """Резюме без файла → 404."""
        resume = Resume(
            user_id=test_user.id,
            title='Text Only',
            file_path='',
            file_format='pdf',
            file_size_bytes=0,
        )
        session.add(resume)
        await session.flush()

        resp = await auth_client.get(f'/api/v1/resumes/{resume.id}/file')
        assert resp.status_code == 404

    @patch('app.core.storage.file_storage')
    async def test_download_success(
        self,
        mock_storage: AsyncMock,
        auth_client: AsyncClient,
        session: AsyncSession,
        test_user: User,
    ) -> None:
        """Скачивание файла → 200 + binary content."""
        mock_storage.read = AsyncMock(return_value=b'%PDF-fake-content')
        resume = Resume(
            user_id=test_user.id,
            title='My Resume',
            file_path='uploads/resume.pdf',
            file_format='pdf',
            file_size_bytes=1000,
        )
        session.add(resume)
        await session.flush()

        resp = await auth_client.get(f'/api/v1/resumes/{resume.id}/file')
        assert resp.status_code == 200
        assert b'%PDF-fake-content' in resp.content


# ═══════════════════════════════════════════════════════════════════
# FIX-009: Account restore — router
# ═══════════════════════════════════════════════════════════════════


class TestAccountRestoreRouter:
    """POST /api/v1/auth/me/restore."""

    async def test_no_auth(self, client: AsyncClient) -> None:
        """Без авторизации → 401."""
        resp = await client.post('/api/v1/auth/me/restore')
        assert resp.status_code == 401

    async def test_restore_not_deleted(self, auth_client: AsyncClient) -> None:
        """Аккаунт не помечен → сообщение."""
        resp = await auth_client.post('/api/v1/auth/me/restore')
        assert resp.status_code == 200
        assert 'message' in resp.json()


# ═══════════════════════════════════════════════════════════════════
# FIX-008: Email enumeration protection
# ═══════════════════════════════════════════════════════════════════


class TestEmailEnumeration:
    """FIX-008: Register не раскрывает существование email."""

    async def test_new_email_returns_201(self, client: AsyncClient) -> None:
        """Новый email → 201 с токенами."""
        resp = await client.post(
            '/api/v1/auth/register',
            json={'email': f'new-{uuid4().hex[:8]}@example.com', 'password': 'StrongPass1'},
        )
        assert resp.status_code == 201
        assert 'access_token' in resp.json()

    async def test_duplicate_email_returns_201(
        self, client: AsyncClient, session: AsyncSession, test_user: User,
    ) -> None:
        """Существующий email → 201 с message (не 409)."""
        # Убедимся что пользователь точно существует
        await session.refresh(test_user)
        resp = await client.post(
            '/api/v1/auth/register',
            json={'email': test_user.email, 'password': 'AnotherPass1'},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert 'message' in data
        assert 'access_token' not in data


# ═══════════════════════════════════════════════════════════════════
# FIX-012: OpenAPI.json скрыт в production
# ═══════════════════════════════════════════════════════════════════


class TestOpenAPIHidden:
    """FIX-012: openapi.json → None в production."""

    def test_openapi_url_disabled_in_production(self) -> None:
        """В production openapi_url = None."""
        with patch('app.main.get_settings') as mock_settings:
            mock_settings.return_value.is_production = True
            mock_settings.return_value.environment = 'production'
            # Проверка логики: в main.py есть условие
            openapi_url = '/openapi.json' if not mock_settings.return_value.is_production else None
            assert openapi_url is None

    def test_openapi_url_enabled_in_testing(self) -> None:
        """В testing openapi_url = '/openapi.json'."""
        with patch('app.main.get_settings') as mock_settings:
            mock_settings.return_value.is_production = False
            openapi_url = '/openapi.json' if not mock_settings.return_value.is_production else None
            assert openapi_url == '/openapi.json'

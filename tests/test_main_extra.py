"""Дополнительные тесты main.py — error handlers, lifespan."""

from __future__ import annotations

from httpx import ASGITransport, AsyncClient

from app.core.exceptions import HHApiError
from app.main import create_app


class TestAppErrorWithDetail:
    """Тест AppError с полем detail."""

    async def test_app_error_with_detail(self) -> None:
        """AppError с detail → JSON содержит detail."""
        app = create_app()

        # HHApiError имеет detail в конструкторе
        async def _raise_hh_error() -> None:
            raise HHApiError(detail='Connection refused')

        @app.get('/test-error-detail')
        async def trigger_error() -> None:
            await _raise_hh_error()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test') as ac:
            resp = await ac.get('/test-error-detail')

        assert resp.status_code == 502
        data = resp.json()
        assert data['error'] == 'HH_API_ERROR'
        assert data['detail'] == 'Connection refused'

    async def test_general_error_handler(self) -> None:
        """Необработанное исключение → 500 JSON."""
        app = create_app()

        @app.get('/test-unhandled')
        async def trigger_unhandled() -> None:
            msg = 'Something went wrong'
            raise RuntimeError(msg)

        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url='http://test') as ac:
            resp = await ac.get('/test-unhandled')

        assert resp.status_code == 500
        data = resp.json()
        assert data['error'] == 'INTERNAL_ERROR'
        assert data['message'] == 'Внутренняя ошибка сервера'


class TestLifespan:
    """Тесты lifespan (модуль загружается, фабрика работает)."""

    def test_lifespan_defined(self) -> None:
        """Lifespan-контекстменеджер определён и является async."""
        import app.main as main_module

        assert hasattr(main_module, 'lifespan')
        assert callable(main_module.lifespan)

    async def test_lifespan_context_manager(self) -> None:
        """Lifespan можно использовать как async context manager."""
        import app.main as main_module

        app = create_app()
        async with main_module.lifespan(app):
            pass  # startup + shutdown выполнились без ошибок

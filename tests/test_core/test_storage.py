"""Тесты модуля core/storage.py."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from app.core.storage import FileStorage


@pytest.fixture
def tmp_storage(tmp_path: Path) -> FileStorage:
    """FileStorage с временной директорией."""
    return FileStorage(base_dir=str(tmp_path))


class TestFileStorage:
    """Тесты файлового хранилища."""

    async def test_save_and_read(self, tmp_storage: FileStorage) -> None:
        """Сохранение и чтение файла."""
        user_id = uuid4()
        content = b'hello world'
        relative_path = await tmp_storage.save(user_id, 'test.txt', content)
        assert relative_path
        result = await tmp_storage.read(relative_path)
        assert result == content

    async def test_save_creates_user_dir(self, tmp_storage: FileStorage) -> None:
        """Сохранение создаёт директорию пользователя."""
        user_id = uuid4()
        await tmp_storage.save(user_id, 'file.pdf', b'%PDF-data')
        user_dir = tmp_storage._base_dir / str(user_id)
        assert user_dir.exists()

    async def test_delete_file(self, tmp_storage: FileStorage) -> None:
        """Удаление файла."""
        user_id = uuid4()
        relative_path = await tmp_storage.save(user_id, 'del.txt', b'delete me')
        full_path = tmp_storage._base_dir / relative_path
        assert full_path.exists()

        await tmp_storage.delete(relative_path)
        assert not full_path.exists()

    async def test_delete_nonexistent_file(self, tmp_storage: FileStorage) -> None:
        """Удаление несуществующего файла — без ошибки."""
        await tmp_storage.delete('nonexistent/file.txt')  # Не должно падать

    async def test_read_nonexistent_file_raises(self, tmp_storage: FileStorage) -> None:
        """Чтение несуществующего файла → FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            await tmp_storage.read('no/such/file.txt')

    async def test_delete_user_files(self, tmp_storage: FileStorage) -> None:
        """Удаление всех файлов пользователя."""
        user_id = uuid4()
        await tmp_storage.save(user_id, 'a.txt', b'aaa')
        await tmp_storage.save(user_id, 'b.txt', b'bbb')
        user_dir = tmp_storage._base_dir / str(user_id)
        assert user_dir.exists()

        await tmp_storage.delete_user_files(user_id)
        assert not user_dir.exists()

    async def test_multiple_users(self, tmp_storage: FileStorage) -> None:
        """Разные пользователи → разные директории."""
        u1 = uuid4()
        u2 = uuid4()
        p1 = await tmp_storage.save(u1, 'file.txt', b'user1')
        p2 = await tmp_storage.save(u2, 'file.txt', b'user2')
        assert p1 != p2
        assert await tmp_storage.read(p1) == b'user1'
        assert await tmp_storage.read(p2) == b'user2'

    async def test_path_traversal_read_blocked(self, tmp_storage: FileStorage) -> None:
        """SEC-006: Чтение с path traversal → PermissionError."""
        with pytest.raises(PermissionError, match='path traversal'):
            await tmp_storage.read('../../etc/passwd')

    async def test_path_traversal_delete_blocked(self, tmp_storage: FileStorage) -> None:
        """SEC-006: Удаление с path traversal → PermissionError."""
        with pytest.raises(PermissionError, match='path traversal'):
            await tmp_storage.delete('../../../root/.ssh/id_rsa')

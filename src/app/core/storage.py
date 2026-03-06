"""Абстракция файлового хранилища (Local FS → MinIO/S3 в production)."""

from __future__ import annotations

import shutil
from pathlib import Path
from uuid import UUID

from app.core.config import get_settings

settings = get_settings()


class FileStorage:
    """Локальное файловое хранилище с Docker volume."""

    def __init__(self, base_dir: str | None = None) -> None:
        self._base_dir = Path(base_dir or settings.upload_dir).resolve()
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def _user_dir(self, user_id: UUID) -> Path:
        """Директория пользователя."""
        user_dir = self._base_dir / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir

    def _safe_resolve(self, relative_path: str) -> Path:
        """Безопасное разрешение пути с защитой от path traversal (SEC-006)."""
        file_path = (self._base_dir / relative_path).resolve()
        if not str(file_path).startswith(str(self._base_dir)):
            msg = 'Access denied: path traversal detected'
            raise PermissionError(msg)
        return file_path

    async def save(
        self,
        user_id: UUID,
        filename: str,
        content: bytes,
    ) -> str:
        """Сохранение файла. Возвращает относительный путь."""
        user_dir = self._user_dir(user_id)
        file_path = user_dir / filename
        file_path.write_bytes(content)
        return str(file_path.relative_to(self._base_dir))

    async def read(self, relative_path: str) -> bytes:
        """Чтение файла по относительному пути."""
        file_path = self._safe_resolve(relative_path)
        if not file_path.exists():
            msg = f'File not found: {relative_path}'
            raise FileNotFoundError(msg)
        return file_path.read_bytes()

    async def delete(self, relative_path: str) -> None:
        """Удаление файла."""
        file_path = self._safe_resolve(relative_path)
        if file_path.exists():
            file_path.unlink()

    async def delete_user_files(self, user_id: UUID) -> None:
        """Удаление всех файлов пользователя."""
        user_dir = self._user_dir(user_id)
        if user_dir.exists():
            shutil.rmtree(user_dir)


file_storage = FileStorage()

import io
import os
from unittest.mock import patch

import pytest
from fastapi import UploadFile


@pytest.fixture
def mock_file_upload():
    """Мок для тестирования загрузки файлов."""
    def _create_upload_file(content: bytes, filename: str, content_type: str):
        return UploadFile(
            file=io.BytesIO(content),
            filename=filename,
            headers={"content-type": content_type}
        )
    return _create_upload_file


@pytest.fixture
def large_file_content():
    """Создает содержимое большого файла для тестов."""
    return b"x" * (10 * 1024 * 1024)  # 10MB


@pytest.fixture
def invalid_file_types():
    """Список недопустимых типов файлов для тестов."""
    return [
        ("virus.exe", "application/x-executable"),
        ("script.js", "application/javascript"),
        ("archive.zip", "application/zip"),
        ("document.doc", "application/msword"),
    ]


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Автоматическая настройка тестового окружения."""
    # Устанавливаем переменные окружения для тестов
    with patch.dict(os.environ, {
        "TODO_JWT_SECRET": "test_secret_key",
        "TODO_JWT_ALG": "HS256",
        "TODO_JWT_EXP": "60",
        "DATABASE_HOSTNAME": "localhost",
        "DATABASE_CREDENTIALS": "test:test",
        "DATABASE_NAME": "test_db",
        "DATABASE_PORT": "5432"
    }):
        yield

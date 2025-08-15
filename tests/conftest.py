import os
import shutil
import tempfile
from typing import Any, Dict, Generator
from unittest.mock import MagicMock, Mock

import httpx
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Создает тестовый клиент для FastAPI приложения."""
    # Импортируем ваше приложение - замените на актуальный путь
    # from main import app
    # return TestClient(app)

    # Для демонстрации используем мок
    mock_client = Mock(spec=TestClient)
    return mock_client


@pytest.fixture
def auth_headers():
    """Возвращает заголовки авторизации для тестов."""
    return {"Authorization": "Bearer test_access_token"}


@pytest.fixture
def user_data():
    """Тестовые данные пользователя."""
    return {
        "username": "testuser",
        "password": "testpassword123"
    }


@pytest.fixture(scope="session")
def temp_dir() -> Generator[str, None, None]:
    """Создает временную директорию для тестов."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture(scope="session")
def app_config():
    """Конфигурация приложения для тестов."""
    return {
        "DATABASE_URL": "sqlite:///./test.db",
        "SECRET_KEY": "test_secret_key",
        "ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
        "FILE_UPLOAD_PATH": "/tmp/test_uploads"
    }


@pytest.fixture(scope="function")
def mock_database():
    """Мок базы данных для изоляции тестов."""
    db_mock = MagicMock()

    # Мокаем основные операции БД
    db_mock.query.return_value = db_mock
    db_mock.filter.return_value = db_mock
    db_mock.first.return_value = None
    db_mock.all.return_value = []
    db_mock.count.return_value = 0

    return db_mock


@pytest.fixture(scope="function")
def authenticated_user():
    """Фикстура аутентифицированного пользователя."""
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "is_active": True,
        "created_at": "2025-08-15T12:00:00Z"
    }


@pytest.fixture(scope="function")
def sample_tasks():
    """Фикстура с примерами задач для тестов."""
    return [
        {
            "id": 1,
            "name": "Task 1",
            "text": "Description for task 1",
            "completed": False,
            "created_at": "2025-08-15T10:00:00Z",
            "user_id": 1
        },
        {
            "id": 2,
            "name": "Task 2",
            "text": "Description for task 2",
            "completed": True,
            "created_at": "2025-08-15T11:00:00Z",
            "user_id": 1
        },
        {
            "id": 3,
            "name": "Shared Task",
            "text": "This task is shared",
            "completed": False,
            "created_at": "2025-08-15T09:00:00Z",
            "user_id": 2
        }
    ]


@pytest.fixture(scope="function")
def mock_file_system(temp_dir):
    """Мок файловой системы для тестов загрузки файлов."""
    upload_dir = os.path.join(temp_dir, "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    return {
        "upload_dir": upload_dir,
        "allowed_extensions": {".txt", ".pdf", ".doc", ".docx", ".jpg", ".png"},
        "max_file_size": 10 * 1024 * 1024  # 10MB
    }


@pytest.fixture(scope="function")
def api_responses():
    """Стандартные API ответы для мокирования."""
    return {
        "success": {"status": "success", "message": "Operation completed successfully"},
        "created": {"status": "created", "message": "Resource created successfully"},
        "not_found": {"detail": "Resource not found"},
        "unauthorized": {"detail": "Not authenticated"},
        "forbidden": {"detail": "Not enough permissions"},
        "validation_error": {
            "detail": [
                {
                    "loc": ["body", "field"],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ]
        }
    }


@pytest.fixture(scope="function")
def mock_jwt_service():
    """Мок сервиса JWT токенов."""
    jwt_mock = Mock()
    jwt_mock.create_access_token.return_value = "test_access_token"
    jwt_mock.verify_token.return_value = {"sub": "testuser", "user_id": 1}
    jwt_mock.get_current_user.return_value = {
        "id": 1,
        "username": "testuser",
        "is_active": True
    }
    return jwt_mock


@pytest.fixture(scope="function")
def mock_password_service():
    """Мок сервиса работы с паролями."""
    pwd_mock = Mock()
    pwd_mock.hash_password.return_value = "hashed_password"
    pwd_mock.verify_password.return_value = True
    return pwd_mock


# Хуки pytest для дополнительной конфигурации
def pytest_configure(config):
    """Конфигурация pytest при запуске."""
    config.addinivalue_line(
        "markers", "auth: mark test as authentication related"
    )
    config.addinivalue_line(
        "markers", "database: mark test as database related"
    )


def pytest_collection_modifyitems(config, items):
    """Модификация собранных тестов."""
    for item in items:
        # Автоматическая пометка тестов маркерами на основе имени
        if "auth" in item.name:
            item.add_marker(pytest.mark.auth)
        elif "task" in item.name:
            item.add_marker(pytest.mark.tasks)
        elif "shar" in item.name:
            item.add_marker(pytest.mark.sharing)
        elif "file" in item.name:
            item.add_marker(pytest.mark.files)

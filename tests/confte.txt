import os
import shutil
import tempfile
from typing import Any, Dict, Generator
from unittest.mock import MagicMock, Mock

import pytest


@pytest.fixture
def client():
    """Создает мок тестового клиента для FastAPI приложения."""
    mock_client = Mock()

    # Настройка базовых методов HTTP
    mock_client.post = Mock()
    mock_client.get = Mock()
    mock_client.put = Mock()
    mock_client.patch = Mock()
    mock_client.delete = Mock()

    return mock_client


@pytest.fixture
def auth_headers():
    """Возвращает заголовки авторизации для тестов."""
    return {"Authorization": "Bearer test_access_token"}


@pytest.fixture
def user_data():
    """Тестовые данные пользователя с валидным паролем."""
    return {
        "username": "testuser",
        "password": "TestPassword123"  # Соответствует требованиям валидации
    }


@pytest.fixture
def invalid_user_data():
    """Данные пользователя с невалидным паролем для тестов валидации."""
    return {
        "username": "testuser",
        "password": "weak"  # Не соответствует требованиям
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
        "TODO_JWT_SECRET": "test_secret_key_for_testing",
        "TODO_JWT_ALG": "HS256",
        "TODO_JWT_EXP": 30,
        "FILE_UPLOAD_PATH": "/tmp/test_uploads"
    }


@pytest.fixture(scope="function")
def mock_database():
    """Мок базы данных для изоляции тестов."""
    db_mock = MagicMock()

    # Мокаем основные операции БД
    db_mock.query.return_value = db_mock
    db_mock.filter.return_value = db_mock
    db_mock.join.return_value = db_mock
    db_mock.first.return_value = None
    db_mock.one_or_none.return_value = None
    db_mock.all.return_value = []
    db_mock.count.return_value = 0
    db_mock.offset.return_value = db_mock
    db_mock.limit.return_value = db_mock
    db_mock.order_by.return_value = db_mock
    db_mock.scalar_one_or_none.return_value = None

    # Методы для изменения данных
    db_mock.add = Mock()
    db_mock.delete = Mock()
    db_mock.commit = Mock()
    db_mock.rollback = Mock()
    db_mock.refresh = Mock()
    db_mock.close = Mock()

    return db_mock


@pytest.fixture(scope="function")
def authenticated_user():
    """Фикстура аутентифицированного пользователя."""
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "disabled": False,
        "password": b"hashed_password_bytes"
    }


@pytest.fixture(scope="function")
def sample_tasks():
    """Фикстура с примерами задач для тестов."""
    return [
        {
            "id": 1,
            "name": "Task 1",
            "text": "Description for task 1",
            "completion_status": False,
            "date_time": "2025-08-15T10:00:00",
            "user_id": 1,
            "file_data": None,
            "file_name": None
        },
        {
            "id": 2,
            "name": "Task 2",
            "text": "Description for task 2",
            "completion_status": True,
            "date_time": "2025-08-15T11:00:00",
            "user_id": 1,
            "file_data": b"file_content",
            "file_name": "test.txt"
        },
        {
            "id": 3,
            "name": "Shared Task",
            "text": "This task is shared",
            "completion_status": False,
            "date_time": "2025-08-15T09:00:00",
            "user_id": 2,
            "file_data": None,
            "file_name": None
        }
    ]


@pytest.fixture(scope="function")
def sample_shares():
    """Фикстура с примерами совместного доступа."""
    return [
        {
            "id": 1,
            "task_id": 3,
            "owner_id": 2,
            "target_user_id": 1,
            "permission_level": "view",
            "date_time": "2025-08-15T09:30:00"
        },
        {
            "id": 2,
            "task_id": 1,
            "owner_id": 1,
            "target_user_id": 3,
            "permission_level": "edit",
            "date_time": "2025-08-15T10:30:00"
        }
    ]


@pytest.fixture(scope="function")
def mock_file_system(temp_dir):
    """Мок файловой системы для тестов загрузки файлов."""
    upload_dir = os.path.join(temp_dir, "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    return {
        "upload_dir": upload_dir,
        "allowed_extensions": {".txt", ".pdf", ".doc", ".docx", ".jpg", ".png", ".jpeg"},
        "allowed_types": {"text/plain", "application/pdf", "image/jpeg", "image/png"},
        "max_file_size": 20 * 1024 * 1024  # 20MB
    }


@pytest.fixture(scope="function")
def api_responses():
    """Стандартные API ответы для мокирования."""
    return {
        "success": {"msg": "Операция выполнена успешно"},
        "created": {"msg": "Ресурс создан успешно"},
        "not_found": {"detail": [{"msg": "Задача не найдена"}]},
        "unauthorized": {"detail": [{"msg": "Не удалось подтвердить учетные данные"}]},
        "forbidden": {"detail": [{"msg": "Задача не найдена или не принадлежит вам"}]},
        "validation_error": {
            "detail": [
                {
                    "msg": "Имя задачи не задано",
                    "loc": ["name"],
                    "type": "value_error",
                }
            ]
        },
        "user_not_found": {"detail": [{"msg": "Пользователь 'username' не найден"}]},
        "task_already_shared": {"detail": [{"msg": "Доступ к задаче уже предоставлен пользователю 'username'"}]},
        "file_empty": {"detail": [{"msg": "файл пуст"}]},
        "invalid_file_extension": {"detail": [{"msg": "Недопустимое расширение файла: .exe"}]}
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
        "disabled": False
    }
    return jwt_mock


@pytest.fixture(scope="function")
def mock_password_service():
    """Мок сервиса работы с паролями."""
    pwd_mock = Mock()
    pwd_mock.hash_password.return_value = b"hashed_password_bytes"
    pwd_mock.verify_password.return_value = True
    pwd_mock.get_hash_password.return_value = b"hashed_password_bytes"
    return pwd_mock


@pytest.fixture
def task_owner():
    """Фикстура владельца задачи."""
    return {
        "id": 1,
        "username": "task_owner",
        "email": "owner@example.com",
        "disabled": False
    }


@pytest.fixture
def collaborator_user():
    """Фикстура пользователя-коллаборатора."""
    return {
        "id": 2,
        "username": "collaborator",
        "email": "collaborator@example.com",
        "disabled": False
    }


@pytest.fixture
def valid_file_data():
    """Фикстура с валидными данными файла."""
    return {
        "filename": "test_document.pdf",
        "content": b"PDF file content here",
        "content_type": "application/pdf",
        "size": 1024  # 1KB
    }


@pytest.fixture
def invalid_file_data():
    """Фикстура с невалидными данными файла."""
    return {
        "filename": "malware.exe",
        "content": b"Executable content",
        "content_type": "application/octet-stream",
        "size": 25 * 1024 * 1024  # 25MB - превышает лимит
    }


# Хуки pytest для дополнительной конфигурации
def pytest_configure(config):
    """Конфигурация pytest при запуске."""
    config.addinivalue_line(
        "markers", "auth: mark test as authentication related"
    )
    config.addinivalue_line(
        "markers", "tasks: mark test as tasks related"
    )
    config.addinivalue_line(
        "markers", "sharing: mark test as sharing related"
    )
    config.addinivalue_line(
        "markers", "files: mark test as file operations related"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Модификация собранных тестов."""
    for item in items:
        # Автоматическая пометка тестов маркерами на основе имени
        if "auth" in item.name.lower():
            item.add_marker(pytest.mark.auth)
        elif "task" in item.name.lower():
            item.add_marker(pytest.mark.tasks)
        elif "shar" in item.name.lower():
            item.add_marker(pytest.mark.sharing)
        elif "file" in item.name.lower():
            item.add_marker(pytest.mark.files)
        elif "integration" in item.name.lower() or "workflow" in item.name.lower():
            item.add_marker(pytest.mark.integration)


@pytest.fixture(autouse=True)
def reset_mocks():
    """Автоматический сброс моков после каждого теста."""
    yield
    # Здесь можно добавить логику очистки моков если потребуется


# Фикстуры для специфичных сценариев тестирования
@pytest.fixture
def empty_task_list_response():
    """Ответ для пустого списка задач."""
    return {"tasks": [], "skip": 0, "limit": 100}


@pytest.fixture
def task_stats_response():
    """Ответ со статистикой задач."""
    return {
        "total_tasks": 10,
        "completed_tasks": 6,
        "uncompleted_tasks": 4,
        "completion_percentage": 60.0
    }


@pytest.fixture
def sharing_permissions_response():
    """Ответ с разрешениями для совместного доступа."""
    return {
        "can_view": True,
        "can_edit": True,
        "can_delete": False,
        "can_share": False,
        "can_upload_files": True,
        "can_change_status": True,
        "is_owner": False
    }

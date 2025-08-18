import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.auth.schemas import UserRegisterSchema
from src.auth.service import create
from src.core.database import Base, get_db
from src.main import app
from src.sharing.models import Share
from src.sharing.share.service import share_task_service
from src.tasks.crud.service import create_task_service

# Конфигурация тестовой базы данных
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Переопределение зависимости БД для тестов."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db_session():
    """Фикстура сессии БД для тестов."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Фикстура тестового клиента."""
    app.dependency_overrides[get_db] = override_get_db

    # Создаем таблицы
    Base.metadata.create_all(bind=engine)

    with TestClient(app) as test_client:
        yield test_client

    # Очищаем таблицы после тестов
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Создает тестового пользователя."""
    user_data = UserRegisterSchema(
        username="testuser",
        password="Password123"
    )
    return create(session=db_session, user_in=user_data)


@pytest.fixture
def test_user2(db_session):
    """Создает второго тестового пользователя."""
    user_data = UserRegisterSchema(
        username="testuser2",
        password="Password123"
    )
    return create(session=db_session, user_in=user_data)


@pytest.fixture
def auth_headers(test_user):
    """Возвращает заголовки авторизации."""
    token = test_user.get_token
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers2(test_user2):
    """Возвращает заголовки авторизации для второго пользователя."""
    token = test_user2.get_token
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_task(db_session, test_user):
    """Создает тестовую задачу."""
    return create_task_service(
        session=db_session,
        current_user_id=test_user.id,
        task_name="Test Task",
        task_text="Test description"
    )


@pytest.fixture
def shared_task(db_session, test_user, test_user2, test_task):
    """Создает расшаренную задачу."""
    share_task_service(
        session=db_session,
        owner_id=test_user.id,
        task_id=test_task.id,
        target_username=test_user2.username,
        permission_level="edit"
    )
    return test_task


@pytest.fixture
def temp_file():
    """Создает временный файл для тестов загрузки."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        tmp.write(b"Test file content")
        tmp.flush()
        yield tmp.name
    os.unlink(tmp.name)

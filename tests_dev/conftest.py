import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.auth.schemas import UserRegisterSchema
from src.auth.service import get_user_by_username, register_service
from src.core.database import Base, get_db
from src.main import app
from src.sharing.share.service import share_task_service
from src.tasks.crud.service import create_task_service

# -------------------------
# Конфигурация тестовой БД
# -------------------------
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)


# -------------------------
# Переопределение зависимости БД
# -------------------------
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------
# Фикстура сессии БД
# -------------------------
@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# -------------------------
# Тестовый клиент
# -------------------------
@pytest.fixture(scope="function")
def client(db_session):
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# -------------------------
# Фикстуры пользователей
# -------------------------
@pytest.fixture
def test_user(db_session):
    user_data = UserRegisterSchema(username="testuser", password="Password123")
    register_service(session=db_session,
                     username=user_data.username, password=user_data.password)
    return get_user_by_username(session=db_session, username=user_data.username)


@pytest.fixture
def test_user2(db_session):
    user_data = UserRegisterSchema(
        username="testuser2", password="Password123")
    register_service(session=db_session,
                     username=user_data.username, password=user_data.password)
    return get_user_by_username(session=db_session, username=user_data.username)


@pytest.fixture
def auth_headers(test_user):
    token = test_user.token()
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers2(test_user2):
    token = test_user2.token()
    return {"Authorization": f"Bearer {token}"}


# -------------------------
# Фикстуры задач
# -------------------------
@pytest.fixture
def test_task(db_session, test_user):
    return create_task_service(
        session=db_session,
        current_user_id=test_user.id,
        task_name="Test Task",
        task_text="Test description"
    )


@pytest.fixture
def shared_task(db_session, test_user, test_user2, test_task):
    share_task_service(
        session=db_session,
        owner_id=test_user.id,
        task_id=test_task.id,
        target_username=test_user2.username,
        permission_level="edit"
    )
    return test_task


# -------------------------
# Временные файлы
# -------------------------
@pytest.fixture
def temp_file():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        tmp.write(b"Test file content")
        tmp.flush()
        yield tmp.name
    os.unlink(tmp.name)

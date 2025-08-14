import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.auth.models import ToDoUser
from src.auth.service import get_current_user
from src.core.database import Base, get_db
from src.main import app

TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={
                       "check_same_thread": False})
TestingSessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def create_test_user(client=client):
    client.post("/auth/register", json={
        "username": "testuser",
        "password": "123456aA"
    })
    resp = client.post("/auth/login", data={
        "username": "testuser",
        "password": "123456aA"
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return token, headers


@pytest.fixture
def token(client):
    return create_test_user(client)[0]


@pytest.fixture
def headers(client):
    return create_test_user(client)[1]


def get_user(db, token) -> ToDoUser:
    return get_current_user(session=db, token=token)

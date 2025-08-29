
import asyncio
import os
import tempfile
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, event
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.pool import NullPool, StaticPool

from src.auth.schemas import UserRegisterSchema
from src.auth.service import get_user_by_username, register_service
from src.common.models import *  # Импортируйте ваши модели
from src.core.database import Base, get_db  # Измените на ваши импорты
from src.main import app  # Измените на ваш путь к FastAPI приложению
from src.sharing.share.service import share_task_service
from src.tasks.crud.service import create_task_service

# Настройка базы данных для тестов
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
# Альтернативно для in-memory базы:
# TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Создает event loop для всей сессии тестов"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def async_engine():
    """Создает async engine для тестов"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
        },
    )

    # Создаем все таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Очищаем после тестов
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def async_session(async_engine):
    """Создает async session для каждого теста"""
    async_session_maker = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(async_session):
    """Создает HTTP клиент для тестирования API"""

    # Переопределяем зависимость базы данных
    async def override_get_db():
        yield async_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    # Очищаем переопределения после теста
    app.dependency_overrides.clear()


@pytest.fixture
async def db_session(async_session):
    """Алиас для async_session для удобства"""
    return async_session

# -------------------------
# Фикстуры пользователей
# -------------------------


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    user_data = UserRegisterSchema(username="testuser", password="Password123")
    await register_service(
        session=db_session,
        username=user_data.username,
        password=user_data.password
    )
    return await get_user_by_username(
        session=db_session, username=user_data.username
    )


@pytest_asyncio.fixture
async def test_user2(db_session: AsyncSession):
    user_data = UserRegisterSchema(
        username="testuser2", password="Password123")
    await register_service(
        session=db_session,
        username=user_data.username,
        password=user_data.password
    )
    return await get_user_by_username(
        session=db_session, username=user_data.username
    )


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


@pytest_asyncio.fixture
async def test_task(db_session: AsyncSession, test_user):
    return await create_task_service(
        session=db_session,
        current_user_id=test_user.id,
        task_name="Test Task",
        task_text="Test description"
    )


@pytest_asyncio.fixture
async def shared_task(db_session: AsyncSession, test_user, test_user2, test_task):
    await share_task_service(
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

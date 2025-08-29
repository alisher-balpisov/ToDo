import asyncio
import os
import tempfile
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.pool import StaticPool

from src.auth.models import User
from src.auth.schemas import UserRegisterSchema
from src.auth.service import get_user_by_username, register_service
from src.core.database import Base, get_db
from src.main import app
from src.sharing.share.service import share_task_service
from src.tasks.crud.service import create_task_service

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# -------------------------
# Event loop
# -------------------------


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# -------------------------
# Async Engine и Session
# -------------------------


@pytest.fixture(scope="session")
async def async_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function", autouse=True)
async def truncate_tables(async_engine):
    async with async_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    yield


@pytest.fixture
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session_maker = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session

# -------------------------
# HTTP Client
# -------------------------


@pytest.fixture
async def client(async_engine):
    async_session_maker = async_sessionmaker(
        bind=async_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

# -------------------------
# Пользователи
# -------------------------


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    await db_session.execute(delete(User))
    await db_session.commit()

    user_data = UserRegisterSchema(username="testuser", password="Password123")
    await register_service(session=db_session, username=user_data.username, password=user_data.password)
    return await get_user_by_username(session=db_session, username=user_data.username)


@pytest_asyncio.fixture
async def test_user2(db_session: AsyncSession, test_user):
    user_data = UserRegisterSchema(
        username="testuser2", password="Password123")
    await register_service(session=db_session, username=user_data.username, password=user_data.password)
    return await get_user_by_username(session=db_session, username=user_data.username)


@pytest_asyncio.fixture
async def auth_headers(test_user):
    token = test_user.token()
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def auth_headers2(test_user2):
    token = test_user2.token()
    return {"Authorization": f"Bearer {token}"}

# -------------------------
# Задачи
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

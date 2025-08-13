from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import or_

from src.auth.models import ToDoUser, get_hash_password
from src.auth.schemas import TokenDataSchema, UserRegisterSchema
from src.core.config import TODO_JWT_ALG, TODO_JWT_SECRET
from src.core.database import DbSession
from src.tasks.crud.service import *

from .conftest import db


def create_test_user(client):
    # Регистрируем пользователя
    client.post("/auth/register", json={
        "username": "testuser",
        "password": "123456aA"
    })
    # Логинимся
    resp = client.post("/auth/login", data={
        "username": "testuser",
        "password": "123456aA"
    })
    print(resp.status_code)
    print(resp.json())
    token = resp.json()["access_token"]
    return token, {"Authorization": f"Bearer {token}"}


def get_user_by_username(session, username: str) -> ToDoUser | None:
    """Возвращает объект User, основанный на username пользователя."""
    return session.query(ToDoUser).filter(ToDoUser.username == username).one_or_none()


def credentials_exception():
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=[{"msg": "Не удалось подтвердить учетные данные"}],
        headers={"WWW-Authenticate": "Bearer"}
    )


async def get_current_user(
        token: str,
        db=db
) -> ToDoUser:
    try:
        payload = jwt.decode(token, TODO_JWT_SECRET, algorithms=[TODO_JWT_ALG])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception()
        token_data = TokenDataSchema(username=username)
    except JWTError:
        raise credentials_exception()

    user = get_user_by_username(
        session=db, username=token_data.username)
    if user is None:
        raise credentials_exception()
    return user


def test_create_task(client, db):
    task_name = "My Task"
    task_text = "My text"
    token, headers = create_test_user(client)
    # test endpoint
    payload = {
        "name": f"{task_name}",
        "text": f"{task_text}"
    }

    user_id = 1
    resp = client.post("/tasks/", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["msg"] == "Задача добавлена"
    assert isinstance(data["task_id"], int)

    # test service
    user: ToDoUser = get_current_user(token=token)
    new_task = create_task_service(session=db,
                                   current_user_id=user.id,
                                   task_name=task_name,
                                   task_text=task_text)
    assert isinstance(new_task, Task)
    assert new_task.id is not None
    assert new_task.name == task_name
    assert new_task.text == task_text
    assert new_task.completion_status is False
    assert new_task.user_id == user_id
    assert isinstance(new_task.date_time, datetime)

    end_task, service_task = db.query(Task).filter(
        or_(
            Task.id == new_task.id,
            Task.id == data["task_id"]
        )).all()
    print(db_task)
    assert end_task is not None and service_task is not None
    assert end_task.name == task_name

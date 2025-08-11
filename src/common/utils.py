from typing import Any

from fastapi import HTTPException, UploadFile, status

from src.auth.models import ToDoUser
from src.common.models import Task

MAX_FILE_SIZE_MB = 20
MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024


def get_task(session, task_id: int) -> Task:
    return session.query(Task).filter(
        Task.id == task_id
    ).first()


def get_task_user(session, task_id: int) -> ToDoUser:
    return session.query(ToDoUser).join(
        Task, Task.user_id == ToDoUser.id).filter(
        Task.id == task_id
    ).one_or_none()


def get_user_task(session, user_id: int, task_id: int) -> Task:
    return session.Query(Task).filter(
        Task.user_id == user_id,
        Task.id == task_id
    ).one_or_none()


def is_user_task(session, user_id: int, task_id: int) -> bool:
    return session.query(Task).filter(
        Task.user_id == user_id,
        Task.id == task_id
    ).one_or_none() is not None


def map_sort_rules(sort: list, sort_mapping: dict[str, Any]) -> list:
    return [sort_mapping[rule]
            for rule in sort
            if rule in sort_mapping]


async def validate_and_read_file(uploaded_file: UploadFile) -> bytes:
    file_data = await uploaded_file.read()
    if len(file_data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=[{"msg": "Размер файла превышает максимально допустимый (20MB)"}],
        )
    return file_data


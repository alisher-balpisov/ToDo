import os

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.common.models import Task
from src.core.config import settings
from src.core.exception import (InvalidInputException,
                                MissingRequiredFieldException,
                                ValidationException)


async def get_task(session: AsyncSession, task_id: int) -> Task | None:
    result = await session.execute(
        select(Task).where(Task.id == task_id)
    )
    return result.scalar_one_or_none()


async def get_task_user(session: AsyncSession, task_id: int) -> User | None:
    result = await session.execute(
        select(User)
        .join(Task, Task.user_id == User.id)
        .where(Task.id == task_id)
    )
    return result.scalar_one_or_none()


async def get_user_task(session: AsyncSession, user_id: int, task_id: int) -> Task | None:
    result = await session.execute(
        select(Task).where(Task.user_id == user_id, Task.id == task_id)
    )
    return result.scalar_one_or_none()


async def is_task_owner(session: AsyncSession, user_id: int, task_id: int) -> bool:
    result = await session.execute(
        select(Task).where(Task.user_id == user_id, Task.id == task_id)
    )
    return result.scalar_one_or_none() is not None


def map_sort_rules(sort: list, sort_mapping) -> list:
    return [sort_mapping[rule] for rule in sort if rule in sort_mapping]


async def validate_and_read_file(uploaded_file: UploadFile) -> bytes:
    filename = uploaded_file.filename
    if not filename:
        raise MissingRequiredFieldException("имя файла")

    safe_filename = os.path.basename(filename.strip())
    if safe_filename != filename.strip():
        raise InvalidInputException(
            "имя файла", filename, "допустимое имя файла")

    extension = os.path.splitext(filename)[1].lower()
    if extension not in settings.ALLOWED_EXTENSIONS:
        raise InvalidInputException(
            "расширение файла", extension, "допустимое расширение")

    if uploaded_file.content_type not in settings.ALLOWED_TYPES:
        raise InvalidInputException(
            "тип файла", uploaded_file.content_type, "допустимый тип файла")

    file_data = await uploaded_file.read()

    if not file_data:
        raise InvalidInputException("файл", "пустой файл", "непустой файл")

    if len(file_data) > settings.MAX_FILE_SIZE:
        raise ValidationException(
            f"Размер файла превышает максимально допустимый ({settings.MAX_FILE_SIZE_MB}MB)")

    return file_data

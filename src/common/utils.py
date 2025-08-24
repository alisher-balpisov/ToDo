import logging
import os
from functools import wraps

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from src.auth.models import User
from src.common.models import Task
from src.constants import ALLOWED_TYPES
from src.core.config import settings
from src.exceptions import FILE_EMPTY


def get_task(session, task_id: int) -> Task:
    return session.query(Task).filter(
        Task.id == task_id
    ).first()


def get_task_user(session, task_id: int) -> User:
    return (session.query(User)
            .join(Task, Task.user_id == User.id)
            .filter(Task.id == task_id)
            .one_or_none())


def get_user_task(session, user_id: int, task_id: int) -> Task:
    return session.query(Task).filter(
        Task.user_id == user_id,
        Task.id == task_id
    ).one_or_none()


def is_task_owner(session, user_id: int, task_id: int) -> bool:
    return session.query(Task).filter(
        Task.user_id == user_id,
        Task.id == task_id
    ).one_or_none() is not None


def map_sort_rules(sort: list, sort_mapping) -> list:
    return [sort_mapping[rule]
            for rule in sort
            if rule in sort_mapping]


async def validate_and_read_file(uploaded_file: UploadFile) -> bytes:
    filename = uploaded_file.filename
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"msg": "Файл не имеет имени"},
        )

    safe_filename = os.path.basename(filename.strip())
    if safe_filename != filename.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"msg": "Недопустимое имя файла"},
        )

    ext = os.path.splitext(filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={"msg": f"Недопустимое расширение файла: {ext}"},
        )

    if uploaded_file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={"msg": f"Недопустимый тип файла: {uploaded_file.content_type}"}
        )

    file_data = await uploaded_file.read()

    if not file_data:
        raise FILE_EMPTY

    if len(file_data) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "msg": f"Размер файла превышает максимально допустимый ({settings.MAX_FILE_SIZE_MB}MB)"},
        )

    return file_data

logger = logging.getLogger(__name__)


def handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Логируем с полным стеком
            logger.exception("[handler] Ошибка в '%s': %s",
                             func.__name__, str(e), exc_info=True)
            raise
    return wrapper


def transactional(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        session = kwargs.get("session")
        if session is None and args:
            session = args[0]

        if session is None:
            raise ValueError(
                f"[transactional] В функции '{func.__name__}' не найден аргумент 'session'. "
                f"Передайте его как первый позиционный аргумент или keyword-аргумент."
            )

        if not isinstance(session, Session):
            raise TypeError(
                f"[transactional] В функции '{func.__name__}' ожидается объект класса 'Session', "
                f"но получен {type(session).__name__}."
            )

        try:
            result = func(*args, **kwargs)
            session.commit()
            return result
        except Exception:
            session.rollback()
            raise
    return wrapper

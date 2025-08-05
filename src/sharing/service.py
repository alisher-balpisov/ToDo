from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, status

from src.auth.models import ToDoUser
from src.auth.service import CurrentUser, get_user_by_username
from src.core.database import DbSession, PrimaryKey, UsernameStr
from src.core.exceptions import handle_server_exception
from src.db.models import SharedAccessEnum, Task, TaskShare
from src.db.schemas import TaskShareSchema


def get_task(session, task_id: int):
    return session.query(Task).filter(
        Task.id == task_id
    ).first()


def is_owned_task(session, owner_id: int, task_id: int) -> bool:
    return session.query(Task).filter(
        Task.id == task_id,
        Task.user_id == owner_id
    ).first() is not None


def is_sharing_with_self(owner_id: int, target_user_id: int) -> bool:
    return owner_id == target_user_id


def is_already_shared(session, target_user_id: int, task_id: int) -> bool:
    return session.query(TaskShare).filter(
        TaskShare.task_id == task_id,
        TaskShare.target_user_id == target_user_id,
    ).first() is not None


def share_task_service(
        session,
        owner_id: int,
        task_id: int,
        target_username: str,
        permission_level: SharedAccessEnum
) -> None:

    if not is_owned_task(session, owner_id, task_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Задача не найдена или не принадлежит вам"
        )

    target_user = get_user_by_username(session, target_username)

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Пользователь '{target_username}' не найден"
        )

    if is_sharing_with_self(owner_id, target_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя делиться задачей с самим собой"
        )

    if is_already_shared(session, target_user.id, task_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Доступ к задаче уже предоставлен пользователю '{target_username}'"
        )
    new_share = TaskShare(
        task_id=task_id,
        owner_id=owner_id,
        target_user_id=target_user.id,
        permission_level=permission_level,
    )
    session.add(new_share)
    session.commit()


def get_shared_access(
        session,
        owner_id: int,
        task_id: int,
        target_user_id: int
) -> TaskShare:
    return session.query(TaskShare).filter(
        TaskShare.task_id == task_id,
        TaskShare.owner_id == owner_id,
        TaskShare.target_user_id == target_user_id,
    ).first()


def unshare_task_service(
        session: DbSession,
        owner_id: int,
        task_id: int,
        target_username: str
) -> None:
    if not is_owned_task(session, owner_id, task_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Задача не найдена или не принадлежит вам"
        )

    target_user = get_user_by_username(session, target_username)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Пользователь '{target_username}' не найден"
        )

    share = get_shared_access(
        session, task_id, owner_id, target_user.id)
    if not share:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Эта задача не расшарена с пользователем {target_username}"
        )
    session.delete(share)
    session.commit()


def update_share_permission_service(
        session,
        owner_id: int,
        new_permission: SharedAccessEnum,
        task_id: int,
        target_username: str
) -> None:
    if not is_owned_task(session, owner_id, task_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Задача не найдена или не принадлежит вам"
        )

    target_user = get_user_by_username(session, target_username)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Пользователь '{target_username}' не найден"
        )

    share = get_shared_access(
        session, task_id, owner_id, target_user.id)
    if not share:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Эта задача не расшарена с пользователем {target_username}"
        )
    share.permission_level = new_permission
    session.commit()

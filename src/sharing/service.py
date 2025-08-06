from typing import Annotated, List

from fastapi import APIRouter, HTTPException, Path, status

from src.auth.models import ToDoUser
from src.auth.service import CurrentUser, get_user_by_id, get_user_by_username
from src.core.database import DbSession, PrimaryKey, UsernameStr
from src.core.exceptions import handle_server_exception
from src.db.models import SharedAccessEnum, Task, TaskShare
from src.db.schemas import SortSharedTasksValidator, TaskShareSchema
from src.routers.helpers.crud_helpers import get_user_task
from src.routers.helpers.shared_tasks_helpers import (SortSharedTasksRule,
                                                      check_task_access_level,
                                                      check_view_permission,
                                                      get_task_collaborators,
                                                      todo_sort_mapping)


def get_task(session, task_id: int):
    return session.query(Task).filter(
        Task.id == task_id
    ).first()


def is_owned_task(session, owner_id: int, task_id: int) -> bool:
    return session.query(Task).filter(
        Task.id == task_id,
        Task.user_id == owner_id
    ).first() is not None


def is_already_shared(session, target_user_id: int, task_id: int) -> bool:
    return session.query(TaskShare).filter(
        TaskShare.task_id == task_id,
        TaskShare.target_user_id == target_user_id,
    ).first() is not None


def is_sharing_with_self(owner_id: int, target_user_id: int) -> bool:
    return owner_id == target_user_id


def get_share_record(
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


def get_permission_level(session: DbSession, current_user_id: int, task_id: int) -> SharedAccessEnum | None:
    permission_level = session.query(TaskShare.permission_level).filter(
        TaskShare.task_id == task_id,
        TaskShare.target_user_id == current_user_id
    ).one_or_none()
    if not permission_level:
        return None
    return permission_level


def get_shared_task_for_user(session, current_user_id: int, task_id: int) -> Task:
    return session.query(Task).join(
        TaskShare, TaskShare.task_id == Task.id).filter(
        Task.id == task_id,
        TaskShare.target_user_id == current_user_id,
    ).first()


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

    share_record = get_share_record(
        session, task_id, owner_id, target_user.id)
    if not share_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Эта задача не расшарена с пользователем {target_username}"
        )
    share_record.permission_level = new_permission
    session.commit()

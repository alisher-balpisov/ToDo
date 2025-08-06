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
from src.sharing.service import (get_share, is_already_shared, is_owned_task,
                                 is_sharing_with_self)


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

    share = get_share(
        session, task_id, owner_id, target_user.id)
    if not share:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Эта задача не расшарена с пользователем {target_username}"
        )
    session.delete(share)
    session.commit()

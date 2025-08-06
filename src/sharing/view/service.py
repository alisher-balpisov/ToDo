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
# from src.sharing.service import 


def get_shared_tasks_service(
    session,
    current_user_id: int,
    sort_shared_tasks: List[SortSharedTasksRule],
    skip: int,
    limit: int
):
    sort = SortSharedTasksValidator(
        sort_shared_tasks=sort_shared_tasks).sort_shared_tasks

    result = (
        session.query(
            Task,
            ToDoUser.username.label("owner_username"),
            TaskShare.permission_level
        )
        .join(TaskShare, TaskShare.task_id == Task.id)
        .join(ToDoUser, ToDoUser.id == Task.user_id)
        .filter(TaskShare.target_user_id == current_user_id)
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Список пуст"
        )

    order_by = [todo_sort_mapping[rule]
                for rule in sort
                if rule in todo_sort_mapping]

    if order_by:
        result = result.order_by(*order_by)

    return result.offset(skip).limit(limit).all()


def get_shared_task_service(
        session,
        current_user_id: int,
        task_id: int
):
    result = (
        session.query(
            Task,
            ToDoUser.username.label("owner_username"),
            TaskShare.permission_level
        )
        .join(TaskShare, TaskShare.task_id == Task.id)
        .join(ToDoUser, ToDoUser.id == Task.user_id)
        .filter(
            Task.id == task_id,
            TaskShare.target_user_id == current_user_id
        ).one_or_none()
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена"
        )
    return result


def check_task_access_level(session, current_user_id: int, task_id: int) -> tuple[Task, SharedAccessEnum]:
    owned_task = get_user_task(session, current_user_id, task_id)
    if owned_task:
        return owned_task, SharedAccessEnum.edit

    shared_task = (
        session.query(Task, TaskShare.permission_level)
        .join(TaskShare, TaskShare.task_id == Task.id)
        .filter(
            Task.id == task_id,
            TaskShare.target_user_id == current_user_id
        ).first()
    )

    if not shared_task:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Задача не найдена или не принадлежит вам"
        )

    task, permission_level = shared_task
    return task, permission_level


def get_task_collaborators_service(
        session: DbSession,
        current_user_id: int,
        task_id: int,
) -> list[dict]:

    task, access_level = check_task_access_level(
        session, task_id, current_user_id)
    owner = get_user_by_id(session, current_user_id)
    collaborators = []

    if owner:
        collaborators.append(
            {
                "user_id": owner.id,
                "username": owner.username,
                "email": owner.email,
                "role": "owner",
                "permission_level": "full_access",
                "can_revoke": False,
            }
        )

    shares = (
        session.query(TaskShare, ToDoUser)
        .join(ToDoUser, ToDoUser.id == TaskShare.target_user_id)
        .filter(TaskShare.task_id == task_id)
        .all()
    )

    for share, ToDoUser in shares:
        collaborators.append(
            {
                "user_id": ToDoUser.id,
                "username": ToDoUser.username,
                "email": ToDoUser.email,
                "role": "collaborator",
                "permission_level": share.permission_level.value,
                "shared_date": share.date_time.isoformat(),
                "can_revoke": task.user_id == current_user_id,
            }
        )
    return collaborators

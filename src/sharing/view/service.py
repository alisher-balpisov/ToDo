from typing import List

from fastapi import HTTPException, status

from src.auth.models import ToDoUser
from src.auth.service import get_user_by_id
from src.core.database import DbSession
from src.db.models import SharedAccessEnum, Task, TaskShare
from src.db.schemas import SortSharedTasksValidator
from src.routers.helpers.shared_tasks_helpers import (
    SortSharedTasksRule, shared_tasks_sort_mapping)
from src.sharing.service import (get_permission_level, get_task, get_task_user,
                                 get_user_shared_task, map_sort_rules)


def get_shared_tasks_service(
    session,
    current_user_id: int,
    sort_shared_tasks: List[SortSharedTasksRule],
    skip: int,
    limit: int
):
    sort = SortSharedTasksValidator(
        sort_shared_tasks=sort_shared_tasks).sort_shared_tasks

    tasks_info = (
        session.query(
            Task,
            ToDoUser.username.label("owner_username"),
            TaskShare.permission_level
        )
        .join(TaskShare, TaskShare.task_id == Task.id)
        .join(ToDoUser, ToDoUser.id == Task.user_id)
        .filter(TaskShare.target_user_id == current_user_id)
    )
    if not tasks_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Список пуст"
        )

    order_by = map_sort_rules(sort, shared_tasks_sort_mapping)
    if order_by:
        tasks_info = tasks_info.order_by(*order_by)

    return tasks_info.offset(skip).limit(limit).all()


def get_shared_task_service(
        session,
        current_user_id: int,
        task_id: int
):
    task = get_user_shared_task(session, current_user_id, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена"
        )
    owner = get_task_user(session, task_id)
    permission_level = get_permission_level(session, current_user_id, task_id)
    return task, owner, permission_level


def check_task_permission_level(session, current_user_id: int, task_id: int) -> tuple[Task, SharedAccessEnum]:
    owned_task = get_user_task(session, current_user_id, task_id)
    if owned_task:
        return owned_task, SharedAccessEnum.edit

    shared_task = get_user_shared_task(session, current_user_id, task_id)
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
    collaborators = []

    owned_task = get_user_task(session, current_user_id, task_id)
    if owned_task:
        return owned_task, SharedAccessEnum.edit

    owner = get_user_by_id(session, current_user_id)
    if owner:
        collaborators.append(
            {
                "user_id": owner.id,
                "username": owner.username,
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
                "role": "collaborator",
                "permission_level": share.permission_level.value,
                "shared_date": share.date_time.isoformat(),
                "can_revoke": share.owner_id == current_user_id,
            }
        )
    return collaborators


def get_task_permissions_service(
        session,
        current_user_id: int,
        task_id: int
):
    task = get_task(session, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена"
        )

    permission_level = get_permission_level(session, current_user_id, task_id)

    permissions = {
        "can_view": True,
        "can_edit": permission_level == SharedAccessEnum.edit,
        "can_delete": task.user_id == current_user_id,
        "can_share": task.user_id == current_user_id,
        "can_upload_files": permission_level == SharedAccessEnum.edit,
        "can_change_status": permission_level == SharedAccessEnum.edit,
        "is_owner": task.user_id == current_user_id,
    }
    return task, permission_level, permissions

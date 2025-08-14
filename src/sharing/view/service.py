from fastapi import HTTPException, Query, status

from src.auth.models import ToDoUser
from src.auth.service import get_user_by_id
from src.common.utils import (get_task, get_task_user, get_user_task,
                              is_task_owner, map_sort_rules)
from src.core.database import DbSession
from src.exceptions import LIST_EMPTY, TASK_NOT_FOUND, TASK_NOT_OWNED
from src.sharing.helpers import SortSharedTasksRule, shared_tasks_sort_mapping
from src.sharing.models import Share, SharedAccessEnum, Task
from src.sharing.schemas import Sort, SortSharedTasksValidator
from src.sharing.service import (get_permission_level, get_user_shared_task,
                                 is_collaborator)


def get_shared_tasks_service(
    session,
    current_user_id: int,
    sort_raw: list[SortSharedTasksRule] = Query(default=[]),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    # /endpoint?sort=date_asc
    params = Sort(sort_raw.query_params())

    sort_raw = SortSharedTasksValidator(sort=sort_raw).sort

    tasks_info = (
        session.query(
            Task,
            ToDoUser.username.label("owner_username"),
            Share.permission_level
        )
        .join(Share, Share.task_id == Task.id)
        .join(ToDoUser, ToDoUser.id == Task.user_id)
        .filter(Share.target_user_id == current_user_id)
    )
    if not tasks_info:
        raise LIST_EMPTY

    # order_by = map_sort_rules(sort_raw, shared_tasks_sort_mapping)
    # if order_by:
    tasks_info = tasks_info.order_by(**params)

    return tasks_info.offset(skip).limit(limit).all()


def get_shared_task_service(
        session,
        current_user_id: int,
        task_id: int
):
    task = get_user_shared_task(session, current_user_id, task_id)
    if not task:
        raise TASK_NOT_FOUND
    owner = get_task_user(session, task_id)
    permission_level = get_permission_level(session, current_user_id, task_id)
    return task, owner, permission_level


def check_task_permission_level(session, current_user_id: int, task_id: int) -> tuple[Task, SharedAccessEnum]:
    owned_task = get_user_task(session, current_user_id, task_id)
    if owned_task:
        return owned_task, SharedAccessEnum.edit

    shared_task = get_user_shared_task(session, current_user_id, task_id)
    if not shared_task:
        raise TASK_NOT_OWNED

    task, permission_level = shared_task
    return task, permission_level


def get_task_collaborators_service(
        session: DbSession,
        current_user_id: int,
        task_id: int,
) -> list[dict]:
    task = get_task(session, task_id)
    if not task:
        raise TASK_NOT_FOUND

    if not is_task_owner(session, current_user_id, task_id):
        if not is_collaborator(session, current_user_id, task_id):
            raise TASK_NOT_OWNED

    collaborators = []
    owner = get_user_by_id(session, task.user_id)
    if owner:
        collaborators.append({
            "user_id": owner.id,
            "username": owner.username,
            "role": "owner",
            "permission_level": "full_access",
            "can_revoke": False,
        })

    shared_users_query = (
        session.query(Share, ToDoUser)
        .join(ToDoUser, Share.target_user_id == ToDoUser.id)
        .filter(Share.task_id == task_id)
    )

    for share, user in shared_users_query.all():
        collaborators.append({
            "user_id": user.id,
            "username": user.username,
            "role": "collaborator",
            "permission_level": share.permission_level.value,
            "shared_date": share.date_time.isoformat(),
            "can_revoke": is_task_owner(session, current_user_id, task_id),
        })

    return collaborators


def get_task_permissions_service(
        session,
        current_user_id: int,
        task_id: int
):
    task = get_task(session, task_id)
    if not task:
        raise TASK_NOT_FOUND

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

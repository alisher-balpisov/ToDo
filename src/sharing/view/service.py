from src.auth.models import User
from src.auth.service import get_user_by_id
from src.common.models import Task
from src.common.utils import (get_task, get_task_user, is_task_owner,
                              map_sort_rules)
from src.core.decorators import handler
from src.core.exception import (InsufficientPermissionsException,
                                ResourceNotFoundException)
from src.sharing.helpers import SortSharedTasksRule, shared_tasks_sort_mapping
from src.sharing.models import Share, SharedAccessEnum
from src.sharing.schemas import SortSharedTasksValidator
from src.sharing.service import (get_permission_level, get_user_shared_task,
                                 is_task_collaborator)


@handler
def get_shared_tasks_service(
    session,
    current_user_id: int,
    sort: list[SortSharedTasksRule],
    skip: int,
    limit: int,
) -> list[tuple]:
    SortSharedTasksValidator(sort=sort)

    tasks_info = (
        session.query(
            Task,
            User.username.label("owner_username"),
            Share.permission_level
        )
        .join(Share, Share.task_id == Task.id)
        .join(User, User.id == Task.user_id)
        .filter(Share.target_user_id == current_user_id)
    )
    order_by = map_sort_rules(sort, shared_tasks_sort_mapping)
    if order_by:
        tasks_info = tasks_info.order_by(*order_by)

    tasks_info = tasks_info.offset(skip).limit(limit).all()
    if not tasks_info:
        raise ResourceNotFoundException("Список", "данные")

    return tasks_info


@handler
def get_shared_task_service(
        session,
        current_user_id: int,
        task_id: int
) -> tuple:
    task = get_user_shared_task(session, current_user_id, task_id)
    if task is None:
        raise ResourceNotFoundException("Задача", task_id)
    owner = get_task_user(session, task_id)
    permission_level = get_permission_level(session, current_user_id, task_id)
    return task, owner, permission_level


@handler
def get_task_collaborators_service(
        session,
        current_user_id: int,
        task_id: int,
) -> list[dict]:
    task = get_task(session, task_id)
    if task is None:
        raise ResourceNotFoundException("Задача", task_id)

    is_owner = is_task_owner(session, current_user_id, task_id)
    is_collaborator = is_task_collaborator(session, current_user_id, task_id)
    if not is_owner and not is_collaborator:
        raise InsufficientPermissionsException(
            "доступ к задаче", "пользователь")

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
        session.query(Share, User)
        .join(User, Share.target_user_id == User.id)
        .filter(Share.task_id == task_id)
        .all()
    )

    for share, user in shared_users_query:
        collaborators.append({
            "user_id": user.id,
            "username": user.username,
            "role": "collaborator",
            "permission_level": share.permission_level.value,
            "shared_date": share.date_time.isoformat(),
            "can_revoke": is_owner
        })

    return collaborators


@handler
def get_task_permissions_service(
        session,
        current_user_id: int,
        task_id: int
) -> tuple[Task, SharedAccessEnum, dict]:
    task = get_task(session, task_id)
    if task is None:
        raise ResourceNotFoundException("Задача", task_id)
    is_owner = is_task_owner(session, current_user_id, task_id)
    permission_level = get_permission_level(session, current_user_id, task_id)
    can_edit_level = is_owner or permission_level == SharedAccessEnum.edit

    permissions = {
        "can_view": True,
        "can_edit": can_edit_level,
        "can_delete": is_owner,
        "can_share": is_owner,
        "can_upload_files": can_edit_level,
        "can_change_status": can_edit_level,
        "is_owner": is_owner,
    }

    return task, permission_level, permissions

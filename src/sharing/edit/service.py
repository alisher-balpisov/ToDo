from fastapi import HTTPException, status

from src.auth.service import get_user_by_username
from src.common.schemas import TaskSchema
from src.common.utils import is_task_owner
from src.core.database import PrimaryKey
from src.exceptions import (NO_EDIT_ACCESS, TASK_NOT_FOUND, TASK_NOT_OWNED,
                            TASK_NOT_SHARED_WITH_USER, USER_NOT_FOUND)
from src.sharing.models import SharedAccessEnum
from src.sharing.service import (get_permission_level, get_share_record,
                                 get_user_shared_task)


def update_share_permission_service(
        session,
        owner_id: int,
        new_permission: SharedAccessEnum,
        task_id: int,
        target_username: str
) -> None:
    if not is_task_owner(session, owner_id, task_id):
        raise TASK_NOT_OWNED

    target_user = get_user_by_username(session, target_username)
    if not target_user:
        raise USER_NOT_FOUND(target_username)
    share_record = get_share_record(
        session, owner_id, target_user.id, task_id)
    if not share_record:
        raise TASK_NOT_SHARED_WITH_USER(target_username)

    if new_permission.value is share_record.permission_level:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[{"msg": f"permission_level уже {new_permission.value}"}]
        )

    share_record.permission_level = new_permission
    session.commit()


def update_shared_task_service(
        session,
        current_user_id: int,
        task_id: PrimaryKey,
        task_update: TaskSchema,
):
    task = get_user_shared_task(session, current_user_id, task_id)
    if not task:
        raise TASK_NOT_FOUND

    if get_permission_level(session, current_user_id, task_id) is not SharedAccessEnum.edit:
        raise NO_EDIT_ACCESS

    if task_update.name is not None:
        task.name = task_update.name
    if task_update.text is not None:
        task.text = task_update.text

    session.commit()
    session.refresh(task)
    return task


def toggle_shared_task_completion_status_service(
        session,
        current_user_id: int,
        task_id: int,
):
    task = get_user_shared_task(session, current_user_id, task_id)
    if not task:
        raise TASK_NOT_FOUND

    if get_permission_level(session, current_user_id, task_id) is not SharedAccessEnum.edit:
        raise NO_EDIT_ACCESS

    task.completion_status = not task.completion_status
    session.commit()
    session.refresh(task)
    return task

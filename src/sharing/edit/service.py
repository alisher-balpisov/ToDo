from fastapi import HTTPException, status

from src.auth.service import get_user_by_username
from src.common.schemas import TaskSchema
from src.common.utils import handler, is_task_owner, transactional
from src.core.database import PrimaryKey
from src.exceptions import (NO_EDIT_ACCESS, TASK_ACCESS_FORBIDDEN,
                            TASK_NOT_FOUND, USER_NOT_FOUND,
                            task_not_shared_with_user)
from src.sharing.models import SharedAccessEnum
from src.sharing.service import (get_permission_level, get_share_record,
                                 get_user_shared_task, is_sharing_with_self)


@handler
@transactional
def update_share_permission_service(
        session,
        owner_id: int,
        new_permission: SharedAccessEnum,
        task_id: int,
        target_username: str
) -> None:
    target_user = get_user_by_username(session, target_username)
    if not target_user:
        raise USER_NOT_FOUND(target_username)

    if not is_task_owner(session, owner_id, task_id):
        raise TASK_ACCESS_FORBIDDEN

    if is_sharing_with_self(owner_id, target_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"msg": "Нельзя изменять доступ к своей собственной задаче"}
        )

    share_record = get_share_record(
        session, owner_id, target_user.id, task_id)
    if not share_record:
        raise task_not_shared_with_user(target_user.username)

    if new_permission == share_record.permission_level:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"msg": f"permission_level уже {new_permission.value}"}
        )

    share_record.permission_level = new_permission


@handler
@transactional
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
    return task


@handler
@transactional
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
    return task

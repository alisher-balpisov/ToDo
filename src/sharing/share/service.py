from fastapi import HTTPException, status

from src.auth.service import get_user_by_username
from src.common.utils import handler, is_task_owner, transactional
from src.core.database import DbSession
from src.exceptions import (TASK_ACCESS_FORBIDDEN, USER_NOT_FOUND,
                            task_already_shared, task_not_shared_with_user)
from src.sharing.models import Share, SharedAccessEnum
from src.sharing.service import (get_share_record, is_already_shared,
                                 is_sharing_with_self)


@handler
@transactional
def share_task_service(
        session,
        owner_id: int,
        task_id: int,
        target_username: str,
        permission_level: SharedAccessEnum
) -> None:
    if not is_task_owner(session, owner_id, task_id):
        raise TASK_ACCESS_FORBIDDEN

    target_user = get_user_by_username(session, target_username)
    if not target_user:
        raise USER_NOT_FOUND

    if is_sharing_with_self(owner_id, target_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"msg": "Нельзя делиться задачей с самим собой"}
        )

    if is_already_shared(session, target_user.id, task_id):
        raise task_already_shared(target_username)

    new_share = Share(
        task_id=task_id,
        owner_id=owner_id,
        target_user_id=target_user.id,
        permission_level=permission_level,
    )
    session.add(new_share)


@handler
@transactional
def unshare_task_service(
    session: DbSession,
    owner_id: int,
    task_id: int,
    target_username: str
) -> None:
    if not is_task_owner(session, owner_id, task_id):
        raise TASK_ACCESS_FORBIDDEN

    target_user = get_user_by_username(session, target_username)
    if not target_user:
        raise USER_NOT_FOUND

    share = get_share_record(
        session, owner_id, target_user.id, task_id)
    if not share:
        raise task_not_shared_with_user(target_username)
    session.delete(share)

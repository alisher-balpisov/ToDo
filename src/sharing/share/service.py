from fastapi import HTTPException, status

from src.auth.service import get_user_by_username
from src.common.utils import is_task_owner
from src.core.database import DbSession
from src.exceptions import (TASK_ALREADY_SHARED, TASK_NOT_OWNED,
                            TASK_NOT_SHARED_WITH_USER, USER_NOT_FOUND)
from src.sharing.models import Share, SharedAccessEnum
from src.sharing.service import (get_share_record, is_already_shared,
                                 is_sharing_with_self)


def share_task_service(
        session,
        owner_id: int,
        task_id: int,
        target_username: str,
        permission_level: SharedAccessEnum
) -> None:
    if not is_task_owner(session, owner_id, task_id):
        raise TASK_NOT_OWNED

    target_user = get_user_by_username(session, target_username)
    if not target_user:
        raise USER_NOT_FOUND(target_username)

    if is_sharing_with_self(owner_id, target_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[{"msg": "Нельзя делиться задачей с самим собой"}]
        )

    if is_already_shared(session, target_user.id, task_id):
        raise TASK_ALREADY_SHARED(target_username)

    new_share = Share(
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
    if not is_task_owner(session, owner_id, task_id):
        raise TASK_NOT_OWNED

    target_user = get_user_by_username(session, target_username)
    if not target_user:
        raise USER_NOT_FOUND(target_username)

    share = get_share_record(
        session, owner_id, target_user.id, task_id)
    if not share:
        raise TASK_NOT_SHARED_WITH_USER(target_username)
    session.delete(share)
    session.commit()

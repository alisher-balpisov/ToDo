from fastapi import HTTPException, status

from src.auth.service import get_user_by_username
from src.common.utils import is_user_task
from src.core.database import DbSession
from src.db.models import SharedAccessEnum, TaskShare
from src.sharing.service import is_already_shared, is_sharing_with_self


def share_task_service(
        session,
        owner_id: int,
        task_id: int,
        target_username: str,
        permission_level: SharedAccessEnum
) -> None:

    if not is_user_task(session, owner_id, task_id):
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
    if not is_user_task(session, owner_id, task_id):
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

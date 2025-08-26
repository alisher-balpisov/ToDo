from src.auth.service import get_user_by_username
from src.common.utils import is_task_owner
from src.core.decorators import handler, transactional
from src.core.exception import (InsufficientPermissionsException,
                                InvalidOperationException,
                                ResourceAlreadyExistsException,
                                ResourceNotFoundException)
from src.core.types import DbSession
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
        raise InsufficientPermissionsException(
            "доступ к задаче", "пользователь")

    target_user = get_user_by_username(session, target_username)
    if target_user is None:
        raise ResourceNotFoundException("Пользователь", target_username)

    if is_sharing_with_self(owner_id, target_user.id):
        raise InvalidOperationException(
            "расшаривание задачи", "самому себе", "Нельзя делиться задачей с самим собой")

    if is_already_shared(session, target_user.id, task_id):
        raise ResourceAlreadyExistsException(
            "Доступ к задаче", target_username)

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
        raise InsufficientPermissionsException(
            "доступ к задаче", "пользователь")

    target_user = get_user_by_username(session, target_username)
    if target_user is None:
        raise ResourceNotFoundException("Пользователь", target_username)

    share = get_share_record(
        session, owner_id, target_user.id, task_id)
    if share is None:
        raise ResourceNotFoundException("Доступ к задаче", target_username)
    session.delete(share)

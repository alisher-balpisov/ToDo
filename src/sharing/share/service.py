from src.auth.service import get_user_by_username
from src.common.utils import is_task_owner
from src.core.decorators import service_method
from src.core.exception import (InsufficientPermissionsException,
                                InvalidOperationException,
                                ResourceAlreadyExistsException,
                                ResourceNotFoundException)
from src.core.types import DbSession
from src.sharing.models import Share, SharedAccessEnum
from src.sharing.service import (get_share_record, is_already_shared,
                                 is_sharing_with_self)


@service_method()
async def share_task_service(
        session,
        owner_id: int,
        task_id: int,
        target_username: str,
        permission_level: SharedAccessEnum
) -> None:
    if not await is_task_owner(session, owner_id, task_id):
        raise InsufficientPermissionsException(
            "доступ к задаче", "пользователь")

    target_user = await get_user_by_username(session, target_username)
    if target_user is None:
        raise ResourceNotFoundException("Пользователь", target_username)

    if await is_sharing_with_self(owner_id, target_user.id):
        raise InvalidOperationException(
            "расшаривание задачи", "самому себе", "Нельзя делиться задачей с самим собой")

    if await is_already_shared(session, target_user.id, task_id):
        raise ResourceAlreadyExistsException(
            "Доступ к задаче", target_username)

    new_share = Share(
        task_id=task_id,
        owner_id=owner_id,
        target_user_id=target_user.id,
        permission_level=permission_level,
    )
    session.add(new_share)


@service_method()
async def unshare_task_service(
    session: DbSession,
    owner_id: int,
    task_id: int,
    target_username: str
) -> None:
    if not await is_task_owner(session, owner_id, task_id):
        raise InsufficientPermissionsException(
            "доступ к задаче", "пользователь")

    target_user = await get_user_by_username(session, target_username)
    if target_user is None:
        raise ResourceNotFoundException("Пользователь", target_username)

    share = await get_share_record(
        session, owner_id, target_user.id, task_id)
    if not share:
        raise ResourceNotFoundException(
            "Доступ к задаче", f"для {target_username}")
    await session.delete(share)

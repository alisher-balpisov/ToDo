from src.auth.service import get_user_by_username
from src.common.schemas import TaskSchema
from src.common.utils import is_task_owner
from src.core.decorators import handler, transactional
from src.core.exception import (InsufficientPermissionsException,
                          InvalidOperationException, ResourceNotFoundException)

from src.core.types import PrimaryKey
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
    if target_user is None:
        raise ResourceNotFoundException(
            "Пользователь", target_username)

    if not is_task_owner(session, owner_id, task_id):
        raise InsufficientPermissionsException(
            "доступ к задаче", "пользователь")

    if is_sharing_with_self(owner_id, target_user.id):
        raise InvalidOperationException(
            "изменение доступа", "собственная задача", "Нельзя изменять доступ к своей собственной задаче")

    share_record = get_share_record(
        session, owner_id, target_user.id, task_id)
    if share_record is None:
        raise ResourceNotFoundException("Доступ к задаче", target_username)

    if new_permission == share_record.permission_level:
        raise InvalidOperationException(
            "установка разрешения", new_permission.value, f"permission_level уже {new_permission.value}")

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
    if task is None:
        raise ResourceNotFoundException("Задача", task_id)

    if get_permission_level(session, current_user_id, task_id) is not SharedAccessEnum.edit:
        raise InsufficientPermissionsException("редактирование задачи")

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
    if task is None:
        raise ResourceNotFoundException("Задача", task_id)

    if get_permission_level(session, current_user_id, task_id) is not SharedAccessEnum.edit:
        raise InsufficientPermissionsException("редактирование задачи")

    task.completion_status = not task.completion_status
    return task

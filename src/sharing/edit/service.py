from fastapi import HTTPException, status

from src.auth.service import get_user_by_username
from src.core.database import PrimaryKey
from src.db.models import SharedAccessEnum
from src.db.schemas import TaskSchema
from src.sharing.service import (get_permission_level, get_share_record,
                                 get_user_shared_task, is_user_task)


def update_share_permission_service(
        session,
        owner_id: int,
        new_permission: SharedAccessEnum,
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

    share_record = get_share_record(
        session, task_id, owner_id, target_user.id)
    if not share_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Эта задача не расшарена с пользователем {target_username}"
        )

    if new_permission.value is share_record.permission_level:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"permission_level уже {new_permission.value}"
        )

    share_record.permission_level = new_permission
    session.commit()


def edit_shared_task_service(
        session,
        current_user_id: int,
        task_id: PrimaryKey,
        task_update: TaskSchema,
):
    task = get_user_shared_task(session, current_user_id, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    if get_permission_level(session, current_user_id, task_id) is not SharedAccessEnum.edit:
        raise HTTPException(
            status_code=403, detail="Нет доступа для редактирования задачи"
        )

    if task_update.name is not None:
        task.name = task_update.name
    if task_update.text is not None:
        task.text = task_update.text
    if task_update.completion_status is not None:
        task.completion_status = task_update.completion_status

    session.commit()
    session.refresh(task)
    return task


def toggle_shared_task_status_service(
        session,
        current_user_id: int,
        task_id: int,
):
    task = get_user_shared_task(session, current_user_id, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    if get_permission_level(session, current_user_id, task_id) is not SharedAccessEnum.edit:
        raise HTTPException(
            status_code=403, detail="Нет доступа для редактирования задачи"
        )

    task.completion_status = not task.completion_status
    session.commit()
    session.refresh()
    return task 

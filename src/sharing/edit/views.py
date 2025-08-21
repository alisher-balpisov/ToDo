from typing import Any

from fastapi import APIRouter

from src.auth.service import CurrentUser
from src.common.schemas import TaskSchema
from src.core.database import DbSession, PrimaryKey, UsernameStr
from src.core.exceptions import handle_server_exception
from src.sharing.models import SharedAccessEnum

from .service import (toggle_shared_task_completion_status_service,
                      update_share_permission_service,
                      update_shared_task_service)

router = APIRouter()


@router.put("/tasks/{task_id}/shares/{target_username}")
def update_share_permission(
        session: DbSession,
        current_user: CurrentUser,
        new_permission: SharedAccessEnum,
        task_id: PrimaryKey,
        target_username: UsernameStr,

) -> dict[str, str]:
    try:
        update_share_permission_service(session=session,
                                        owner_id=current_user.id,
                                        new_permission=new_permission,
                                        task_id=task_id,
                                        target_username=target_username)
        return {"msg": "Уровень доступа успешно обновлен"}
    except Exception as e:
        session.rollback()
        handle_server_exception(
            e, "Ошибка сервера при обновлении уровня доступа")


@router.put("/shared-tasks/{task_id}")
def update_shared_task(
        session: DbSession,
        current_user: CurrentUser,
        task_id: PrimaryKey,
        task_update: TaskSchema,
) -> dict[str, Any]:
    try:
        task = update_shared_task_service(session=session,
                                          current_user_id=current_user.id,
                                          task_id=task_id,
                                          task_update=task_update)
        return {
            "msg": "Расшаренная задача успешно обновлена",
            "id": task.id,
            "task_name": task.name,
            "completion_status": task.completion_status,
            "date_time": task.date_time.strftime("%Y-%m-%d | %H:%M:%S"),
            "text": task.text
        }

    except Exception as e:
        session.rollback()
        handle_server_exception(
            e, "Ошибка сервера при редактировании расшаренной задачи"
        )


@router.patch("/shared-tasks/{task_id}")
def toggle_shared_task_completion_status(
        session: DbSession,
        current_user: CurrentUser,
        task_id: PrimaryKey,
) -> dict[str, Any]:
    try:
        task = toggle_shared_task_completion_status_service(session=session,
                                                            current_user_id=current_user.id,
                                                            task_id=task_id)
        return {
            "msg": f"Статус задачи изменен на {'выполнено' if task.completion_status else 'не выполнено'}",
            "task_id": task.id,
            "new_status": task.completion_status,
        }

    except Exception as e:
        session.rollback()
        handle_server_exception(
            e, "Ошибка сервера при изменении статуса задачи")

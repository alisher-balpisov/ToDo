from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Path
from sqlalchemy.orm import Session

from src.auth.models import ToDoUser
from src.auth.service import CurrentUser
from src.db.database import DbSession, PrimaryKey
from src.db.schemas import ToDoSchema
from src.handle_exception import handle_server_exception
from src.routers.helpers.sharing_helpers import check_edit_permission

router = APIRouter()


@router.put("/shared-tasks/{task_id}")
def edit_shared_task(
        session: DbSession,
        current_user: CurrentUser,
        task_id: Annotated[int, PrimaryKey],
        task_update: ToDoSchema,

) -> dict[str, Any]:
    try:
        task = check_edit_permission(task_id, current_user)

        if task_update.name is not None:
            task.name = task_update.name
        if task_update.text is not None:
            task.text = task_update.text
        if task_update.completion_status is not None:
            task.completion_status = task_update.completion_status

        session.commit()
        session.refresh(task)

        owner = session.query(ToDoUser).filter(
            ToDoUser.id == task.user_id).first()

        return {
            "message": "Расшаренная задача успешно обновлена",
            "id": task.id,
            "task_name": task.name,
            "completion_status": task.completion_status,
            "date_time": task.date_time.strftime("%Y-%m-%d | %H:%M:%S"),
            "text": task.text,
            "owner_username": owner.username if owner else "Неизвестен",
        }

    except Exception as e:
        session.rollback()
        handle_server_exception(
            e, "Ошибка сервера при редактировании расшаренной задачи"
        )


@router.patch("/shared-tasks/{task_id}")
def toggle_shared_task_status(
        session: DbSession,
        current_user: CurrentUser,
        task_id: Annotated[int, PrimaryKey],

) -> dict[str, Any]:
    try:
        task = check_edit_permission(task_id, current_user)

        task.completion_status = not task.completion_status
        session.commit()
        return {
            "message": f"Статус задачи изменен на {'выполнено' if task.completion_status else 'не выполнено'}",
            "task_id": task.id,
            "new_status": task.completion_status,
        }

    except Exception as e:
        session.rollback()
        handle_server_exception(
            e, "Ошибка сервера при изменении статуса задачи")

from typing import Any

from fastapi import APIRouter, Body, Depends, Path
from sqlalchemy.orm import Session

from app.auth.jwt_handler import get_current_active_user
from app.db.database import get_db
from app.db.models import User
from app.db.schemas import ToDoSchema
from app.handle_exception import handle_server_exception
from app.routers.helpers.sharing_helpers import check_edit_permission

router = APIRouter()


@router.put("/shared-tasks/{task_id}")
def edit_shared_task(
    task_id: int = Path(ge=1),
    task_update: ToDoSchema = Body(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    try:
        task = check_edit_permission(task_id, current_user)

        if task_update.name is not None:
            task.name = task_update.name
        if task_update.text is not None:
            task.text = task_update.text
        if task_update.completion_status is not None:
            task.completion_status = task_update.completion_status

        db.commit()
        db.refresh(task)

        owner = db.query(User).filter(User.id == task.user_id).first()

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
        db.rollback()
        handle_server_exception(
            e, "Ошибка сервера при редактировании расшаренной задачи"
        )


@router.patch("/shared-tasks/{task_id}")
def toggle_shared_task_status(
    task_id: int = Path(ge=1),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    try:
        task = check_edit_permission(task_id, current_user)

        task.completion_status = not task.completion_status
        db.commit()
        return {
            "message": f"Статус задачи изменен на {'выполнено' if task.completion_status else 'не выполнено'}",
            "task_id": task.id,
            "new_status": task.completion_status,
        }

    except Exception as e:
        db.rollback()
        handle_server_exception(
            e, "Ошибка сервера при изменении статуса задачи")

from typing import Annotated, Any

from fastapi import APIRouter
from sqlalchemy import or_

from src.auth.service import CurrentUser
from src.core.database import DbSession, PrimaryKey
from src.core.exceptions import handle_server_exception
from src.db.models import Task

from .helpers.crud_helpers import get_user_task

router = APIRouter()


@router.get("/search")
def search_tasks(
        session: DbSession,
        current_user: CurrentUser,
        search_query: str,

) -> list[dict[str, Any]]:
    try:
        search_pattern = f"%{search_query}%"
        tasks = (
            session.query(Task).filter(
                or_(
                    Task.name.ilike(search_pattern),
                    Task.text.ilike(search_pattern)
                ),
                Task.user_id == current_user.id,
            ).all()
        )
        return [
            {
                "id": task.id,
                "task_name": task.name,
                "completion_status": task.completion_status,
                "date_time": task.date_time.isoformat(),
                "text": task.text,
            }
            for task in tasks
        ]

    except Exception as e:
        handle_server_exception(e, "Ошибка сервера при поиске задачи")


@router.get("/stats")
def get_tasks_stats(
        session: DbSession,
        current_user: CurrentUser,

) -> dict[str, Any]:
    try:
        query = session.query(Task).filter(Task.user_id == current_user.id)

        total = query.count()
        completed = query.filter(Task.completion_status).count()
        uncompleted = query.filter(Task.completion_status is None).count()
        completion_percentage = round(
            (completed / total) * 100 if total > 0 else 0, 2)
        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "uncompleted_tasks": uncompleted,
            "completion_percentage": completion_percentage,
        }
    except Exception as e:
        handle_server_exception(e, "Ошибка сервера при выводе статистики")


@router.patch("/tasks/{task_id}")
def toggle_task_completion_status(
        session: DbSession,
        current_user: CurrentUser,
        task_id: PrimaryKey,

) -> dict[str, Any]:
    try:
        task = get_user_task(
            session=session,
            owner_id=current_user.id,
            task_id=task_id)

        task.completion_status = not task.completion_status
        session.commit()
        return {
            "msg": f"Статус задачи изменен на {'выполнено' if task.completion_status else 'не выполнено'}",
            "task_id": task.id,
            "new_status": task.completion_status,
        }

    except Exception as e:
        session.rollback()
        handle_server_exception(
            e, "Ошибка сервера при изменении статуса задачи")

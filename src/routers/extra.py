from typing import Any

from fastapi import APIRouter
from sqlalchemy import or_

from src.auth.service import CurrentUser
from src.core.database import DbSession
from src.core.exceptions import handle_server_exception
from src.db.models import Task

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

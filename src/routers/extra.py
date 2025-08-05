from typing import Any

from fastapi import APIRouter
from sqlalchemy import or_

from src.auth.service import CurrentUser
from src.db.database import DbSession
from src.db.models import ToDo
from src.handle_exception import handle_server_exception

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
            session.query(ToDo).filter(
                or_(
                    ToDo.name.ilike(search_pattern),
                    ToDo.text.ilike(search_pattern)
                ),
                ToDo.user_id == current_user.id,
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
        query = session.query(ToDo).filter(ToDo.user_id == current_user.id)

        total = query.count()
        completed = query.filter(ToDo.completion_status).count()
        uncompleted = query.filter(ToDo.completion_status is None).count()
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

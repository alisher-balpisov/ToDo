from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import Any

from app.auth.jwt_handler import get_current_active_user
from app.db.database import get_db
from app.db.models import ToDo, User
from app.routers.handle_exception import check_handle_exception

router = APIRouter(prefix="/tasks")


@router.get("/search")
def search_tasks(
    search_query: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> list[dict[str, Any]]:
    try:
        search_pattern = f"%{search_query}%"
        tasks = (
            db.query(ToDo).filter(
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
        check_handle_exception(e, "Ошибка сервера при поиске задачи")


@router.get("/stats")
def get_tasks_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    try:
        query = db.query(ToDo).filter(ToDo.user_id == current_user.id)

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
        check_handle_exception(e, "Ошибка сервера при выводе статистики")

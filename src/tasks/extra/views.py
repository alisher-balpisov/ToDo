from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.auth.models import User
from src.auth.service import CurrentUser, get_current_user
from src.core.database import DbSession, PrimaryKey, get_db

from .service import (get_tasks_stats_service, search_tasks_service,
                      toggle_task_completion_status_service)

router = APIRouter()


@router.get("/search")
def search_tasks(
        session: DbSession,
        current_user: CurrentUser,
        search_query: str
) -> list[dict]:
    try:
        tasks = search_tasks_service(session=session,
                                     current_user_id=current_user.id,
                                     search_query=search_query)
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
        current_user: CurrentUser
) -> dict:
    try:
        result = get_tasks_stats_service(session=session,
                                         current_user_id=current_user.id)
        total, completed, uncompleted, completion_percentage = result
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
) -> dict:
    task = toggle_task_completion_status_service(session=session,
                                                 current_user_id=current_user.id,
                                                 task_id=task_id)
    return {
        "msg": "Статус задачи успешно изменён",
        "task_id": task.id,
        "new_status": task.completion_status,
    }

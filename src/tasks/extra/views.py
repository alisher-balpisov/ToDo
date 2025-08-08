from typing import Any

from fastapi import APIRouter

from src.auth.service import CurrentUser
from src.core.database import DbSession, PrimaryKey
from src.core.exceptions import handle_server_exception

from .service import (get_tasks_stats_service, search_tasks_service,
                      toggle_task_completion_status_service)

router = APIRouter()


@router.get("/search")
def search_tasks(
        session: DbSession,
        current_user: CurrentUser,
        search_query: str,

) -> list[dict[str, Any]]:
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
) -> dict[str, Any]:
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
) -> dict[str, Any]:
    try:
        task = toggle_task_completion_status_service(session=session,
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

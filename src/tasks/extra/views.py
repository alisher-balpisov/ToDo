from fastapi import APIRouter

from src.core.types import CurrentUser, DbSession, PrimaryKey

from .service import (get_tasks_stats_service, search_tasks_service,
                      toggle_task_completion_status_service)

router = APIRouter()


@router.get("/search")
async def search_tasks(
        session: DbSession,
        current_user: CurrentUser,
        search_query: str
) -> list[dict]:
    tasks = await search_tasks_service(session=session,
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


@router.get("/stats")
async def get_tasks_stats(
        session: DbSession,
        current_user: CurrentUser
) -> dict:
    result = await get_tasks_stats_service(session=session,
                                           current_user_id=current_user.id)
    total, completed, uncompleted, completion_percentage = result
    return {
        "total_tasks": total,
        "completed_tasks": completed,
        "uncompleted_tasks": uncompleted,
        "completion_percentage": completion_percentage,
    }


@router.patch("/tasks/{task_id}")
async def toggle_task_completion_status(
        session: DbSession,
        current_user: CurrentUser,
        task_id: PrimaryKey,
) -> dict:
    task = await toggle_task_completion_status_service(session=session,
                                                       current_user_id=current_user.id,
                                                       task_id=task_id)
    return {
        "msg": "Статус задачи успешно изменён",
        "task_id": task.id,
        "new_status": task.completion_status,
    }

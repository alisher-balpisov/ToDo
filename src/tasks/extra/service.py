from sqlalchemy import func, or_, select

from src.common.constants import MAX_SEARCH_QUERY, STATS_PERCENTAGE_PRECISION
from src.common.models import Task
from src.common.utils import get_user_task
from src.core.decorators import service_method
from src.core.exception import InvalidInputException, ResourceNotFoundException


@service_method()
async def search_tasks_service(
        session,
        current_user_id: int,
        search_query: str,
) -> list[Task]:
    if not search_query.strip():
        return []
    if len(search_query) > MAX_SEARCH_QUERY:
        raise InvalidInputException(
            "поисковый запрос", search_query[0:20] + "...",
            f"запрос не длиннее {MAX_SEARCH_QUERY}"
        )

    search_pattern = f"%{search_query.strip()}%"

    stmt = (
        select(Task)
        .where(Task.user_id == current_user_id)
        .where(
            or_(
                Task.name.ilike(search_pattern),
                Task.text.ilike(search_pattern),
            )
        )
    )

    result = await session.execute(stmt)
    return result.scalars().all()


@service_method()
async def get_tasks_stats_service(
        session,
        current_user_id: int
) -> tuple[int, int, int, float]:
    stmt = select(
        func.count().label("total"),
        func.sum(
            func.case((Task.completion_status == True, 1), else_=0)
        ).label("completed"),
    ).where(Task.user_id == current_user_id)

    result = await session.execute(stmt)
    total, completed = result.one()

    completed = completed or 0
    uncompleted = total - completed
    completion_percentage = round(
        (completed / total) * 100 if total > 0 else 0,
        STATS_PERCENTAGE_PRECISION
    )
    return total, completed, uncompleted, completion_percentage


@service_method()
async def toggle_task_completion_status_service(
        session,
        current_user_id: int,
        task_id: int,
) -> Task:
    task = await get_user_task(session, current_user_id, task_id)
    if task is None:
        raise ResourceNotFoundException("Задача", task_id)

    task.completion_status = not task.completion_status
    return task

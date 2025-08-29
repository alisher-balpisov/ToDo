from sqlalchemy import case, func, or_, select

from src.common.constants import MAX_SEARCH_QUERY, STATS_PERCENTAGE_PRECISION
from src.common.models import Task
from src.common.utils import get_user_task
from src.core.decorators import service_method
from src.core.exception import InvalidInputException, ResourceNotFoundException
from src.tasks.crud.service import get_task_service


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


@service_method(commit=False)
async def get_tasks_stats_service(session, current_user_id: int) -> tuple[int, int, int, float]:
    """
    Получение статистики по задачам пользователя.
    """
    stmt = (
        select(
            func.count(Task.id).label("total_tasks"),
            func.sum(
                case(
                    (Task.completion_status == True, 1),
                    else_=0
                )
            ).label("completed_tasks"),
        )
        .where(Task.user_id == current_user_id)
    )

    result = await session.execute(stmt)
    stats = result.mappings().one()

    total_tasks = stats.get("total_tasks", 0)
    completed_tasks = stats.get("completed_tasks", 0) or 0
    uncompleted_tasks = total_tasks - completed_tasks
    if total_tasks > 0:
        completion_percentage = round((completed_tasks / total_tasks) * 100, 2)
    else:
        completion_percentage = 0.0

    return total_tasks, completed_tasks, uncompleted_tasks, completion_percentage


@service_method()
async def toggle_task_completion_status_service(
        session,
        current_user_id: int,
        task_id: int,
) -> Task:
    task = await get_task_service(session, current_user_id, task_id)

    task.completion_status = not task.completion_status
    return task

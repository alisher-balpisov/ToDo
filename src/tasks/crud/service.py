from datetime import datetime, timezone

from sqlalchemy import select

from src.common.models import Task
from src.common.utils import get_user_task, map_sort_rules
from src.core.decorators import service_method
from src.core.exception import (MissingRequiredFieldException,
                                ResourceNotFoundException)
from src.tasks.helpers import tasks_sort_mapping
from src.tasks.schemas import SortTasksValidator


@service_method()
async def create_task_service(
        session,
        current_user_id: int,
        task_name: str | None,
        task_text: str | None
) -> Task:
    if not task_name or not task_name.strip():
        raise MissingRequiredFieldException("имя задачи")

    new_task = Task(
        name=task_name,
        text=task_text,
        completion_status=False,
        date_time=datetime.now(timezone.utc).astimezone(),
        user_id=current_user_id,
    )
    session.add(new_task)
    return new_task


@service_method(commit=False)
async def get_tasks_service(
        session,
        current_user_id: int,
        sort: list,
        skip: int,
        limit: int,
) -> list[Task]:
    SortTasksValidator(sort=sort)
    stmt = select(Task).where(Task.user_id == current_user_id)

    order_by = map_sort_rules(sort, tasks_sort_mapping)
    if order_by:
        stmt = stmt.order_by(*order_by)
    stmt = stmt.offset(skip).limit(limit)

    result = await session.execute(stmt)
    tasks = result.scalars().all()
    return tasks


@service_method(commit=False)
async def get_task_service(
        session,
        current_user_id: int,
        task_id: int
) -> Task:
    task = await get_user_task(session, current_user_id, task_id)
    if task is None:
        raise ResourceNotFoundException("Задача", task_id)
    return task


@service_method()
async def update_task_service(
        session,
        current_user_id: int,
        task_id: int,
        name_update: str | None,
        text_update: str | None
) -> Task:
    task = await get_task_service(session, current_user_id, task_id)
    task.name = name_update if name_update else task.name
    task.text = text_update if text_update else task.text
    return task


@service_method()
async def delete_task_service(
        session,
        current_user_id: int,
        task_id: int
) -> None:
    task = await get_task_service(session, current_user_id, task_id)
    await session.delete(task)

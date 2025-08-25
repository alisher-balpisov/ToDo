from datetime import datetime, timezone

from src.common.models import Task
from src.common.utils import get_user_task, map_sort_rules
from src.core.decorators import handler, transactional
from src.core.exception import MissingRequiredFieldException
from src.tasks.helpers import tasks_sort_mapping
from src.tasks.schemas import SortTasksValidator


@handler
@transactional
def create_task_service(
        session,
        current_user_id: int,
        task_name: str | None,
        task_text: str | None
) -> Task:
    if not task_name.strip():
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


@handler
def get_tasks_service(
        session,
        current_user_id: int,
        sort: list,
        skip: int,
        limit: int,
) -> list[Task]:
    SortTasksValidator(sort=sort)

    tasks_query = session.query(Task).filter(
        Task.user_id == current_user_id)

    order_by = map_sort_rules(sort, tasks_sort_mapping)
    if order_by:
        tasks_query = tasks_query.order_by(*order_by)

    tasks = tasks_query.offset(skip).limit(limit).all()
    return tasks


@handler
def get_task_service(
        session,
        current_user_id: int,
        task_id: int
) -> Task:
    task = get_user_task(session, current_user_id, task_id)
    if task is None:
        raise ResourceNotFoundException("Задача", task_id)
    return task


@handler
@transactional
def update_task_service(
        session,
        current_user_id: int,
        task_id: int,
        name_update: str | None,
        text_update: str | None
) -> Task:
    task = get_user_task(session, current_user_id, task_id)
    if task is None:
        raise ResourceNotFoundException("Задача", task_id)
    task.name = name_update if name_update else task.name
    task.text = text_update if text_update else task.text
    return task


@handler
@transactional
def delete_task_service(
        session,
        current_user_id: int,
        task_id: int
) -> None:
    task = get_user_task(session, current_user_id, task_id)
    if task is None:
        raise ResourceNotFoundException("Задача", task_id)
    session.delete(task)

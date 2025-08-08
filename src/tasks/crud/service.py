from datetime import datetime, timezone
from typing

from fastapi import HTTPException, Query, status

from src.common.utils import map_sort_rules
from src.db.models import Task
from src.tasks.helpers.crud_helpers import SortTasksRule, tasks_sort_mapping


def create_task_service(
        session,
        current_user_id: int,
        task_name: str | None,
        task_text: str | None
) -> Task:
    if task_name is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Имя задачи не задано"
        )
    new_task = Task(
        name=task_name,
        text=task_text,
        completion_status=False,
        date_time=datetime.now(timezone.utc).astimezone(),
        user_id=current_user_id,
    )
    session.add(new_task)
    session.commit()
    session.refresh()
    return new_task


def get_tasks_service(
        session,
        current_user_id: int,
        sort: list,
        skip: int,
        limit: int,
) -> list[Task]:
    tasks_query = session.query(Task).filter(
        Task.user_id == current_user_id)

    order_by = map_sort_rules(sort, tasks_sort_mapping)
    if order_by:
        tasks_query = tasks_query.order_by(*order_by)

    tasks = tasks_query.offset(skip).limit(limit).all()
    return tasks

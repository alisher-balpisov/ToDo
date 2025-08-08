from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import or_

from src.auth.service import CurrentUser
from src.common.utils import get_user_task
from src.core.database import DbSession, PrimaryKey
from src.core.exceptions import handle_server_exception
from src.db.models import Task


def search_tasks_service(
        session,
        current_user_id: int,
        search_query: str,
) -> list[Task]:
    if not search_query:
        return []

    search_pattern = f"%{search_query}%"
    tasks = session.query(Task).filter(
        Task.user_id == current_user_id,
        or_(
            Task.name.ilike(search_pattern),
            Task.text.ilike(search_pattern)
        )
    ).all()

    return tasks


def get_tasks_stats_service(
        session,
        current_user_id: int
) -> tuple[int, int, int, float]:
    query = session.query(Task).filter(Task.user_id == current_user_id)

    total = int(query.count())
    completed = int(query.filter(Task.completion_status).count())
    uncompleted = int(query.filter(Task.completion_status.is_(False)).count())
    completion_percentage = round(
        (completed / total) * 100 if total > 0 else 0, 2)

    return total, completed, uncompleted, completion_percentage


def toggle_task_completion_status_service(
        session,
        current_user_id: int,
        task_id: int,
) -> Task:
    task = get_user_task(session, current_user_id, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    task.completion_status = not task.completion_status
    session.commit()
    session.refresh()
    return task

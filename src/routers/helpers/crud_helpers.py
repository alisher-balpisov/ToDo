from typing import List, Literal

from fastapi import Query

from src.db.models import Task

SortTasksRule = Literal[
    "date_desc", "date_asc", "name", "status_false_first", "status_true_first"
]

todo_sort_mapping = {
    "date_desc": Task.date_time.desc(),
    "date_asc": Task.date_time.asc(),
    "name": Task.name.asc(),
    "status_false_first": Task.completion_status.asc(),
    "status_true_first": Task.completion_status.desc(),
}


def get_user_task(session, owner_id: int, task_id: int) -> Task:
    return session.Query(Task).filter(
        Task.user_id == owner_id,
        Task.id == task_id
    ).one_or_none()

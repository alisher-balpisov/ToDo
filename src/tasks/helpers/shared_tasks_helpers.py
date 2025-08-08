from typing import Literal

from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.auth.models import ToDoUser
from src.auth.service import CurrentUser
from src.core.database import DbSession, get_db
from src.db.models import SharedAccessEnum, Task, TaskShare


def check_edit_permission(
        session: DbSession,
        current_user: CurrentUser,
        task_id: int,
) -> Task:

    task = (
        session.query(Task)
        .join(TaskShare, TaskShare.task_id == Task.id)
        .filter(
            Task.id == task_id,
            TaskShare.target_user_id == current_user.id,
            TaskShare.permission_level == SharedAccessEnum.edit,
        )
        .first()
    )
    if not task:
        raise HTTPException(
            status_code=403, detail="Нет доступа для редактирования задачи"
        )
    return task


SortSharedTasksRule = Literal[
    "date_desc",
    "date_asc",
    "name",
    "status_false_first",
    "status_true_first",
    "permission_view_first",
    "permission_edit_first",
]

shared_tasks_sort_mapping = {
    "date_desc": Task.date_time.desc(),
    "date_asc": Task.date_time.asc(),
    "name": Task.name.asc(),
    "status_false_first": Task.completion_status.asc(),
    "status_true_first": Task.completion_status.desc(),
    "permission_view_first": TaskShare.permission_level.asc(),
    "permission_edit_first": TaskShare.permission_level.desc(),
}

from typing import List, Literal

from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.auth.models import ToDoUser
from src.auth.service import CurrentUser
from src.core.database import DbSession, get_db
from src.db.models import SharedAccessEnum, Task, TaskShare


def check_view_permission(
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
            TaskShare.permission_level.in_(
                [SharedAccessEnum.VIEW, SharedAccessEnum.EDIT]
            ),
        )
        .first()
    )
    if not task:
        raise HTTPException(
            status_code=403, detail="Нет доступа для просмотра задачи")
    return task


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
            TaskShare.permission_level == SharedAccessEnum.EDIT,
        )
        .first()
    )
    if not task:
        raise HTTPException(
            status_code=403, detail="Нет доступа для редактирования задачи"
        )
    return task


SortRule = Literal[
    "date_desc",
    "date_asc",
    "name",
    "status_false_first",
    "status_true_first",
    "permission_view_first",
    "permission_edit_first",
]

todo_sort_mapping = {
    "date_desc": Task.date_time.desc(),
    "date_asc": Task.date_time.asc(),
    "name": Task.name.asc(),
    "status_false_first": Task.completion_status.asc(),
    "status_true_first": Task.completion_status.desc(),
    "permission_view_first": TaskShare.permission_level.asc(),
    "permission_edit_first": TaskShare.permission_level.desc(),
}


def check_task_access_level(
        session: DbSession,
        current_user: CurrentUser,
        task_id: int,
) -> tuple[Task, SharedAccessEnum]:

    owned_task = (
        session.query(Task)
        .filter(Task.id == task_id, Task.user_id == current_user.id)
        .first()
    )

    if owned_task:
        return owned_task, SharedAccessEnum.EDIT

    shared_task = (
        session.query(Task, TaskShare.permission_level)
        .join(TaskShare, TaskShare.task_id == Task.id)
        .filter(Task.id == task_id, TaskShare.target_user_id == current_user.id)
        .first()
    )

    if not shared_task:
        raise HTTPException(
            status_code=403, detail="Нет доступа к данной задаче")

    task, permission_level = shared_task
    return task, permission_level


def get_task_collaborators(
        session: DbSession,
        current_user: CurrentUser,
        task_id: int,
) -> list[dict]:

    task, access_level = check_task_access_level(task_id, current_user)
    owner = session.query(ToDoUser).filter(ToDoUser.id == task.user_id).first()
    collaborators = []

    if owner:
        collaborators.append(
            {
                "user_id": owner.id,
                "username": owner.username,
                "email": owner.email,
                "role": "owner",
                "permission_level": "full_access",
                "can_revoke": False,
            }
        )

    shares = (
        session.query(TaskShare, ToDoUser)
        .join(ToDoUser, ToDoUser.id == TaskShare.target_user_id)
        .filter(TaskShare.task_id == task_id)
        .all()
    )

    for share, ToDoUser in shares:
        collaborators.append(
            {
                "user_id": ToDoUser.id,
                "username": ToDoUser.username,
                "email": ToDoUser.email,
                "role": "collaborator",
                "permission_level": share.permission_level.value,
                "shared_date": share.date_time.isoformat(),
                "can_revoke": task.user_id == current_user.id,
            }
        )

    return collaborators

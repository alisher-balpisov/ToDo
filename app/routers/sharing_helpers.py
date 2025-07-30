from typing import List, Literal

from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import SharedAccessEnum, TaskShare, ToDo, User


def check_owned_task(
    task_id: int,
    current_user: User,
    db: Session = Depends(get_db)
) -> None | HTTPException:

    task = (
        db.query(ToDo)
        .filter(ToDo.id == task_id, ToDo.user_id == current_user.id)
        .first()
    )
    if not task:
        raise HTTPException(
            status_code=404, detail="Задача не найдена или вам не принадлежит"
        )


def get_existing_user(username: str, db: Session = Depends(get_db)) -> User | HTTPException:
    shared_with_user = db.query(User).filter(User.username == username).first()
    if not shared_with_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return shared_with_user


def get_shared_access(
    task_id: int, current_user: User,
    shared_with_user: User,
    db: Session = Depends(get_db)
) -> TaskShare | HTTPException:

    share = (
        db.query(TaskShare)
        .filter(
            TaskShare.task_id == task_id,
            TaskShare.owner_id == current_user.id,
            TaskShare.shared_with_id == shared_with_user.id,
        )
        .first()
    )
    if not share:
        raise HTTPException(status_code=404, detail="Доступ не найден")
    return share


def check_view_permission(
    task_id: int,
    current_user: User,
    db: Session = Depends(get_db)
) -> ToDo:

    task = (
        db.query(ToDo)
        .join(TaskShare, TaskShare.task_id == ToDo.id)
        .filter(
            ToDo.id == task_id,
            TaskShare.shared_with_id == current_user.id,
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
    task_id: int,
    current_user: User,
    db: Session = Depends(get_db)
) -> ToDo:

    task = (
        db.query(ToDo)
        .join(TaskShare, TaskShare.task_id == ToDo.id)
        .filter(
            ToDo.id == task_id,
            TaskShare.shared_with_id == current_user.id,
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
    "date_desc": ToDo.date_time.desc(),
    "date_asc": ToDo.date_time.asc(),
    "name": ToDo.name.asc(),
    "status_false_first": ToDo.completion_status.asc(),
    "status_true_first": ToDo.completion_status.desc(),
    "permission_view_first": TaskShare.permission_level.asc(),
    "permission_edit_first": TaskShare.permission_level.desc(),
}


def validate_sort(
    sort: List[SortRule] = Query(default=["date_desc"]),
) -> List[SortRule]:

    if "date_desc" in sort and "date_asc" in sort:
        raise ValueError(
            "Нельзя использовать одновременно 'date_desc' и 'date_asc'")

    if "status_false_first" in sort and "status_true_first" in sort:
        raise ValueError(
            "Нельзя использовать одновременно 'status_false_first' и 'status_true_first'"
        )

    if "permission_view_first" in sort and "permission_edit_first" in sort:
        raise ValueError(
            "Нельзя использовать одновременно 'permission_view_first' и 'permission_edit_first'"
        )

    return sort


def check_task_access_level(
    task_id: int,
    current_user: User,
    db: Session = Depends(get_db)
) -> tuple[ToDo, SharedAccessEnum]:

    owned_task = (
        db.query(ToDo)
        .filter(ToDo.id == task_id, ToDo.user_id == current_user.id)
        .first()
    )

    if owned_task:
        return owned_task, SharedAccessEnum.EDIT

    shared_task = (
        db.query(ToDo, TaskShare.permission_level)
        .join(TaskShare, TaskShare.task_id == ToDo.id)
        .filter(ToDo.id == task_id, TaskShare.shared_with_id == current_user.id)
        .first()
    )

    if not shared_task:
        raise HTTPException(
            status_code=403, detail="Нет доступа к данной задаче")

    task, permission_level = shared_task
    return task, permission_level


def get_task_collaborators(
    task_id: int,
    current_user: User,
    db: Session = Depends(get_db)
) -> list[dict]:

    task, access_level = check_task_access_level(task_id, current_user)
    owner = db.query(User).filter(User.id == task.user_id).first()
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
        db.query(TaskShare, User)
        .join(User, User.id == TaskShare.shared_with_id)
        .filter(TaskShare.task_id == task_id)
        .all()
    )

    for share, user in shares:
        collaborators.append(
            {
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "role": "collaborator",
                "permission_level": share.permission_level.value,
                "shared_date": share.date_time.isoformat(),
                "can_revoke": task.user_id == current_user.id,
            }
        )

    return collaborators

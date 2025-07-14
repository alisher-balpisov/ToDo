from typing import Literal

from fastapi import HTTPException

from app.db.models import SharedAccessEnum, TaskShare, ToDo, User, session


def check_owned_task(task_id: int, current_user: User) -> None | HTTPException:
    task = (
        session.query(ToDo)
        .filter(ToDo.id == task_id, ToDo.user_id == current_user.id)
        .first()
    )
    if not task:
        raise HTTPException(
            status_code=404, detail="Задача не найдена или вам не принадлежит"
        )


def get_existing_user(username: str) -> User | HTTPException:
    shared_with_user = session.query(User).filter(
        User.username == username).first()
    if not shared_with_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return shared_with_user


def get_shared_access(
    task_id: int, current_user: User, shared_with_user: User
) -> TaskShare | HTTPException:
    share = (
        session.query(TaskShare)
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


def check_view_permission(task_id: int, current_user: User) -> ToDo:
    task = (
        session.query(ToDo)
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


def check_edit_permission(task_id: int, current_user: User) -> ToDo:
    task = (
        session.query(ToDo)
        .join(TaskShare, TaskShare.task_id == ToDo.id)
        .filter(
            ToDo.id == task_id,
            TaskShare.shared_with_id == current_user.id,
            TaskShare.permission_level == SharedAccessEnum.EDIT
        )
        .first()
    )
    if not task:
        raise HTTPException(
            status_code=403, detail="Нет доступа для редактирования задачи")
    return task


SortRule = Literal[
    "date_desc", "date_asc",
    "name",
    "status_false_first", "status_true_first",
    "permission_view_first", "permission_edit_first"
]

todo_sort_mapping = {
    "date_desc": ToDo.date_time.desc(),
    "date_asc": ToDo.date_time.asc(),
    "name": ToDo.name.asc(),
    "status_false_first": ToDo.completion_status.asc(),
    "status_true_first": ToDo.completion_status.desc(),
    "permission_view_first": TaskShare.permission_level.asc(), 
    "permission_edit_first": TaskShare.permission_level.desc()
}

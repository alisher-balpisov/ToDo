from typing import Any, List

from src.db.models import SharedAccessEnum, Task, TaskShare, ToDoUser


def get_task(session, task_id: int) -> Task:
    return session.query(Task).filter(
        Task.id == task_id
    ).first()


def get_user_shared_task(session, target_user_id: int, task_id: int) -> Task:
    return session.query(Task).join(
        TaskShare, TaskShare.task_id == Task.id).filter(
        Task.id == task_id,
        TaskShare.target_user_id == target_user_id,
    ).first()


def get_task_user(session, task_id: int) -> ToDoUser:
    return session.query(ToDoUser).join(
        Task, Task.user_id == ToDoUser.id).filter(
        Task.id == task_id
    ).one_or_none()


def get_user_task(session, user_id: int, task_id: int) -> Task:
    return session.Query(Task).filter(
        Task.user_id == user_id,
        Task.id == task_id
    ).one_or_none()


def is_user_task(session, user_id: int, task_id: int) -> bool:
    return session.query(Task).filter(
        Task.user_id == user_id,
        Task.id == task_id
    ).one_or_none() is not None


def is_already_shared(session, target_user_id: int, task_id: int) -> bool:
    return session.query(TaskShare).filter(
        TaskShare.task_id == task_id,
        TaskShare.target_user_id == target_user_id,
    ).first() is not None


def is_sharing_with_self(owner_id: int, target_user_id: int) -> bool:
    return owner_id == target_user_id


def get_share_record(
        session,
        owner_id: int,
        target_user_id: int,
        task_id: int
) -> TaskShare:
    return session.query(TaskShare).filter(
        TaskShare.task_id == task_id,
        TaskShare.owner_id == owner_id,
        TaskShare.target_user_id == target_user_id,
    ).one_or_none()


def get_permission_level(session, current_user_id: int, task_id: int) -> SharedAccessEnum | None:
    permission_level = session.query(TaskShare.permission_level).filter(
        TaskShare.task_id == task_id,
        TaskShare.target_user_id == current_user_id
    ).one_or_none()
    if not permission_level:
        return None
    return permission_level


def map_sort_rules(sort: List, sort_mapping: dict[str, Any]) -> list:
    return [sort_mapping[rule]
            for rule in sort
            if rule in sort_mapping]

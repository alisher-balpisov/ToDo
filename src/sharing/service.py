from src.db.models import SharedAccessEnum, Task, TaskShare


def get_user_shared_task(session, target_user_id: int, task_id: int) -> Task:
    return session.query(Task).join(
        TaskShare, TaskShare.task_id == Task.id).filter(
        Task.id == task_id,
        TaskShare.target_user_id == target_user_id,
    ).first()


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

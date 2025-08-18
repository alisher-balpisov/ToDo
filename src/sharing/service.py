from src.common.models import Task
from src.core.database import DbSession

from .models import Share, SharedAccessEnum


def get_user_shared_task(session, target_user_id: int, task_id: int) -> Task:
    return session.query(Task).join(
        Share, Share.task_id == Task.id).filter(
        Task.id == task_id,
        Share.target_user_id == target_user_id,
    ).first()


def is_already_shared(session, target_user_id: int, task_id: int) -> bool:
    return session.query(Share).filter(
        Share.task_id == task_id,
        Share.target_user_id == target_user_id,
    ).first() is not None


def is_sharing_with_self(owner_id: int, target_user_id: int) -> bool:
    return owner_id == target_user_id


def is_collaborator(session, target_user_id, task_id):
    return session.query(Share).filter(
        Share.task_id == task_id,
        Share.target_user_id == target_user_id
    ).first()


def get_share_record(
        session,
        owner_id: int,
        target_user_id: int,
        task_id: int
) -> Share:
    return session.query(Share).filter(
        Share.task_id == task_id,
        Share.owner_id == owner_id,
        Share.target_user_id == target_user_id,
    ).one_or_none()


def get_permission_level(session: DbSession, current_user_id: int, task_id: int) -> SharedAccessEnum | None:
    permission_level = session.query(Share.permission_level).filter(
        Share.task_id == task_id,
        Share.target_user_id == current_user_id
    ).scalar()
    if not permission_level:
        return None
    return permission_level

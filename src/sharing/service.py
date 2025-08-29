from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.models import Task

from .models import Share, SharedAccessEnum


async def get_user_shared_task(session: AsyncSession, target_user_id: int, task_id: int) -> Task | None:
    stmt = (
        select(Task)
        .join(Share, Share.task_id == Task.id)
        .where(Task.id == task_id, Share.target_user_id == target_user_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def is_already_shared(session: AsyncSession, target_user_id: int, task_id: int) -> bool:
    stmt = select(Share).where(
        Share.task_id == task_id,
        Share.target_user_id == target_user_id,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


async def is_sharing_with_self(owner_id: int, target_user_id: int) -> bool:
    return owner_id == target_user_id


async def is_task_collaborator(session: AsyncSession, target_user_id: int, task_id: int) -> bool:
    stmt = select(Share).where(
        Share.task_id == task_id,
        Share.target_user_id == target_user_id
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


async def get_share_record(
    session: AsyncSession,
    owner_id: int,
    target_user_id: int,
    task_id: int,
) -> Share | None:
    stmt = select(Share).where(
        Share.task_id == task_id,
        Share.owner_id == owner_id,
        Share.target_user_id == target_user_id,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_permission_level(session: AsyncSession, current_user_id: int, task_id: int) -> SharedAccessEnum | None:
    stmt = select(Share.permission_level).where(
        Share.task_id == task_id,
        Share.target_user_id == current_user_id
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

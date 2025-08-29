from typing import Any

from fastapi import APIRouter, Query

from src.core.types import CurrentUser, DbSession, PrimaryKey
from src.sharing.helpers import SortSharedTasksRule

from .service import (get_shared_task_service, get_shared_tasks_service,
                      get_task_collaborators_service,
                      get_task_permissions_service)

router = APIRouter()


@router.get("/shared-tasks")
async def get_shared_tasks(
        session: DbSession,
        current_user: CurrentUser,
        sort_shared_tasks: list[SortSharedTasksRule] = Query(default=[
                                                             "date_desc"]),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
) -> list[dict]:
    tasks_info = await get_shared_tasks_service(session=session,
                                                current_user_id=current_user.id,
                                                sort=sort_shared_tasks,
                                                skip=skip,
                                                limit=limit)
    return [
        {
            "id": task.id,
            "task_name": task.name,
            "completion_status": task.completion_status,
            "date_time": task.date_time.isoformat(),
            "text": task.text,
            "owner_username": owner_username,
            "permission_level": permission_level,
        } for task, owner_username, permission_level in tasks_info
    ]


@router.get("/shared-tasks/{task_id}")
async def get_shared_task(
        session: DbSession,
        current_user: CurrentUser,
        task_id: PrimaryKey
) -> dict[str, Any]:
    task, owner, permission_level = await get_shared_task_service(session=session,
                                                                  current_user_id=current_user.id,
                                                                  task_id=task_id)
    return {
        "id": task.id,
        "task_name": task.name,
        "completion_status": task.completion_status,
        "date_time": task.date_time.isoformat(),
        "text": task.text,
        "file_name": task.file_name,
        "owner_username": owner.username,
        "permission_level": permission_level,
    }


@router.get("/tasks/{task_id}/collaborators")
async def get_task_collaborators(
    session: DbSession,
    current_user: CurrentUser,
    task_id: PrimaryKey
) -> dict[str, Any]:
    collaborators = await get_task_collaborators_service(session=session,
                                                         current_user_id=current_user.id,
                                                         task_id=task_id)
    return {
        "task_id": task_id,
        "total_collaborators": len(collaborators),
        "collaborators": collaborators,
    }


@router.get("/shared-tasks/{task_id}/permissions")
async def get_task_permissions(
    session: DbSession,
    current_user: CurrentUser,
    task_id: PrimaryKey
) -> dict[str, Any]:
    task, permission_level, permissions = await get_task_permissions_service(session=session,
                                                                             current_user_id=current_user.id,
                                                                             task_id=task_id)
    return {
        "task_id": task_id,
        "task_name": task.name,
        "permission_level": permission_level.value if permission_level else "owner",
        "permissions": permissions,
    }

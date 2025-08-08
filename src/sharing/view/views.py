from typing import Any

from fastapi import APIRouter, Query

from src.auth.service import CurrentUser
from src.core.database import DbSession, PrimaryKey
from src.core.exceptions import handle_server_exception
from src.tasks.helpers.shared_tasks_helpers import SortSharedTasksRule

from .service import (get_shared_task_service, get_shared_tasks_service,
                      get_task_collaborators_service,
                      get_task_permissions_service)

router = APIRouter()


@router.get("/shared-tasks")
def get_shared_tasks(
        session: DbSession,
        current_user: CurrentUser,
        sort_shared_tasks: list[SortSharedTasksRule] = Query(default=[]),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),

) -> list[dict]:
    try:
        tasks_info = get_shared_tasks_service(session=session,
                                              current_user_id=current_user.id,
                                              sort_shared_tasks=sort_shared_tasks,
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

    except Exception as e:
        handle_server_exception(
            e, "Ошибка сервера при получении расшаренных задач")


@router.get("/shared-tasks/{task_id}")
def get_shared_task(
        session: DbSession,
        current_user: CurrentUser,
        task_id: PrimaryKey
) -> dict[str, Any]:
    try:
        task, owner, permission_level = get_shared_task_service(session=session,
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

    except Exception as e:
        handle_server_exception(
            e, "Ошибка сервера при получении расшаренной задачи")


@router.get("/tasks/{task_id}/collaborators")
def get_task_collaborators(
    session: DbSession,
    current_user: CurrentUser,
    task_id: PrimaryKey
) -> dict[str, Any]:
    try:
        collaborators = get_task_collaborators_service(session=session,
                                                       current_user_id=current_user.id,
                                                       task_id=task_id)
        return {
            "task_id": task_id,
            "total_collaborators": len(collaborators),
            "collaborators": collaborators,
        }

    except Exception as e:
        handle_server_exception(
            e, "Ошибка сервера при получении списка соавторов")


@router.get("/shared-tasks/{task_id}/permissions")
def get_task_permissions(
    session: DbSession,
    current_user: CurrentUser,
    task_id: PrimaryKey
) -> dict[str, Any]:
    try:
        task, permission_level, permissions = get_task_permissions_service(session=session,
                                                                           current_user_id=current_user.id,
                                                                           task_id=task_id)
        return {
            "task_id": task_id,
            "task_name": task.name,
            "permission_level": permission_level.value if permission_level else "owner",
            "permissions": permissions,
        }

    except Exception as e:
        handle_server_exception(e, "Ошибка сервера при получении прав доступа")

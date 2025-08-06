from typing import Annotated, Any, List

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from src.auth.models import ToDoUser
from src.auth.service import CurrentUser
from src.core.database import DbSession, PrimaryKey, UsernameStr
from src.core.exceptions import handle_server_exception
from src.db.models import SharedAccessEnum, Task, TaskShare
from src.db.schemas import SortSharedTasksValidator, TaskShareSchema
from src.routers.helpers.shared_tasks_helpers import (SortSharedTasksRule,
                                                      check_task_access_level,
                                                      check_view_permission,
                                                      todo_sort_mapping)

from .service import (get_shared_task_service, get_shared_tasks_service,
                      get_task_collaborators_service, share_task_service,
                      unshare_task_service, update_share_permission_service)

router = APIRouter()


@router.get("/shared-tasks")
def get_shared_tasks(
        session: DbSession,
        current_user: CurrentUser,
        sort_shared_tasks: List[SortSharedTasksRule] = Query(default=[]),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),

) -> list[dict]:
    try:
        result = get_shared_tasks_service(session=session,
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
            } for task, owner_username, permission_level in result
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
        result = get_shared_task_service(session=session,
                                         current_user_id=current_user.id,
                                         task_id=task_id)
        task, owner_username, permission_level = result
        return {
            "id": task.id,
            "task_name": task.name,
            "completion_status": task.completion_status,
            "date_time": task.date_time.isoformat(),
            "text": task.text,
            "file_name": task.file_name,
            "owner_username": owner_username,
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

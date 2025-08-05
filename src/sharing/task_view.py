from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from src.auth.models import ToDoUser
from src.auth.service import CurrentUser
from src.core.database import DbSession, PrimaryKey
from src.core.exceptions import handle_server_exception
from src.db.models import SharedAccessEnum, Task, TaskShare
from src.db.schemas import SortSharedTasksValidator
from src.routers.helpers.shared_tasks_helpers import (SortRule,
                                                      check_task_access_level,
                                                      check_view_permission,
                                                      get_task_collaborators,
                                                      todo_sort_mapping)

router = APIRouter()


@router.get("/shared-tasks")
def get_shared_tasks(
        session: DbSession,
        current_user: CurrentUser,
        sort: SortSharedTasksValidator,
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),

) -> list[dict]:
    try:
        query = (
            session.query(
                Task,
                ToDoUser.username.label("owner_username"),
                TaskShare.permission_level
            )
            .join(TaskShare, TaskShare.task_id == Task.id)
            .join(ToDoUser, ToDoUser.id == Task.user_id)
            .filter(TaskShare.target_user_id == current_user.id)
        )
        order_by = []
        for rule in sort.sort_shared_tasks:
            if rule in todo_sort_mapping:
                order_by.append(todo_sort_mapping[rule])

        if order_by:
            query = query.order_by(*order_by)
        tasks = query.offset(skip).limit(limit).all()
        return [
            {
                "id": task.id,
                "task_name": task.name,
                "completion_status": task.completion_status,
                "date_time": task.date_time.isoformat(),
                "text": task.text,
                "owner_username": owner_username,
                "permission_level": permission_level,
            }
            for task, owner_username, permission_level in tasks
        ]
    except Exception as e:
        handle_server_exception(
            e, "Ошибка сервера при получении расшаренных задач")


@router.get("/shared-tasks/{task_id}")
def get_shared_task(
        session: DbSession,
        current_user: CurrentUser,
        task_id: Annotated[int, PrimaryKey],

) -> dict[str, Any]:
    try:
        task_info = check_view_permission(task_id, current_user)

        task_info = (
            session.query(
                Task,
                ToDoUser.username.label("owner_username"),
                TaskShare.permission_level
            )
            .join(TaskShare, TaskShare.task_id == Task.id)
            .join(ToDoUser, ToDoUser.id == Task.user_id)
            .filter(
                Task.id == task_id,
                TaskShare.target_user_id == current_user.id
            ).first()
        )

        if not task_info:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        task_obj, owner_username, permission_level = task_info
        return {
            "id": task_obj.id,
            "task_name": task_obj.name,
            "completion_status": task_obj.completion_status,
            "date_time": task_obj.date_time.strftime("%Y-%m-%d | %H:%M:%S"),
            "text": task_obj.text,
            "file_name": task_obj.file_name,
            "owner_username": owner_username,
            "permission_level": permission_level,
        }

    except Exception as e:
        handle_server_exception(
            e, "Ошибка сервера при получении расшаренной задачи")


@router.get("/shared-tasks/{task_id}/permissions")
def get_my_task_permissions(
    task_id: Annotated[int, PrimaryKey],

) -> dict[str, Any]:
    try:
        task, access_level = check_task_access_level(task_id, current_user)

        permissions = {
            "can_view": True,
            "can_edit": access_level == SharedAccessEnum.EDIT,
            "can_delete": task.user_id == current_user.id,
            "can_share": task.user_id == current_user.id,
            "can_upload_files": access_level == SharedAccessEnum.EDIT,
            "can_change_status": access_level == SharedAccessEnum.EDIT,
            "is_owner": task.user_id == current_user.id,
        }
        return {
            "task_id": task_id,
            "task_name": task.name,
            "access_level": access_level.value if access_level else "owner",
            "permissions": permissions,
        }

    except Exception as e:
        handle_server_exception(e, "Ошибка сервера при получении прав доступа")


@router.get("/tasks/{task_id}/collaborators")
def get_task_collaborators(
    task_id: Annotated[int, PrimaryKey]
) -> dict[str, Any]:
    try:
        collaborators = get_task_collaborators(task_id, current_user)
        return {
            "task_id": task_id,
            "total_collaborators": len(collaborators),
            "collaborators": collaborators,
        }

    except Exception as e:
        handle_server_exception(
            e, "Ошибка сервера при получении списка соавторов")

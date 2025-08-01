from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.auth.jwt_handler import get_current_active_user
from app.db.database import get_db
from app.db.models import SharedAccessEnum, TaskShare, ToDo, User
from app.handle_exception import handle_server_exception
from app.routers.helpers.sharing_helpers import (SortRule,
                                                 check_task_access_level,
                                                 check_view_permission,
                                                 get_task_collaborators,
                                                 todo_sort_mapping,
                                                 validate_sort)

router = APIRouter()


@router.get("/shared-tasks")
def get_shared_tasks(
    sort: List[SortRule] = Depends(validate_sort),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> list[dict]:
    try:
        query = (
            db.query(
                ToDo,
                User.username.label("owner_username"),
                TaskShare.permission_level
            )
            .join(TaskShare, TaskShare.task_id == ToDo.id)
            .join(User, User.id == ToDo.user_id)
            .filter(TaskShare.shared_with_id == current_user.id)
        )
        order_by = []
        for rule in sort:
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
    task_id: int = Path(ge=1),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    try:
        task_info = check_view_permission(task_id, current_user)

        task_info = (
            db.query(
                ToDo,
                User.username.label("owner_username"),
                TaskShare.permission_level
            )
            .join(TaskShare, TaskShare.task_id == ToDo.id)
            .join(User, User.id == ToDo.user_id)
            .filter(
                ToDo.id == task_id,
                TaskShare.shared_with_id == current_user.id
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
    task_id: int = Path(ge=1),
    current_user: User = Depends(get_current_active_user)
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
    task_id: int = Path(ge=1),
    current_user: User = Depends(get_current_active_user),
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

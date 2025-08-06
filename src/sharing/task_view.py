from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from src.auth.models import ToDoUser
from src.auth.service import CurrentUser
from src.core.database import DbSession, PrimaryKey
from src.core.exceptions import handle_server_exception
from src.db.models import SharedAccessEnum, Task, TaskShare
from src.db.schemas import SortSharedTasksValidator
from src.routers.helpers.shared_tasks_helpers import (SortSharedTasksRule,
                                                      check_task_access_level,
                                                      check_view_permission,
                                                      get_task_collaborators,
                                                      todo_sort_mapping)

router = APIRouter()





@router.get("/shared-tasks/{task_id}/permissions")
def get_my_task_permissions(
    task_id: PrimaryKey,

) -> dict[str, Any]:
    try:
        task, access_level = check_task_access_level(task_id, current_user)

        permissions = {
            "can_view": True,
            "can_edit": access_level == SharedAccessEnum.edit,
            "can_delete": task.user_id == current_user.id,
            "can_share": task.user_id == current_user.id,
            "can_upload_files": access_level == SharedAccessEnum.edit,
            "can_change_status": access_level == SharedAccessEnum.edit,
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




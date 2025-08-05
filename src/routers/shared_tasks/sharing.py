from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from src.auth.models import ToDoUser
from src.auth.service import CurrentUser
from src.db.database import DbSession, PrimaryKey
from src.db.models import SharedAccessEnum, TaskShare
from src.db.schemas import TaskShareSchema
from src.handle_exception import handle_server_exception
from src.routers.helpers.sharing_helpers import (check_owned_task,
                                                 get_existing_user,
                                                 get_shared_access)

router = APIRouter()


@router.post("/tasks/{TaskShareSchema.task_id}/shares")
def share_task(
        session: DbSession,
        current_user: CurrentUser,
        share_data: TaskShareSchema,

) -> dict[str, str]:
    try:
        check_owned_task(share_data.task_id, current_user)
        shared_with_user = get_existing_user(share_data.shared_with_username)

        if shared_with_user.id == current_user.id:
            raise HTTPException(
                status_code=400, detail="Нельзя поделиться задачей с самим собой"
            )
        already_shared = (
            session.query(TaskShare).filter(
                TaskShare.task_id == share_data.task_id,
                TaskShare.shared_with_id == shared_with_user.id,
            ).first()
        )

        if already_shared:
            raise HTTPException(
                status_code=400, detail="Доступ уже предоставлен этому пользователю"
            )
        new_share = TaskShare(
            task_id=share_data.task_id,
            owner_id=current_user.id,
            shared_with_id=shared_with_user.id,
            permission_level=share_data.permission_level,
        )
        session.add(new_share)
        session.commit()
        return {"message": "Задача успешно расшарена с пользователем"}
    except Exception as e:
        session.rollback()
        handle_server_exception(
            e, "Ошибка сервера при предоставлении доступа к задаче")


@router.delete("/tasks/{task_id}/shares/{username}")
def unshare_task(
        session: DbSession,
        current_user: CurrentUser,
        task_id: Annotated[int, PrimaryKey],
        username: Annotated[str, Path(max_length=30)],

) -> dict[str, str]:
    try:
        check_owned_task(task_id, current_user)
        shared_with_user = get_existing_user(username)
        share = get_shared_access(task_id, current_user, shared_with_user)
        session.delete(share)
        session.commit()
        return {"message": "Доступ к задаче успешно отозван"}
    except Exception as e:
        session.rollback()
        handle_server_exception(
            e, "Ошибка сервера при отзыве доступа к задаче")


@router.put("/tasks/{task_id}/shares/{username}")
def update_share_permission(
        session: DbSession,
        current_user: CurrentUser,
        new_permission: SharedAccessEnum,
        task_id: Annotated[int, PrimaryKey],
        username: Annotated[str, Path(max_length=30)],

) -> dict[str, str]:
    try:
        check_owned_task(task_id, current_user)
        shared_with_user = get_existing_user(username)
        share = get_shared_access(task_id, current_user, shared_with_user)
        share.permission_level = new_permission
        session.commit()
        return {"message": "Уровень доступа успешно обновлен"}
    except Exception as e:
        session.rollback()
        handle_server_exception(
            e, "Ошибка сервера при обновлении уровня доступа")

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.auth.jwt_handler import get_current_active_user
from app.db.database import get_db
from app.db.models import SharedAccessEnum, TaskShare, User
from app.db.schemas import TaskShareSchema
from app.handle_exception import handle_server_exception
from app.routers.helpers.sharing_helpers import (check_owned_task,
                                                 get_existing_user,
                                                 get_shared_access)

router = APIRouter()


@router.post("/tasks/{TaskShareSchema.task_id}/shares")
def share_task(
    share_data: TaskShareSchema,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict[str, str]:
    try:
        check_owned_task(share_data.task_id, current_user)
        shared_with_user = get_existing_user(share_data.shared_with_username)

        if shared_with_user.id == current_user.id:
            raise HTTPException(
                status_code=400, detail="Нельзя поделиться задачей с самим собой"
            )
        already_shared = (
            db.query(TaskShare).filter(
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
        db.add(new_share)
        db.commit()
        return {"message": "Задача успешно расшарена с пользователем"}
    except Exception as e:
        db.rollback()
        handle_server_exception(
            e, "Ошибка сервера при предоставлении доступа к задаче")


@router.delete("/tasks/{task_id}/shares/{username}")
def unshare_task(
    task_id: int = Path(ge=1),
    username: str = Path(max_length=30),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict[str, str]:
    try:
        check_owned_task(task_id, current_user)
        shared_with_user = get_existing_user(username)
        share = get_shared_access(task_id, current_user, shared_with_user)
        db.delete(share)
        db.commit()
        return {"message": "Доступ к задаче успешно отозван"}
    except Exception as e:
        db.rollback()
        handle_server_exception(
            e, "Ошибка сервера при отзыве доступа к задаче")


@router.put("/tasks/{task_id}/shares/{username}")
def update_share_permission(
    new_permission: SharedAccessEnum,
    task_id: int = Path(ge=1),
    username: str = Path(max_length=30),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict[str, str]:
    try:
        check_owned_task(task_id, current_user)
        shared_with_user = get_existing_user(username)
        share = get_shared_access(task_id, current_user, shared_with_user)
        share.permission_level = new_permission
        db.commit()
        return {"message": "Уровень доступа успешно обновлен"}
    except Exception as e:
        db.rollback()
        handle_server_exception(
            e, "Ошибка сервера при обновлении уровня доступа")

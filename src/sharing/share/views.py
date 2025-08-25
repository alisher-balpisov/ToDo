from fastapi import APIRouter

from src.core.types import CurrentUser, DbSession, PrimaryKey, UsernameStr
from src.sharing.schemas import TaskShareSchema

from .service import share_task_service, unshare_task_service

router = APIRouter()


@router.post("/tasks/{task_id}/shares")
def share_task(
        session: DbSession,
        current_user: CurrentUser,
        task_id: PrimaryKey,
        share_data: TaskShareSchema,
):
    share_task_service(session=session,
                       owner_id=current_user.id,
                       task_id=task_id,
                       target_username=share_data.target_username,
                       permission_level=share_data.permission_level)
    return {"msg": "Задача успешно расшарена с пользователем"}


@router.delete("/tasks/{task_id}/shares/{target_username}")
def unshare_task(
        session: DbSession,
        current_user: CurrentUser,
        task_id: PrimaryKey,
        target_username: UsernameStr,
) -> dict[str, str]:
    unshare_task_service(session=session,
                         owner_id=current_user.id,
                         task_id=task_id,
                         target_username=target_username)
    return {"msg": "Доступ к задаче успешно отозван"}

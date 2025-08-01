import mimetypes
from io import BytesIO
from typing import Any, List

from fastapi import (APIRouter, Body, Depends, File, HTTPException, Path,
                     Query, UploadFile)
from fastapi.responses import StreamingResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth.jwt_handler import get_current_active_user
from app.db.database import get_db
from app.db.models import SharedAccessEnum, TaskShare, ToDo, User
from app.db.schemas import TaskShareSchema, ToDoSchema
from app.routers.handle_exception import check_handle_exception
from app.routers.sharing_helpers import (SortRule, check_edit_permission,
                                         check_owned_task,
                                         check_task_access_level,
                                         check_view_permission,
                                         get_existing_user, get_shared_access,
                                         get_task_collaborators,
                                         todo_sort_mapping, validate_sort)

router = APIRouter()
# prefix="/tasks/share"


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
            db.query(TaskShare)
            .filter(
                TaskShare.task_id == share_data.task_id,
                TaskShare.shared_with_id == shared_with_user.id,
            )
            .first()
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
        check_handle_exception(
            e, "Ошибка сервера при предоставлении доступа к задаче")


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
                ToDo, User.username.label(
                    "owner_username"), TaskShare.permission_level
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
        check_handle_exception(
            e, "Ошибка сервера при получении расшаренных задач")


@router.get("/shared-tasks/{task_id}/file")
def get_shared_task_file(
    task_id: int = Path(ge=1),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> StreamingResponse:
    try:
        task = (
            db.query(ToDo)
            .join(TaskShare, TaskShare.task_id == ToDo.id)
            .filter(
                ToDo.id == task_id,
                or_(
                    ToDo.user_id == current_user.id,
                    TaskShare.shared_with_id == current_user.id,
                ),
            )
            .first()
        )

        if not task or not task.file_data:
            raise HTTPException(status_code=404, detail="Файл не найден")
        mime_type, _ = mimetypes.guess_type(task.file_name or "")
        mime_type = mime_type or "application/octet-stream"
        return StreamingResponse(
            BytesIO(task.file_data),
            media_type=mime_type,
            headers={
                "Content-Disposition": f"inline; filename={task.file_name or 'file'}"
            },
        )
    except Exception as e:
        check_handle_exception(e, "Ошибка сервера при получении файла")


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
        check_handle_exception(e, "Ошибка сервера при отзыве доступа к задаче")


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
        check_handle_exception(
            e, "Ошибка сервера при обновлении уровня доступа")


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
                ToDo, User.username.label(
                    "owner_username"), TaskShare.permission_level
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
        check_handle_exception(
            e, "Ошибка сервера при получении расшаренной задачи")


@router.put("/shared-tasks/{task_id}")
def edit_shared_task(
    task_id: int = Path(ge=1),
    task_update: ToDoSchema = Body(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    try:
        task = check_edit_permission(task_id, current_user)

        if task_update.name is not None:
            task.name = task_update.name
        if task_update.text is not None:
            task.text = task_update.text
        if task_update.completion_status is not None:
            task.completion_status = task_update.completion_status

        db.commit()
        db.refresh(task)

        owner = db.query(User).filter(User.id == task.user_id).first()

        return {
            "message": "Расшаренная задача успешно обновлена",
            "id": task.id,
            "task_name": task.name,
            "completion_status": task.completion_status,
            "date_time": task.date_time.strftime("%Y-%m-%d | %H:%M:%S"),
            "text": task.text,
            "owner_username": owner.username if owner else "Неизвестен",
        }

    except Exception as e:
        db.rollback()
        check_handle_exception(
            e, "Ошибка сервера при редактировании расшаренной задачи"
        )


@router.post("/shared-tasks/{task_id}/file")
async def upload_file_to_shared_task(
    uploaded_file: UploadFile = File(),
    task_id: int = Path(ge=1),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict[str, str]:
    try:
        task = check_edit_permission(task_id, current_user)
        MAX_FILE_SIZE = 20 * 1024 * 1024
        file_data = await uploaded_file.read()

        if len(file_data) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="Размер файла превышает максимально допустимый (10MB)",
            )

        task.file_data = file_data
        task.file_name = uploaded_file.filename
        db.commit()
        return {"message": "Файл успешно загружен к расшаренной задаче"}

    except Exception as e:
        db.rollback()
        check_handle_exception(
            e, "Ошибка сервера при загрузке файла к расшаренной задаче"
        )


@router.patch("/shared-tasks/{task_id}")
def toggle_shared_task_status(
    task_id: int = Path(ge=1),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    try:
        task = check_edit_permission(task_id, current_user)

        task.completion_status = not task.completion_status
        db.commit()
        return {
            "message": f"Статус задачи изменен на {'выполнено' if task.completion_status else 'не выполнено'}",
            "task_id": task.id,
            "new_status": task.completion_status,
        }

    except Exception as e:
        db.rollback()
        check_handle_exception(
            e, "Ошибка сервера при изменении статуса задачи")


@router.get("/tasks/{task_id}/collaborators")
def get_task_collaborators_endpoint(
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
        check_handle_exception(
            e, "Ошибка сервера при получении списка соавторов")


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
        check_handle_exception(e, "Ошибка сервера при получении прав доступа")

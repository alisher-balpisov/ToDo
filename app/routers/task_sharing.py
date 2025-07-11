import mimetypes
from io import BytesIO
from typing import List

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import or_

from app.auth.jwt_handler import get_current_active_user
from app.db.models import session, ToDo, User, TaskShare, SharedAccessEnum
from app.db.schemas import TaskShareSchema
from app.routers.crud import validate_sort, SortRule, todo_sort_mapping
from app.routers.handle_exception import get_handle_exception
from app.routers.sharing_helpers import (get_owned_task,
                                         get_existing_user,
                                         get_shared_access)

router = APIRouter(prefix="/tasks/share")


@router.post("/share_task")
def share_task(
        share_data: TaskShareSchema,
        current_user: User = Depends(get_current_active_user)
):
    try:

        get_owned_task(share_data.task_id, current_user)

        shared_with_user = get_existing_user(share_data.shared_with_username)

        if shared_with_user.id == current_user.id:
            raise HTTPException(status_code=400, detail="Нельзя поделиться задачей с самим собой")

        already_shared = session.query(TaskShare).filter(
            TaskShare.task_id == share_data.task_id,
            TaskShare.shared_with_id == shared_with_user.id
        ).first()
        if already_shared:
            raise HTTPException(status_code=400, detail="Доступ уже предоставлен этому пользователю")

        new_share = TaskShare(
            task_id=share_data.task_id,
            owner_id=current_user.id,
            shared_with_id=shared_with_user.id,
            permission_level=share_data.permission_level
        )
        session.add(new_share)
        session.commit()
        return {"message": "Задача успешно расшарена с пользователем"}
    except Exception as e:
        session.rollback()
        get_handle_exception(e, "Ошибка сервера при предоставлении доступа к задаче")


@router.get("/tasks")
def get_shared_tasks(
        sort: List[SortRule] = Depends(validate_sort),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        current_user: User = Depends(get_current_active_user)
):
    try:

        query = (
            session.query(
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
                'id': task.id,
                'task_name': task.name,
                'completion_status': task.completion_status,
                'date_time': task.date_time.strftime("%Y-%m-%d | %H:%M:%S"),
                'text': task.text,
                'owner_username': owner_username,
                'permission_level': permission_level
            } for task, owner_username, permission_level in tasks
        ]
    except Exception as e:
        get_handle_exception(e, "Ошибка сервера при получении расшаренных задач")


@router.get("/task_file")
def get_shared_task_file(id: int, current_user: User = Depends(get_current_active_user)):
    try:
        task = (
            session.query(ToDo)
            .join(TaskShare, TaskShare.task_id == ToDo.id)
            .filter(
                ToDo.id == id,
                or_(ToDo.user_id == current_user.id,
                    TaskShare.shared_with_id == current_user.id)
            ).first()
        )

        if not task or not task.file_data:
            raise HTTPException(status_code=404, detail="Файл не найден")

        mime_type, _ = mimetypes.guess_type(task.file_name or "")
        mime_type = mime_type or "application/octet-stream"

        return StreamingResponse(
            BytesIO(task.file_data),
            media_type=mime_type,
            headers={"Content-Disposition": f"inline; filename={task.file_name or 'file'}"}
        )
    except Exception as e:
        get_handle_exception(e, "Ошибка сервера при получении файла")


@router.delete("/delete")
def unshare_task(
        task_id: int,
        username: str,
        current_user: User = Depends(get_current_active_user)
):
    try:

        get_owned_task(task_id, current_user)

        shared_with_user = get_existing_user(username)

        share = get_shared_access(task_id, current_user, shared_with_user)

        session.delete(share)
        session.commit()

        return {"message": "Доступ к задаче успешно отозван"}
    except Exception as e:
        session.rollback()
        get_handle_exception(e, "Ошибка сервера при отзыве доступа к задаче")


@router.put("/update_permission")
def update_share_permission(
        task_id: int,
        username: str,
        new_permission: SharedAccessEnum,
        current_user: User = Depends(get_current_active_user)
):
    try:

        get_owned_task(task_id, current_user)

        shared_with_user = get_existing_user(username)

        share = get_shared_access(task_id, current_user, shared_with_user)

        share.permission_level = new_permission
        session.commit()

        return {"message": "Уровень доступа успешно обновлен"}
    except Exception as e:
        session.rollback()
        get_handle_exception(e, "Ошибка сервера при обновлении уровня доступа")

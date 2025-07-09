
from fastapi import APIRouter, Depends, Query
from app.auth.jwt_handler import get_current_active_user
from app.db.models import session, ToDo, User, TaskShare
from app.db.schemas import TaskShareSchema
from app.routers.crud import handle_exception, validate_sort, SortRule, todo_sort_mapping
from typing import List



router = APIRouter(prefix="/tasks/share")


def get_owned_task_or_404(task_id: int, current_user: User):
    task = session.query(ToDo).filter(
        ToDo.id == task_id,
        ToDo.user_id == current_user.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена или вам не принадлежит")


def get_existing_user_or_404(username: str) -> User:
    shared_with_user = session.query(User).filter(User.username == username).first()
    if not shared_with_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return shared_with_user


def get_shared_access_or_404(task_id: int, current_user: User, shared_with_user: User) -> TaskShare:
    share = session.query(TaskShare).filter(
        TaskShare.task_id == task_id,
        TaskShare.owner_id == current_user.id,
        TaskShare.shared_with_id == shared_with_user.id
    ).first()
    if not share:
        raise HTTPException(status_code=404, detail="Доступ не найден")
    return share


@router.post("/share_task")
def share_task(
        share_data: TaskShareSchema,
        current_user: User = Depends(get_current_active_user)
):
    try:

        get_owned_task_or_404(share_data.task_id, current_user)

        shared_with_user = get_existing_user_or_404(share_data.shared_with_username)

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
        handle_exception(e, "Ошибка сервера при предоставлении доступа к задаче")


@router.get("/tasks")
def get_shared_tasks(
        sort: List[SortRule] = Depends(validate_sort),
        completion_status: bool = Query(None),
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

        if completion_status is not None:
            query = query.filter(ToDo.completion_status == completion_status)

        order_by = []

        for rule in sort:
            if rule in todo_sort_mapping:
                order_by.append(todo_sort_mapping[rule])

        if completion_status is True:
            order_by.insert(0, ToDo.completion_status.desc())
        elif completion_status is False:
            order_by.insert(0, ToDo.completion_status.asc())

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
        handle_exception(e, "Ошибка сервера при получении расшаренных задач")


from fastapi.responses import StreamingResponse
from fastapi import HTTPException
from io import BytesIO
import mimetypes


@router.get("/task_file")
def get_shared_task_file(id: int, current_user: User = Depends(get_current_active_user)):
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


def unshare_task(
        task_id: int,
        username: str,
        current_user: User = Depends(get_current_active_user)
):
    try:

        get_owned_task_or_404(task_id, current_user)

        shared_with_user = get_existing_user_or_404(username)

        share = get_shared_access_or_404(task_id, current_user, shared_with_user)

        session.delete(share)
        session.commit()

        return {"message": "Доступ к задаче успешно отозван"}
    except Exception as e:
        session.rollback()
        handle_exception(e, "Ошибка сервера при отзыве доступа к задаче")


@router.put("/update_permission")
def update_share_permission(
        task_id: int,
        username: str,
        new_permission: str = Query(pattern='^(view|edit)$'),
        current_user: User = Depends(get_current_active_user)
):
    try:

        get_owned_task_or_404(task_id, current_user)

        shared_with_user = get_existing_user_or_404(username)

        share = get_shared_access_or_404(task_id, current_user, shared_with_user)

        share.permission_level = new_permission
        session.commit()

        return {"message": "Уровень доступа успешно обновлен"}
    except Exception as e:
        session.rollback()
        handle_exception(e, "Ошибка сервера при обновлении уровня доступа")

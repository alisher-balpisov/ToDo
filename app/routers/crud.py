import mimetypes
from datetime import datetime
from io import BytesIO
from typing import List

import pytz
from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.auth.jwt_handler import get_current_active_user
from app.db.models import ToDo, User, session
from app.db.schemas import ToDoSchema
from app.routers.crud_helpers import SortRule, todo_sort_mapping, validate_sort
from app.routers.handle_exception import check_handle_exception

router = APIRouter(prefix="/tasks")


@router.post("/create")
def create_task(
    task: ToDoSchema = Body(), current_user: User = Depends(get_current_active_user)
):
    try:
        new_task = ToDo(
            name=task.name,
            text=task.text,
            completion_status=False,
            date_time=datetime.now(pytz.timezone("Asia/Almaty")),
            user_id=current_user.id,
        )
        session.add(new_task)
        session.commit()
        return {"message": "Задача добавлена"}
    except Exception as e:
        session.rollback()
        check_handle_exception(e, "Ошибка сервера при создании задачи")


@router.post("/upload_file")
async def upload_file(
    uploaded_file: UploadFile = File(),
    todo_id: int = Query(),
    current_user: User = Depends(get_current_active_user),
):
    try:
        file_data = await uploaded_file.read()
        file_name = uploaded_file.filename

        MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB

        if len(file_data) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="Размер файла превышает максимально допустимый (10MB)",
            )

        task = (
            session.query(ToDo)
            .filter(ToDo.id == todo_id, ToDo.user_id == current_user.id)
            .first()
        )
        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        task.file_data = file_data
        task.file_name = file_name
        session.commit()
        return {"message": "Файл успешно загружен"}
    except Exception as e:
        session.rollback()
        check_handle_exception(e, "Ошибка сервера при загрузке файла")


@router.get("/tasks")
def get_tasks(
    sort: List[SortRule] = Depends(validate_sort),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
):
    try:
        tasks_query = session.query(ToDo).filter(ToDo.user_id == current_user.id)

        order_by = []

        for rule in sort:
            if rule in todo_sort_mapping:
                order_by.append(todo_sort_mapping[rule])

        if order_by:
            tasks_query = tasks_query.order_by(*order_by)

        tasks = tasks_query.offset(skip).limit(limit).all()
        return [
            {
                "id": task.id,
                "task_name": task.name,
                "completion_status": task.completion_status,
                "date_time": task.date_time.strftime("%Y-%m-%d | %H:%M:%S"),
                "text": task.text,
                "file_name": task.file_name,
            }
            for task in tasks
        ]
    except Exception as e:
        check_handle_exception(e, "Ошибка сервера при выводе задач")


@router.get("/task_file")
def get_task_file(task_id: int, current_user: User = Depends(get_current_active_user)):
    try:
        task = (
            session.query(ToDo)
            .filter(ToDo.id == task_id, ToDo.user_id == current_user.id)
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


@router.get("/task")
def get_task(
    id: int = Query(ge=1), current_user: User = Depends(get_current_active_user)
):
    try:
        task = (
            session.query(ToDo)
            .filter(ToDo.id == id, ToDo.user_id == current_user.id)
            .first()
        )

        if task is None:
            raise HTTPException(status_code=404, detail="ToDo не существует")

        return {
            "id": task.id,
            "task_name": task.name,
            "completion_status": task.completion_status,
            "date_time": task.date_time.strftime("%Y-%m-%d | %H:%M:%S"),
            "text": task.text,
        }
    except Exception as e:
        check_handle_exception(e, "Ошибка сервера при выводе задачи")


@router.put("/update/by_id")
def update_task_by_id(
    id: int = Query(ge=1),
    task_update: ToDoSchema = Body(),
    current_user: User = Depends(get_current_active_user),
):
    try:
        task = (
            session.query(ToDo)
            .filter(ToDo.id == id, ToDo.user_id == current_user.id)
            .first()
        )
        if task is None:
            raise HTTPException(status_code=404, detail="ToDo не существует")

        task.name = task_update.name if task_update.name else task.name
        task.text = task_update.text if task_update.text else task.text
        task.completion_status = (
            task_update.completion_status
            if task_update.completion_status is not None
            else task.completion_status
        )

        session.commit()
        session.refresh(task)

        return {
            "message": "ToDo изменён",
            "id": task.id,
            "task_name": task.name,
            "completion_status": task.completion_status,
            "date_time": task.date_time.strftime("%Y-%m-%d | %H:%M:%S"),
            "text": task.text,
        }
    except Exception as e:
        session.rollback()
        check_handle_exception(e, "Ошибка сервера при изменении задачи по id")


@router.put("/update/by_name")
def update_task_by_name(
    search_name: str = Query(),
    task_update: ToDoSchema = Body(),
    current_user: User = Depends(get_current_active_user),
):
    try:
        task = (
            session.query(ToDo)
            .filter(ToDo.name == search_name, ToDo.user_id == current_user.id)
            .first()
        )
        if task is None:
            raise HTTPException(status_code=404, detail="ToDo не существует")

        task.name = task_update.name if task_update.name else task.name
        task.text = task_update.text if task_update.text else task.text
        if task_update.completion_status is not None:
            task.completion_status = task_update.completion_status

        session.commit()
        session.refresh(task)
        return {
            "message": "ToDo изменён",
            "id": task.id,
            "task_name": task.name,
            "completion_status": task.completion_status,
            "date_time": task.date_time.strftime("%Y-%m-%d | %H:%M:%S"),
            "text": task.text,
        }
    except Exception as e:
        session.rollback()
        check_handle_exception(e, "Ошибка сервера при изменении задачи по имени")


@router.delete("/delete")
def delete_task(
    id: int = Query(ge=1), current_user: User = Depends(get_current_active_user)
):
    try:
        task = (
            session.query(ToDo)
            .filter(ToDo.id == id, ToDo.user_id == current_user.id)
            .first()
        )

        if task is None:
            raise HTTPException(status_code=404, detail="ToDo не существует")

        session.delete(task)
        session.commit()
        return {"message": "ToDo удалён"}
    except Exception as e:
        session.rollback()
        check_handle_exception(e, "Ошибка сервера при удалении задачи")

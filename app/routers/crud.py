import mimetypes
from datetime import datetime, timezone
from io import BytesIO
from typing import List

from fastapi import (APIRouter, Body, Depends, File, HTTPException, Query,
                     UploadFile, status)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.jwt_handler import get_current_active_user
from app.db.database import get_db
from app.db.models import ToDo, User
from app.db.schemas import ToDoSchema
from app.routers.crud_helpers import SortRule, todo_sort_mapping, validate_sort
from app.routers.handle_exception import check_handle_exception

router = APIRouter(prefix="/tasks")


@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_task(
    task: ToDoSchema = Body(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict[str, str] | None:
    try:
        new_task = ToDo(
            name=task.name,
            text=task.text,
            completion_status=False,
            date_time=datetime.now(timezone.utc).astimezone(),
            user_id=current_user.id,
        )
        db.add(new_task)
        db.commit()
        return {
            "message": "Задача добавлена",
            "task_id": new_task.id,
            "task_name": new_task.name
        }

    except Exception as e:
        db.rollback()
        check_handle_exception(e, "Ошибка сервера при создании задачи")


@router.post("/upload_file")
async def upload_file(
    uploaded_file: UploadFile = File(),
    todo_id: int = Query(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict[str, str] | None:
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
            db.query(ToDo)
            .filter(ToDo.id == todo_id, ToDo.user_id == current_user.id)
            .first()
        )
        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        task.file_data = file_data
        task.file_name = file_name
        db.commit()
        return {"message": "Файл успешно загружен"}

    except Exception as e:
        db.rollback()
        check_handle_exception(e, "Ошибка сервера при загрузке файла")


@router.get("/list")
def get_tasks(
    sort: List[SortRule] = Depends(validate_sort),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> list[dict[str, ToDo | int]] | None:
    try:
        tasks_query = db.query(ToDo).filter(ToDo.user_id == current_user.id)

        order_by = []

        for rule in sort:
            if rule in todo_sort_mapping:
                order_by.append(todo_sort_mapping[rule])

        if order_by:
            tasks_query = tasks_query.order_by(*order_by)

        tasks = tasks_query.offset(skip).limit(limit).all()
        return {
            "tasks": [
                {
                    "id": task.id,
                    "task_name": task.name,
                    "completion_status": task.completion_status,
                    "date_time": task.date_time.isoformat(),  # ISO формат для фронтенда
                    "text": task.text,
                    "file_name": task.file_name,
                }
                for task in tasks
            ],
            "skip": skip,
            "limit": limit
        }

    except Exception as e:
        check_handle_exception(e, "Ошибка сервера при выводе задач")


@router.get("/task_file/{id}")
def get_task_file(
        id: int,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)):
    try:
        task = (
            db.query(ToDo).filter(
                ToDo.id == id,
                ToDo.user_id == current_user.id
            ).first()
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


@router.get("/task/{id}")
def get_task(
    id: int = Query(ge=1), current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict[str, ToDo]:
    try:
        task = (
            db.query(ToDo)
            .filter(ToDo.id == id, ToDo.user_id == current_user.id)
            .first()
        )

        if task is None:
            raise HTTPException(status_code=404, detail="ToDo не существует")
        return {
            "id": task.id,
            "task_name": task.name,
            "completion_status": task.completion_status,
            "date_time": task.date_time.isoformat(),
            "text": task.text,
            "file_name": task.file_name,
        }

    except Exception as e:
        check_handle_exception(e, "Ошибка сервера при получении задачи")


@router.put("/update/by_id/{id}")
def update_task_by_id(
    id: int = Query(ge=1),
    task_update: ToDoSchema = Body(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict[str, ToDo]:
    try:
        task = db.query(ToDo).filter(
            ToDo.id == id,
            ToDo.user_id == current_user.id
        ).first()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Задача не найдена"
            )

        task.name = task_update.name if task_update.name else task.name
        task.text = task_update.text if task_update.text else task.text
        task.completion_status = (
            task_update.completion_status if task_update.completion_status is not None
            else task.completion_status
        )

        db.commit()
        db.refresh(task)
        return {
            "message": "Задача обновлена",
            "id": task.id,
            "task_name": task.name,
            "completion_status": task.completion_status,
            "date_time": task.date_time.isoformat(),
            "text": task.text,
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        check_handle_exception(e, "Ошибка сервера при изменении задачи по id")


@router.put("/update/by_name/{search_name}")
def update_task_by_name(
    search_name: str = Query(),
    task_update: ToDoSchema = Body(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict[str, ToDo | str]:
    try:
        task = db.query(ToDo).filter(
            ToDo.name == search_name,
            ToDo.user_id == current_user.id
        ).first()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Задача не найдена"
            )

        task.name = task_update.name if task_update.name else task.name
        task.text = task_update.text if task_update.text else task.text
        task.completion_status = (
            task_update.completion_status if task_update.completion_status is not None
            else task.completion_status
        )

        db.commit()
        db.refresh(task)
        return {
            "message": "Задача обновлена",
            "id": task.id,
            "task_name": task.name,
            "completion_status": task.completion_status,
            "date_time": task.date_time.isoformat(),
            "text": task.text,
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        check_handle_exception(
            e, "Ошибка сервера при изменении задачи по имени")


@router.delete("/delete/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    id: int = Query(ge=1),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict[str, str]:
    try:
        task = db.query(ToDo).filter(
            ToDo.id == id,
            ToDo.user_id == current_user.id
        ).first()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Задача не найдена"
            )

        db.delete(task)
        db.commit()
        return {"message": "ToDo удалён"}

    except Exception as e:
        db.rollback()
        check_handle_exception(e, "Ошибка сервера при удалении задачи")

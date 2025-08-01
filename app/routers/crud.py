from datetime import datetime, timezone
from typing import Any, List

from fastapi import (APIRouter, Body, Depends, HTTPException, Path,
                     Query, status)
from sqlalchemy.orm import Session

from app.auth.jwt_handler import get_current_active_user
from app.db.database import get_db
from app.db.models import ToDo, User
from app.db.schemas import ToDoSchema
from app.routers.helpers.crud_helpers import SortRule, todo_sort_mapping, validate_sort
from app.handle_exception import handle_server_exception

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
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
        handle_server_exception(e, "Ошибка сервера при создании задачи")


@router.get("/")
def get_tasks(
    sort: List[SortRule] = Depends(validate_sort),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> list[dict[str, Any]]:
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
                    "date_time": task.date_time.isoformat(),
                    "text": task.text,
                    "file_name": task.file_name,
                }
                for task in tasks
            ],
            "skip": skip,
            "limit": limit
        }

    except Exception as e:
        handle_server_exception(e, "Ошибка сервера при выводе задач")


@router.get("/{id}")
def get_task(
    id: int = Path(ge=1),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    try:
        task = (
            db.query(ToDo).filter(
                ToDo.id == id,
                ToDo.user_id == current_user.id
            ).first()
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
        handle_server_exception(e, "Ошибка сервера при получении задачи")


@router.put("/{id}")
def update_task_by_id(
    id: int = Path(ge=1),
    task_update: ToDoSchema = Body(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict[str, Any]:
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
        handle_server_exception(e, "Ошибка сервера при изменении задачи по id")


@router.put("/by_name/{search_name}")
def update_task_by_name(
    search_name: str = Path(max_length=30),
    task_update: ToDoSchema = Body(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict[str, Any]:
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
        handle_server_exception(
            e, "Ошибка сервера при изменении задачи по имени")


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    id: int = Path(ge=1),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> None:
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
        return

    except Exception as e:
        db.rollback()
        handle_server_exception(e, "Ошибка сервера при удалении задачи")

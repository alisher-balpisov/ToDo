from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Path, Query, status

from src.auth.service import CurrentUser
from src.core.database import DbSession, PrimaryKey
from src.core.exceptions import handle_server_exception
from src.db.models import Task
from src.db.schemas import SortTasksValidator, TaskSchema
from src.routers.helpers.crud_helpers import tasks_sort_mapping

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_task(
        session: DbSession,
        current_user: CurrentUser,
        task: TaskSchema,

) -> dict[str, str] | None:
    try:
        new_task = Task(
            name=task.name,
            text=task.text,
            completion_status=False,
            date_time=datetime.now(timezone.utc).astimezone(),
            user_id=current_user.id,
        )
        session.add(new_task)
        session.commit()
        return {
            "msg": "Задача добавлена",
            "task_id": new_task.id,
            "task_name": new_task.name
        }

    except Exception as e:
        session.rollback()
        handle_server_exception(e, "Ошибка сервера при создании задачи")


@router.get("/")
def get_tasks(
        session: DbSession,
        current_user: CurrentUser,
        sort: SortTasksValidator,
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),

) -> list[dict[str, Any]]:
    try:
        tasks_query = session.query(Task).filter(
            Task.user_id == current_user.id)

        order_by = []

        for rule in sort:
            if rule in tasks_sort_mapping:
                order_by.append(tasks_sort_mapping[rule])

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
        session: DbSession,
        current_user: CurrentUser,
        id: PrimaryKey,

) -> dict[str, Any]:
    try:
        task = (
            session.query(Task).filter(
                Task.id == id,
                Task.user_id == current_user.id
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
        session: DbSession,
        current_user: CurrentUser,
        id: PrimaryKey,
        task_update: TaskSchema,

) -> dict[str, Any]:
    try:
        task = session.query(Task).filter(
            Task.id == id,
            Task.user_id == current_user.id
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

        session.commit()
        session.refresh(task)
        return {
            "msg": "Задача обновлена",
            "id": task.id,
            "task_name": task.name,
            "completion_status": task.completion_status,
            "date_time": task.date_time.isoformat(),
            "text": task.text,
        }

    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        handle_server_exception(e, "Ошибка сервера при изменении задачи по id")


@router.put("/by_name/{search_name}")
def update_task_by_name(
        session: DbSession,
        current_user: CurrentUser,
        search_name: Annotated[str, Path(max_length=30)],
        task_update: TaskSchema,

) -> dict[str, Any]:
    try:
        task = session.query(Task).filter(
            Task.name == search_name,
            Task.user_id == current_user.id
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

        session.commit()
        session.refresh(task)
        return {
            "msg": "Задача обновлена",
            "id": task.id,
            "task_name": task.name,
            "completion_status": task.completion_status,
            "date_time": task.date_time.isoformat(),
            "text": task.text,
        }

    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        handle_server_exception(
            e, "Ошибка сервера при изменении задачи по имени")


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
        session: DbSession,
        current_user: CurrentUser,
        id: PrimaryKey,

) -> None:
    try:
        task = session.query(Task).filter(
            Task.id == id,
            Task.user_id == current_user.id
        ).first()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Задача не найдена"
            )

        session.delete(task)
        session.commit()
        return

    except Exception as e:
        session.rollback()
        handle_server_exception(e, "Ошибка сервера при удалении задачи")

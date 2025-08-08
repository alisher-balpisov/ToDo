
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Path, Query, status

from src.auth.service import CurrentUser
from src.core.database import DbSession, PrimaryKey
from src.core.exceptions import handle_server_exception
from src.db.models import Task
from src.db.schemas import SortTasksValidator, TaskSchema
from src.tasks.helpers.crud_helpers import tasks_sort_mapping

from .service import create_task_service, get_tasks_service

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_task(
        session: DbSession,
        current_user: CurrentUser,
        task: TaskSchema,
) -> dict[str, str] | None:
    try:
        new_task = create_task_service(session=session,
                                       current_user_id=current_user.id,
                                       task_name=task.name,
                                       task_text=task.text)
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
        tasks = get_tasks_service(session=session,
                                  current_user_id=current_user.id,
                                  sort=sort.sort_tasks,
                                  skip=skip,
                                  limit=limit)
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
def update_task(
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

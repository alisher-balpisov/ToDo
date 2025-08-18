from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.auth.service import CurrentUser
from src.common.schemas import TaskSchema
from src.core.database import DbSession, PrimaryKey
from src.core.exceptions import handle_server_exception
from src.tasks.helpers import SortTasksRule

from .service import (create_task_service, delete_task_service,
                      get_task_service, get_tasks_service, update_task_service)

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_task(
        session: DbSession,
        current_user: CurrentUser,
        task: TaskSchema,
) -> dict[str, Any] | None:
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
        sort: list[SortTasksRule] = Query(default=[]),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
) -> dict[str, Any]:
    try:
        tasks = get_tasks_service(session=session,
                                  current_user_id=current_user.id,
                                  sort=sort,
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


@router.get("/{task_id}")
def get_task(
        session: DbSession,
        current_user: CurrentUser,
        task_id: PrimaryKey,

) -> dict[str, Any]:
    try:
        task = get_task_service(session=session,
                                current_user_id=current_user.id,
                                task_id=task_id)
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


@router.put("/{task_id}")
def update_task(
        session: DbSession,
        current_user: CurrentUser,
        task_id: PrimaryKey,
        task_update: TaskSchema,
) -> dict[str, Any]:
    try:
        task = update_task_service(session=session,
                                   current_user_id=current_user.id,
                                   task_id=task_id,
                                   name_update=task_update.name,
                                   text_update=task_update.text)
        return {
            "msg": "Задача обновлена",
            "id": task.id,
            "task_name": task.name,
            "completion_status": task.completion_status,
            "date_time": task.date_time.isoformat(),
            "text": task.text,
        }

    except Exception as e:
        session.rollback()
        handle_server_exception(e, "Ошибка сервера при изменении задачи по id")


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
        session: DbSession,
        current_user: CurrentUser,
        task_id: PrimaryKey,
) -> None:
    try:
        delete_task_service(session=session,
                            current_user_id=current_user.id,
                            task_id=task_id)
        return
    except Exception as e:
        session.rollback()
        handle_server_exception(e, "Ошибка сервера при удалении задачи")

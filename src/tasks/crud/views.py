from typing import Any

from fastapi import APIRouter, Query, status

from src.common.schemas import TaskSchema
from src.core.types import CurrentUser, DbSession, PrimaryKey
from src.tasks.helpers import SortTasksRule

from .service import (create_task_service, delete_task_service,
                      get_task_service, get_tasks_service, update_task_service)

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_task(
        session: DbSession,
        current_user: CurrentUser,
        task: TaskSchema,
) -> dict[str, Any] | None:
    new_task = await create_task_service(session=session,
                                         current_user_id=current_user.id,
                                         task_name=task.name,
                                         task_text=task.text)
    return {
        "msg": "Задача добавлена",
        "task_id": new_task.id,
        "task_name": new_task.name
    }


@router.get("/")
async def get_tasks(
        session: DbSession,
        current_user: CurrentUser,
        sort: list[SortTasksRule] = Query(default=[]),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
) -> dict[str, Any]:
    tasks = await get_tasks_service(session=session,
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


@router.get("/{task_id}")
async def get_task(
        session: DbSession,
        current_user: CurrentUser,
        task_id: PrimaryKey,

) -> dict[str, Any]:
    task = await get_task_service(session=session,
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


@router.put("/{task_id}")
async def update_task(
        session: DbSession,
        current_user: CurrentUser,
        task_id: PrimaryKey,
        task_update: TaskSchema,
) -> dict[str, Any]:
    task = await update_task_service(session=session,
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


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
        session: DbSession,
        current_user: CurrentUser,
        task_id: PrimaryKey,
) -> None:
    await delete_task_service(session=session,
                              current_user_id=current_user.id,
                              task_id=task_id)

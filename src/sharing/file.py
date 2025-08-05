import mimetypes
from io import BytesIO
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import or_

from src.auth.service import CurrentUser
from src.core.database import DbSession, PrimaryKey
from src.core.exceptions import handle_server_exception
from src.db.models import Task, TaskShare
from src.routers.helpers.shared_tasks_helpers import check_edit_permission

router = APIRouter()


@router.post("/shared-tasks/{task_id}/file")
async def upload_file_to_shared_task(
        session: DbSession,
        current_user: CurrentUser,
        uploaded_file: Annotated[UploadFile, File()],
        task_id: Annotated[int, PrimaryKey],

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
        session.commit()
        return {"message": "Файл успешно загружен к расшаренной задаче"}

    except Exception as e:
        session.rollback()
        handle_server_exception(
            e, "Ошибка сервера при загрузке файла к расшаренной задаче"
        )


@router.get("/shared-tasks/{task_id}/file")
def get_shared_task_file(
        session: DbSession,
        current_user: CurrentUser,
        task_id: Annotated[int, PrimaryKey],

) -> StreamingResponse:
    try:
        task = (
            session.query(Task)
            .join(TaskShare, TaskShare.task_id == Task.id)
            .filter(
                Task.id == task_id,
                or_(
                    Task.user_id == current_user.id,
                    TaskShare.target_user_id == current_user.id,
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
        handle_server_exception(e, "Ошибка сервера при получении файла")

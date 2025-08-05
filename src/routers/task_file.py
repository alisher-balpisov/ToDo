import mimetypes
from io import BytesIO
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from src.auth.service import CurrentUser
from src.core.database import DbSession, PrimaryKey
from src.core.exceptions import handle_server_exception
from src.db.models import Task

router = APIRouter()


@router.post("/{task_id}/file")
async def upload_file(
        session: DbSession,
        current_user: CurrentUser,
        uploaded_file: Annotated[UploadFile, File()],
        task_id: Annotated[int, PrimaryKey],

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
            session.query(Task).filter(
                Task.id == task_id,
                Task.user_id == current_user.id
            ).first()
        )
        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        task.file_data = file_data
        task.file_name = file_name
        session.commit()
        return {"message": "Файл успешно загружен"}

    except Exception as e:
        session.rollback()
        handle_server_exception(e, "Ошибка сервера при загрузке файла")


@router.get("/{task_id}/file")
def get_task_file(
        session: DbSession,
        current_user: CurrentUser,
        task_id: Annotated[int, PrimaryKey],

) -> StreamingResponse:
    try:
        task = (
            session.query(Task).filter(
                Task.id == task_id,
                Task.user_id == current_user.id
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
        handle_server_exception(e, "Ошибка сервера при получении файла")

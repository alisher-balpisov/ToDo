import mimetypes

from fastapi import HTTPException, UploadFile

from src.common.utils import get_user_task, validate_and_read_file
from src.core.database import PrimaryKey
from src.db.models import Task


def upload_file_to_task_service(
    session,
    current_user_id: int,
    uploaded_file: UploadFile,
    task_id: int
) -> None:
    task = get_user_task(session, current_user_id, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    file_data = validate_and_read_file(uploaded_file)
    task.file_data = file_data
    task.file_name = uploaded_file.filename
    session.commit()


def get_task_file_service(
        session,
        current_user_id: int,
        task_id: int
) -> tuple[Task, str]:
    task = get_user_task(session, current_user_id, task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    if not task.file_data:
        raise HTTPException(status_code=404, detail="Файл не найден")

    mime_type, _ = mimetypes.guess_type(task.file_name or "")

    return task, mime_type or "application/octet-stream"

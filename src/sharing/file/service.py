import mimetypes

from fastapi import HTTPException, UploadFile

from src.core.database import PrimaryKey
from src.db.models import SharedAccessEnum, Task
from src.sharing.service import get_permission_level, get_user_shared_task

MAX_FILE_SIZE_MB = 20
MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024


async def validate_and_read_file(uploaded_file: UploadFile) -> bytes:
    file_data = await uploaded_file.read()
    if len(file_data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Размер файла превышает максимально допустимый (20MB)",
        )
    return file_data


def upload_file_to_shared_task_service(
    session,
    current_user_id: int,
    uploaded_file: UploadFile,
    task_id: PrimaryKey
) -> None:
    task = get_user_shared_task(session, current_user_id, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    if get_permission_level(session, current_user_id, task_id) is not SharedAccessEnum.edit:
        raise HTTPException(
            status_code=403, detail="Нет доступа для редактирования задачи"
        )

    file_data = validate_and_read_file(uploaded_file)
    task.file_data = file_data
    task.file_name = uploaded_file.filename
    session.commit()


def get_shared_task_file_service(
        session,
        current_user_id: int,
        task_id: int
) -> tuple[Task, str]:
    task = get_user_shared_task(session, current_user_id, task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    if not task.file_data:
        raise HTTPException(status_code=404, detail="Файл не найден")

    mime_type, _ = mimetypes.guess_type(task.file_name or "")
    mime_type = mime_type or "application/octet-stream"

    return task, mime_type

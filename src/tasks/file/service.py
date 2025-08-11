import mimetypes

from fastapi import UploadFile

from src.common.models import Task
from src.common.utils import get_user_task, validate_and_read_file
from src.exceptions import FILE_NOT_FOUND, TASK_NOT_FOUND


def upload_file_to_task_service(
    session,
    current_user_id: int,
    uploaded_file: UploadFile,
    task_id: int
) -> None:
    task = get_user_task(session, current_user_id, task_id)
    if not task:
        raise TASK_NOT_FOUND

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
        raise TASK_NOT_FOUND
    if not task.file_data:
        raise FILE_NOT_FOUND

    mime_type, _ = mimetypes.guess_type(task.file_name or "")

    return task, mime_type or "application/octet-stream"

import mimetypes

from fastapi import HTTPException, UploadFile, status

from src.common.models import Task
from src.common.utils import validate_and_read_file
from src.exceptions import FILE_NOT_FOUND, TASK_NOT_FOUND
from src.sharing.models import SharedAccessEnum
from src.sharing.service import get_permission_level, get_user_shared_task


def upload_file_to_shared_task_service(
    session,
    current_user_id: int,
    uploaded_file: UploadFile,
    task_id: int
) -> None:
    task = get_user_shared_task(session, current_user_id, task_id)
    if not task:
        raise TASK_NOT_FOUND

    if get_permission_level(session, current_user_id, task_id) is not SharedAccessEnum.edit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=[{"msg": "Нет доступа для редактирования задачи"}]
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
        raise TASK_NOT_FOUND
    if not task.file_data:
        raise FILE_NOT_FOUND

    mime_type, _ = mimetypes.guess_type(task.file_name or "")

    return task, mime_type or "application/octet-stream"

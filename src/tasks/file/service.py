import mimetypes

from fastapi import UploadFile

from src.common.constants import CONTENT_TYPE_OCTET_STREAM
from src.common.models import Task
from src.common.utils import get_user_task, validate_and_read_file
from src.core.decorators import handler, transactional
from src.core.exception import InvalidInputException, ResourceNotFoundException


@handler
@transactional
async def upload_file_to_task_service(
    session,
    current_user_id: int,
    uploaded_file: UploadFile,
    task_id: int
) -> None:
    task = get_user_task(session, current_user_id, task_id)
    if task is None:
        raise ResourceNotFoundException("Задача", task_id)

    file_data = await validate_and_read_file(uploaded_file)
    task.file_data = file_data
    task.file_name = uploaded_file.filename


@handler
def get_task_file_service(
        session,
        current_user_id: int,
        task_id: int
) -> tuple[Task, str]:
    task = get_user_task(session, current_user_id, task_id)

    if task is None:
        raise ResourceNotFoundException("Задача", task_id)
    if not task.file_data:
        raise InvalidInputException("файл", "пустой файл", "непустой файл")

    mime_type, _ = mimetypes.guess_type(task.file_name or "")

    return task, mime_type or CONTENT_TYPE_OCTET_STREAM

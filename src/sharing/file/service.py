import mimetypes

from fastapi import UploadFile

from src.common.constants import CONTENT_TYPE_OCTET_STREAM
from src.common.models import Task
from src.common.utils import validate_and_read_file
from src.core.decorators import service_method
from src.core.exception import (InsufficientPermissionsException,
                                InvalidInputException,
                                ResourceNotFoundException)
from src.sharing.models import SharedAccessEnum
from src.sharing.service import get_permission_level, get_user_shared_task


@service_method()
async def upload_file_to_shared_task_service(
    session,
    current_user_id: int,
    uploaded_file: UploadFile,
    task_id: int
) -> None:
    task = await get_user_shared_task(session, current_user_id, task_id)
    if task is None:
        raise ResourceNotFoundException("Задача", task_id)

    if await get_permission_level(session, current_user_id, task_id) is not SharedAccessEnum.edit:
        raise InsufficientPermissionsException("редактирование задачи")

    file_data = await validate_and_read_file(uploaded_file)
    task.file_data = file_data
    task.file_name = uploaded_file.filename


@service_method(commit=False)
async def get_shared_task_file_service(
    session,
    current_user_id: int,
    task_id: int
) -> tuple[Task, str]:
    task = await get_user_shared_task(session, current_user_id, task_id)
    if task is None:
        raise ResourceNotFoundException("Задача", task_id)
    if not task.file_data:
        raise InvalidInputException("файл", "пустой файл", "непустой файл")
    mime_type, _ = mimetypes.guess_type(task.file_name or "")

    return task, mime_type or CONTENT_TYPE_OCTET_STREAM

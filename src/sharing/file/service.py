
from fastapi import HTTPException, UploadFile

from src.core.database import PrimaryKey
from src.db.models import SharedAccessEnum
from src.sharing.service import get_permission_level, get_shared_task_for_user

MAX_FILE_SIZE_MB = 20
MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024


async def validate_and_read_file(uploaded_file: UploadFile):
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
    if get_permission_level(session, current_user_id, task_id) is not SharedAccessEnum.edit:
        raise HTTPException(
            status_code=403, detail="Нет доступа для редактирования задачи"
        )
    task = get_shared_task_for_user(session, current_user_id, task_id)

    file_data = validate_and_read_file(uploaded_file)

    task.file_data = file_data
    task.file_name = uploaded_file.filename
    session.commit()

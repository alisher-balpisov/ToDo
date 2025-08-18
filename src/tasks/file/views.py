from io import BytesIO

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from src.auth.service import CurrentUser
from src.core.database import DbSession, PrimaryKey, UploadedFile
from src.core.exceptions import handle_server_exception

from .service import get_task_file_service, upload_file_to_task_service

router = APIRouter()


@router.post("/{task_id}/file")
async def upload_file_to_task(
        session: DbSession,
        current_user: CurrentUser,
        uploaded_file: UploadedFile,
        task_id: PrimaryKey,

):
    try:
        await upload_file_to_task_service(session=session,
                                          current_user_id=current_user.id,
                                          uploaded_file=uploaded_file,
                                          task_id=task_id)
        return {"msg": "Файл успешно загружен"}

    except Exception as e:
        session.rollback()
        handle_server_exception(e, "Ошибка сервера при загрузке файла")


@router.get("/{task_id}/file")
def get_task_file(
        session: DbSession,
        current_user: CurrentUser,
        task_id: PrimaryKey,

) -> StreamingResponse:
    try:
        task, mime_type = get_task_file_service(session=session,
                                                current_user_id=current_user.id,
                                                task_id=task_id)
        return StreamingResponse(
            BytesIO(task.file_data),
            media_type=mime_type,
            headers={
                "Content-Disposition": f"inline; filename={task.file_name or 'file'}"
            }
        )

    except Exception as e:
        handle_server_exception(e, "Ошибка сервера при получении файла")

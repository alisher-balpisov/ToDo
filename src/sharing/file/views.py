from io import BytesIO

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from src.core.types import CurrentUser, DbSession, PrimaryKey, UploadedFile

from .service import (get_shared_task_file_service,
                      upload_file_to_shared_task_service)

router = APIRouter()


@router.post("/shared-tasks/{task_id}/file")
async def upload_file_to_shared_task(
        session: DbSession,
        current_user: CurrentUser,
        uploaded_file: UploadedFile,
        task_id: PrimaryKey,

) -> dict[str, str]:
    await upload_file_to_shared_task_service(session=session,
                                             current_user_id=current_user.id,
                                             uploaded_file=uploaded_file,
                                             task_id=task_id)
    return {"msg": "Файл успешно загружен к расшаренной задаче"}


@router.get("/shared-tasks/{task_id}/file")
async def get_shared_task_file(
        session: DbSession,
        current_user: CurrentUser,
        task_id: PrimaryKey,

) -> StreamingResponse:
    task, mime_type = await get_shared_task_file_service(session=session,
                                                         current_user_id=current_user.id,
                                                         task_id=task_id)
    return StreamingResponse(
        BytesIO(task.file_data),
        media_type=mime_type,
        headers={
            "Content-Disposition": f"inline; filename={task.file_name or 'file'}"
        }
    )

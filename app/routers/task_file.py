import mimetypes
from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, Path, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.jwt_handler import get_current_active_user
from app.db.database import get_db
from app.db.models import ToDo, User
from app.handle_exception import handle_server_exception

router = APIRouter()


@router.post("/{task_id}/file")
async def upload_file(
    uploaded_file: UploadFile = File(),
    task_id: int = Path(ge=1),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
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
            db.query(ToDo).filter(
                ToDo.id == task_id,
                ToDo.user_id == current_user.id
            ).first()
        )
        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        task.file_data = file_data
        task.file_name = file_name
        db.commit()
        return {"message": "Файл успешно загружен"}

    except Exception as e:
        db.rollback()
        handle_server_exception(e, "Ошибка сервера при загрузке файла")


@router.get("/{task_id}/file")
def get_task_file(
        task_id: int = Path(ge=1),
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)) -> StreamingResponse:
    try:
        task = (
            db.query(ToDo).filter(
                ToDo.id == task_id,
                ToDo.user_id == current_user.id
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

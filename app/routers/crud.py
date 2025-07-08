from fastapi import APIRouter, Query, HTTPException, Body, Depends, File, UploadFile
from datetime import datetime
import pytz
from sqlalchemy import or_
from app.db.models import session, ToDo, User
from app.db.schemas import ToDoSchema
from app.auth.jwt_handler import get_current_active_user
from logging import getLogger

router = APIRouter(prefix="/tasks")
logger = getLogger()


def handle_exception(e: Exception, message: str = "Ошибка сервера"):
    logger.exception(message)
    raise HTTPException(
        status_code=500,
        detail=f"{message}: {str(e)}"
    )


@router.post("/create/")
def create_task(task: ToDoSchema = Body(),
                current_user: User = Depends(get_current_active_user)):
    try:
        new_task = ToDo(
            name=task.name,
            text=task.text,
            completion_status=False,
            date_time=datetime.now(pytz.timezone('Asia/Almaty')),
            user_id=current_user.id
        )
        session.add(new_task)
        session.commit()
        return {"message": "Задача добавлена"}
    except Exception as e:
        session.rollback()
        handle_exception(e, "Ошибка сервера при создании задачи")


@router.post("/upload_file")
async def upload_file(uploaded_file: UploadFile = File(),
                      todo_id: int = Query(),
                      current_user: User = Depends(get_current_active_user)):
    try:
        file_data = await uploaded_file.read()
        file_name = uploaded_file.filename
        task = session.query(ToDo).filter(
            ToDo.id == todo_id,
            ToDo.user_id == current_user.id
        ).first()
        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        task.file_data = file_data
        task.file_name = file_name
        session.commit()
        return {"message": "Файл успешно загружен"}
    except Exception as e:
        session.rollback()
        handle_exception(e, "Ошибка сервера при загрузке файла")


from typing import Literal, List

SortRule = Literal['date_desc', 'date_asc', 'name', 'status_false_first', 'status_true_first']

todo_sort_mapping = {
    'date_desc': ToDo.date_time.desc(),
    'date_asc': ToDo.date_time.asc(),
    'name': ToDo.name.asc(),
    'status_false_first': ToDo.completion_status.asc(),
    'status_true_first': ToDo.completion_status.desc()
}


def validate_sort(sort: List[SortRule] = Query(default=['date_desc'])) -> List[SortRule]:
    if 'date_desc' in sort and 'date_asc' in sort:
        raise ValueError("Нельзя использовать одновременно 'date_desc' и 'date_asc'")
    if 'status_false_first' in sort and 'status_true_first' in sort:
        raise ValueError("Нельзя использовать одновременно 'status_false_first' и 'status_true_first'")
    return sort


@router.get("/get/tasks")
def get_tasks(
        sort: List[SortRule] = Depends(validate_sort),
        completion_status: bool = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        current_user: User = Depends(get_current_active_user)
):
    try:
        tasks_query = session.query(ToDo).filter(ToDo.user_id == current_user.id)

        order_by = []

        for rule in sort:
            if rule in todo_sort_mapping:
                order_by.append(todo_sort_mapping[rule])

        if completion_status is True:
            order_by.insert(0, ToDo.completion_status.desc())
        elif completion_status is False:
            order_by.insert(0, ToDo.completion_status.asc())

        print(*order_by)
        if order_by:
            tasks_query = tasks_query.order_by(*order_by)

        tasks = tasks_query.offset(skip).limit(limit).all()
        import base64
        return [
            {
                'id': task.id, 'task_name': task.name,
                'completion_status': task.completion_status,
                'date_time': task.date_time.strftime("%Y-%m-%d | %H:%M:%S"),
                'text': task.text,
                'file_name': task.file_name,
            } for task in tasks
        ]
    except Exception as e:
        handle_exception(e, "Ошибка сервера при выводе задач")


from fastapi.responses import StreamingResponse
from fastapi import HTTPException
from io import BytesIO
import mimetypes


@router.get("/get/file/{task_id}")
def get_task_file(task_id: int, current_user: User = Depends(get_current_active_user)):
    task = session.query(ToDo).filter(
        ToDo.id == task_id, ToDo.user_id == current_user.id
    ).first()

    if not task or not task.file_data:
        raise HTTPException(status_code=404, detail="Файл не найден")

    # Определяем MIME-тип по имени файла
    mime_type, _ = mimetypes.guess_type(task.file_name or "")
    mime_type = mime_type or "application/octet-stream"

    return StreamingResponse(
        BytesIO(task.file_data),
        media_type=mime_type,
        headers={"Content-Disposition": f"inline; filename={task.file_name or 'file'}"}
    )


@router.get("/get/task")
def get_task(id: int = Query(ge=1), current_user: User = Depends(get_current_active_user)):
    try:
        task = session.query(ToDo).filter(
            ToDo.id == id,
            ToDo.user_id == current_user.id
        ).first()
        if task is None:
            raise HTTPException(status_code=404, detail="ToDo не существует")
        return {
            'id': task.id, 'task_name': task.name,
            'completion_status': task.completion_status,
            'date_time': task.date_time.strftime("%Y-%m-%d | %H:%M:%S"),
            'text': task.text
        }
    except Exception as e:
        handle_exception(e, "Ошибка сервера при выводе задачи")


@router.get("/search/")
def search_tasks(search_query: str, current_user: User = Depends(get_current_active_user)):
    try:
        tasks = session.query(ToDo).filter(
            or_(
                ToDo.name.ilike(f"%{search_query}%"),
                ToDo.text.ilike(f"%{search_query}%")
            )
        ).filter(ToDo.user_id == current_user.id).all()
        return [
            {
                'id': task.id, 'task_name': task.name,
                'completion_status': task.completion_status,
                'date_time': task.date_time.strftime("%Y-%m-%d | %H:%M:%S"),
                'text': task.text
            } for task in tasks
        ]
    except Exception as e:
        handle_exception(e, "Ошибка сервера при поиске задачи")


@router.put("/update/by_id")
def update_task_by_id(
        id: int = Query(ge=1),
        completion_status: bool = Query(None),
        task_update: ToDoSchema = Body(),
        current_user: User = Depends(get_current_active_user)
):
    try:
        task = session.query(ToDo).filter(
            ToDo.id == id,
            ToDo.user_id == current_user.id
        ).first()
        if task is None:
            raise HTTPException(status_code=404, detail="ToDo не существует")

        task.name = task_update.name
        task.text = task_update.text
        if completion_status is not None:
            task.completion_status = completion_status

        session.commit()
        session.refresh(task)

        return {
            'message': 'ToDo изменён',
            'id': task.id,
            'task_name': task.name,
            'completion_status': task.completion_status,
            'date_time': task.date_time.strftime("%Y-%m-%d | %H:%M:%S"),
            'text': task.text
        }
    except Exception as e:
        session.rollback()
        handle_exception(e, "Ошибка сервера при изменении задачи по id")


@router.put("/update/by_name")
def update_task_by_name(
        search_name: str = Query(),
        completion_status: bool = Query(None),
        task_update: ToDoSchema = Body(),
        current_user: User = Depends(get_current_active_user)
):
    try:
        task = session.query(ToDo).filter(
            ToDo.name == search_name,
            ToDo.user_id == current_user.id
        ).first()
        if task is None:
            raise HTTPException(status_code=404, detail="ToDo не существует")

        task.name = task_update.name
        task.text = task_update.text
        if completion_status is not None:
            task.completion_status = completion_status

        session.commit()
        session.refresh(task)

        return {
            'message': 'ToDo изменён',
            'id': task.id,
            'task_name': task.name,
            'completion_status': task.completion_status,
            'date_time': task.date_time.strftime("%Y-%m-%d | %H:%M:%S"),
            'text': task.text
        }
    except Exception as e:
        session.rollback()
        handle_exception(e, "Ошибка сервера при изменении задачи по имени")


@router.delete("/delete")
def delete_task(id: int = Query(ge=1), current_user: User = Depends(get_current_active_user)):  # удаление по id
    try:
        task = session.query(ToDo).filter(
            ToDo.id == id,
            ToDo.user_id == current_user.id
        ).first()
        if task is None:
            raise HTTPException(status_code=404, detail="ToDo не существует")
        session.delete(task)
        session.commit()
        return {"message": "ToDo удалён"}
    except Exception as e:
        session.rollback()
        handle_exception(e, "Ошибка сервера при удалении задачи")


@router.get("/stats")
def get_tasks_stats(current_user: User = Depends(get_current_active_user)):
    try:
        query = session.query(ToDo).filter(ToDo.user_id == current_user.id)

        total = query.count()
        completed = query.filter(ToDo.completion_status == True).count()
        uncompleted = query.filter(ToDo.completion_status == False).count()
        completion_percentage = round((completed / total) * 100 if total > 0 else 0, 2)
        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "uncompleted_tasks": uncompleted,
            "completion_percentage": completion_percentage
        }
    except Exception as e:
        handle_exception(e, "Ошибка сервера при выводе статистики")






@router.get("/share")
def share_task_user_to_user(user_id: int = Query(), task_id: int = Query()):



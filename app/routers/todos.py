from fastapi import APIRouter, Query, HTTPException, Body, Depends
from datetime import datetime
import pytz
from sqlalchemy import or_
from app.db.models import session, ToDo, User
from app.db.schemas import ToDoSchema
from app.auth.jwt_handler import get_current_active_user

router = APIRouter(prefix="/tasks")


@router.post("/create/")
def create_task(task: ToDoSchema = Body(), current_user: User = Depends(get_current_active_user)):
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
        raise HTTPException(status_code=500, detail=str(e))


from typing import Literal

SortRule = Literal['date_desc', 'date_asc', 'name', 'status_false_first', 'status_true_first']


@router.get("/get/tasks")
def get_tasks(
        sort: list[SortRule] = Query(default=['date_desc']),
        current_user: User = Depends(get_current_active_user),
        completion_status: bool = Query(None)
):
    order_by_clauses = []

    for rule in sort:
        if rule == 'date_desc':
            order_by_clauses.append(ToDo.date_time.desc())
        elif rule == 'date_asc':
            order_by_clauses.append(ToDo.date_time.asc())
        elif rule == 'name':
            order_by_clauses.append(ToDo.name.asc())
        elif rule == 'status_false_first':
            order_by_clauses.append(ToDo.completion_status.asc())
        elif rule == 'status_true_first':
            order_by_clauses.append(ToDo.completion_status.desc())

    tasks_query = session.query(ToDo).filter(ToDo.user_id == current_user.id)

    if completion_status is not None:
        tasks_query = tasks_query.filter(ToDo.completion_status == completion_status)

    if order_by_clauses:
        tasks_query = tasks_query.order_by(*order_by_clauses)

    tasks = tasks_query.all()
    return [
        {
            'id': task.id, 'task_name': task.name,
            'completion_status': task.completion_status,
            'date_time': task.date_time.strftime("%Y-%m-%d | %H:%M:%S"),
            'text': task.text
        } for task in tasks]


@router.get("/get/task")
def get_task(id: int = Query(ge=1)):
    task = session.query(ToDo).filter(ToDo.id == id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="ToDo не существует")
    return {
        'id': task.id, 'task_name': task.name,
        'completion_status': str(task.completion_status),
        'date_time': task.date_time,
        'text': task.text
    }


@router.get("/search/")
def search_tasks(search_query: str):
    tasks = session.query(ToDo).filter(
        or_(
            ToDo.name.ilike(f"%{search_query}%"),
            ToDo.text.ilike(f"%{search_query}%")
        )
    ).all()
    return [
        {
            'id': task.id, 'task_name': task.name,
            'completion_status': str(task.completion_status),
            'date_time': task.date_time.strftime("%Y-%m-%d | %H:%M:%S"),
            'text': task.text
        } for task in tasks]


@router.put("/update/by_id")
def update_task_by_id(
        id: int = Query(ge=1),
        completion_status: bool = Query(None),
        task_update: ToDoSchema = Body()
):
    task = session.query(ToDo).filter(ToDo.id == id).first()
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


@router.put("/update/by_name")
def update_task_by_name(
        search_name: str = Query(),
        completion_status: bool = Query(None),
        task_update: ToDoSchema = Body()
):
    task = session.query(ToDo).filter(ToDo.name == search_name).first()
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


@router.delete("/delete")
def delete_task(id: int = Query(ge=1)):  # удаление по id
    task = session.query(ToDo).filter(ToDo.id == id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="ToDo не существует")
    session.delete(task)
    session.commit()
    return {"message": "ToDo удалён"}

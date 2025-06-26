from fastapi import FastAPI, Query, HTTPException, Body
from sqlalchemy import (create_engine, Column, Integer,
                        String, Boolean, DateTime, or_)
from sqlalchemy.orm import sessionmaker, declarative_base
from pydantic import BaseModel, Field
from datetime import datetime
import pytz

DATABASE_URL = 'postgresql://localhost:5432/base_db'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()


class ToDoSchema(BaseModel):
    name: str = Field(max_length=20)
    text: str = Field(max_length=4096)


class ToDo(Base):
    __tablename__ = "ToDo"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    text = Column(String)
    completion_status = Column(Boolean)
    date_time = Column(DateTime)


Base.metadata.create_all(engine)

app = FastAPI()


@app.post("/tasks/")
def create_task(task: ToDoSchema = Body()):
    new_task = ToDo(
        name=task.name,
        text=task.text,
        completion_status=False,
        date_time=datetime.now(pytz.timezone('Asia/Almaty'))
    )
    session.add(new_task)
    session.commit()
    return {"message": "Задача добавлена"}


@app.get("/tasks/get/tasks")
def get_tasks(sort: list[str] = Query(default=['date_desc'], enum=[
    'date_desc', 'date_asc', 'name',
    'status_false_first', 'status_true_first'
]),
              completion_status: bool = Query(None)):
    tasks_query = session.query(ToDo)

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

    tasks_query = session.query(ToDo)

    if completion_status is not None:
        tasks_query = tasks_query.filter(ToDo.completion_status == completion_status)

    if order_by_clauses:
        tasks_query = tasks_query.order_by(*order_by_clauses)

    tasks = tasks_query.all()
    return tasks


@app.get("/tasks/get/task")
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


@app.get("/tasks/search/")
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


@app.put("/tasks/update/by_id")
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


@app.put("/tasks/update/by_name")
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


@app.delete("/tasks/")
def delete_task(id: int = Query(ge=1)):  # удаление по id
    task = session.query(ToDo).filter(ToDo.id == id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="ToDo не существует")
    session.delete(task)
    session.commit()
    return {"message": "ToDo удалён"}

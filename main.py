from fastapi import FastAPI, Query, HTTPException, Body
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from pydantic import BaseModel, Field
from datetime import datetime
import pytz

DATABASE_URL = 'postgresql://postgres:200614@localhost:5432/alish'
engine = create_engine(DATABASE_URL)

Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()


class ToDoModel(BaseModel):
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
def create_task(task: ToDoModel = Query()):
    new_task = ToDo(
        name=task.name,
        text=task.text,
        completion_status=False,
        date_time=datetime.now(pytz.timezone('Asia/Almaty')).strftime('%Y-%m-%d  %H:%M:%S')
    )
    session.add(new_task)
    session.commit()
    return {"message": "Задача добавлена"}


@app.get("/tasks/get/tasks")
def get_tasks(sort: str = Query('date_time_descending',
                                enum=['date_time_descending', 'date_time_ascending', 'name',
                                      'completion_status_by_False', 'completion_status_by_True'])):
    if sort == 'date_time_descending':
        tasks = session.query(ToDo).order_by(ToDo.date_time.desc()).all()
    elif sort == 'date_time_ascending':
        tasks = session.query(ToDo).order_by(ToDo.date_time.asc()).all()
    elif sort == 'name':
        tasks = session.query(ToDo).order_by(ToDo.name).all()
    elif sort == 'completion_status_by_False':
        tasks = session.query(ToDo).order_by(ToDo.completion_status.asc()).all()
    elif sort == 'completion_status_by_True':
        tasks = session.query(ToDo).order_by(ToDo.completion_status.desc()).all()

    return [{'id': task.id, 'task_name': task.name,
             'completion_status': str(task.completion_status),
             'date_time': task.date_time.strftime("%Y-%m-%d | %H:%M:%S"),
             'task': task.text} for task in tasks]


@app.get("/tasks/get/task")
def get_task(id: int = Query(ge=1)):
    task = session.query(ToDo).filter(ToDo.id == id).first()
    return {'id': task.id, 'task_name': task.name,
            'completion_status': str(task.completion_status),
            'date_time': task.date_time,
            'text': task.text}


@app.put("/tasks/update/by_id")
def update_task_by_id(
        id: int = Query(None, ge=1),
        completion_status: bool = Query(enum=[False, True]),
        task_temp: ToDoModel = Body()
):
    task = session.query(ToDo).filter(ToDo.id == id).first()
    if not task:
        raise HTTPException(status_code=404, detail="ToDo не существует")
    task.text = task_temp.text
    if completion_status is not None:
        task.completion_status = completion_status
    if task_temp.name is not None:
        task.name = task_temp.name
    session.commit()
    session.refresh(task)
    return {'id': task.id, 'task_name': task.name,
            'completion_status': str(task.completion_status),
            'date_time': task.date_time,
            'text': task.text}


@app.put("/tasks/update/by_name")
def update_task_by_name(
        name: str = Query(),
        completion_status: bool = Query(None),
        update_task: ToDoModel = Body()
):
    task = session.query(ToDo).filter(ToDo.name == name).first()
    if not task:
        raise HTTPException(status_code=404, detail="ToDo не существует")
    task.text = update_task.text
    if completion_status is not None:
        task.completion_status = completion_status
    if update_task.name is not None:
        task.name = update_task.name
    session.commit()
    session.refresh(task)
    return {'id': task.id, 'task_name': task.name,
            'completion_status': str(task.completion_status),
            'date_time': task.date_time,
            'text': task.text}


@app.delete("/tasks/")
def delete_task(id: int = Query(ge=1, le=session.query(ToDo).count())):  # удаление по id
    task = session.query(ToDo).filter(ToDo.id == id).first()
    session.delete(task)
    session.commit()
    return {f"ToDo с id {id} удалён"}

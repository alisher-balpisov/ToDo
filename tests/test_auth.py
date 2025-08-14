import pytest
from sqlalchemy import or_

from src.auth.models import ToDoUser
from src.auth.service import get_current_user
from src.tasks.crud.service import *

from .conftest import get_user

task_name = "My Task"
task_text = "My text"


def test_create_task(client, db, headers, token):

    # test endpoint
    payload = {
        "name": f"{task_name}",
        "text": f"{task_text}"
    }
    resp = client.post("/tasks", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["msg"] == "Задача добавлена"
    assert isinstance(data["task_id"], int)

    # test service
    user = get_user(db, token)
    new_task = create_task_service(session=db,
                                   current_user_id=user.id,
                                   task_name=task_name,
                                   task_text=task_text)
    assert isinstance(new_task, Task)
    assert new_task.id is not None
    assert new_task.name == task_name
    assert new_task.text == task_text
    assert new_task.completion_status is False
    assert new_task.user_id == user.id
    assert isinstance(new_task.date_time, datetime)

    tasks = db.query(Task).filter(
        or_(
            Task.id == new_task.id,
            Task.id == data["task_id"]
        )).all()
    assert len(tasks) == 2
    end_task, service_task = tasks
    assert end_task is not None and service_task is not None
    assert end_task.name == task_name


def test_get_tasks(client, db, headers, token):
    # test endpoint
    params = {
        "sort_raw": ["date_asc"],
        "skip": 0,
        "limit": 100
    }
    resp = client.get("/tasks", params=params, headers=headers)
    data = resp.json()
    tasks = data["tasks"]
    for i in range(0, len(data["tasks"])):
        assert tasks[i]["task_name"] == task_name
        assert tasks[i]["text"] == task_text
        assert tasks[i]["completion_status"] == False
        assert tasks[i]["file_name"] == None
    assert data["skip"] == params["skip"]
    assert data["limit"] == params["limit"]


def test_get_task(client, db, headers, token):
    task_count = db.query(Task).count()
    print(task_count)
    for task_id in range(1, task_count + 1):
        resp = client.get("/tasks", params={"task_id": task_id}, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        print(data)

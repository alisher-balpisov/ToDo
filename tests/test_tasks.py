def test_create_task(auth_clients):
    client1, _ = auth_clients
    response = client1.post(
        "/tasks/",
        json={"name": "Test Task", "text": "Test task description"},
    )
    assert response.status_code == 201
    assert response.json()["msg"] == "Задача добавлена"
    assert "task_id" in response.json()
    assert response.json()["task_name"] == "Test Task"

def test_get_tasks(auth_clients):
    client1, _ = auth_clients
    response = client1.get("/tasks/?sort=asc")
    assert response.status_code == 200
    assert "tasks" in response.json()
    assert isinstance(response.json()["tasks"], list)

def test_get_task(auth_clients):
    client1, _ = auth_clients
    create_response = client1.post(
        "/tasks/",
        json={"name": "Another Task", "text": "Another task description"},
    )
    task_id = create_response.json()["task_id"]
    response = client1.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["id"] == task_id
    assert response.json()["task_name"] == "Another Task"

def test_update_task(auth_clients):
    client1, _ = auth_clients
    create_response = client1.post(
        "/tasks/",
        json={"name": "Task to Update", "text": "Initial description"},
    )
    task_id = create_response.json()["task_id"]
    response = client1.put(
        f"/tasks/{task_id}",
        json={"name": "Updated Task", "text": "Updated description"},
    )
    assert response.status_code == 200
    assert response.json()["msg"] == "Задача обновлена"
    assert response.json()["task_name"] == "Updated Task"

def test_delete_task(auth_clients):
    client1, _ = auth_clients
    create_response = client1.post(
        "/tasks/",
        json={"name": "Task to Delete", "text": "Description"},
    )
    task_id = create_response.json()["task_id"]
    response = client1.delete(f"/tasks/{task_id}")
    assert response.status_code == 204

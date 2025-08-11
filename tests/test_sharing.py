def test_share_task(auth_clients):
    client1, client2 = auth_clients
    create_response = client1.post(
        "/tasks/",
        json={"name": "Task to Share", "text": "Sharing description"},
    )
    task_id = create_response.json()["task_id"]
    
    response = client1.post(
        f"/sharing/tasks/{task_id}/shares",
        json={"target_username": "testuser2", "permission_level": "view"},
    )
    assert response.status_code == 200
    assert response.json()["msg"] == "Задача успешно расшарена с пользователем"

def test_unshare_task(auth_clients):
    client1, client2 = auth_clients
    create_response = client1.post(
        "/tasks/",
        json={"name": "Task to Unshare", "text": "Unsharing description"},
    )
    task_id = create_response.json()["task_id"]
    
    client1.post(
        f"/sharing/tasks/{task_id}/shares",
        json={"target_username": "testuser2", "permission_level": "view"},
    )
    
    response = client1.delete(f"/sharing/tasks/{task_id}/shares/testuser2")
    assert response.status_code == 200
    assert response.json()["msg"] == "Доступ к задаче успешно отозван"

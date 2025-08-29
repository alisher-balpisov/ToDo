import pytest


@pytest.mark.integration
class TestCompleteWorkflows:
    """End-to-end тесты, проверяющие полные пользовательские сценарии от начала до конца."""

    async def test_full_user_and_task_management_workflow_succeeds(self, client):
        """Тестирует полный сценарий: регистрация, вход, создание, обновление и получение статистики задач."""
        # --- 1. Регистрация нового пользователя ---
        # Arrange
        user_data = {"username": "workflowuser", "password": "Password123"}

        # Act
        reg_response = await client.post("/register", json=user_data)

        # Assert
        assert reg_response.status_code == 200

        # --- 2. Вход в систему ---
        # Act
        login_response = await client.post("/login", data=user_data)

        # Assert
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # --- 3. Создание задачи ---
        # Arrange
        task_data = {"name": "My First Task", "text": "This is my first task"}

        # Act
        create_response = await client.post(
            "/tasks/", json=task_data, headers=headers)

        # Assert
        assert create_response.status_code == 201
        task_id = create_response.json()["task_id"]

        # --- 4. Получение списка задач ---
        # Act
        list_response = await client.get("/tasks/", headers=headers)

        # Assert
        assert list_response.status_code == 200
        assert len(list_response.json()["tasks"]) == 1

        # --- 5. Обновление задачи ---
        # Arrange
        update_data = {"name": "Updated Task Name",
                       "text": "Updated task description"}

        # Act
        update_response = await client.put(
            f"/tasks/{task_id}", json=update_data, headers=headers)

        # Assert
        assert update_response.status_code == 200

        # --- 6. Переключение статуса выполнения ---
        # Act
        toggle_response = await client.patch(f"/tasks/{task_id}", headers=headers)

        # Assert
        assert toggle_response.status_code == 200
        assert toggle_response.json()["new_status"] is True

        # --- 7. Получение статистики ---
        # Act
        stats_response = await client.get("/stats", headers=headers)

        # Assert
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert stats["total_tasks"] == 1
        assert stats["completed_tasks"] == 1
        assert stats["completion_percentage"] == 100.0

    async def test_full_task_sharing_and_collaboration_workflow_succeeds(self, client):
        """Тестирует полный сценарий: создание задачи, предоставление доступа, редактирование и отзыв доступа."""
        # --- 1. Создание и вход для двух пользователей ---
        # Arrange
        owner_data = {"username": "owner", "password": "Password123"}
        collab_data = {"username": "collaborator", "password": "Password123"}

        # Act & Assert
        await client.post("/register", json=owner_data)
        owner_login = await client.post("/login", data=owner_data)
        owner_headers = {
            "Authorization": f"Bearer {owner_login.json()['access_token']}"}

        await client.post("/register", json=collab_data)
        collab_login = await client.post("/login", data=collab_data)
        collab_headers = {
            "Authorization": f"Bearer {collab_login.json()['access_token']}"}

        # --- 2. Владелец создает задачу ---
        # Arrange
        task_data = {"name": "Shared Task", "text": "Task to be shared"}

        # Act
        create_response = await client.post(
            "/tasks/", json=task_data, headers=owner_headers)

        # Assert
        assert create_response.status_code == 201
        task_id = create_response.json()["task_id"]

        # --- 3. Владелец предоставляет доступ коллаборатору ---
        # Arrange
        share_data = {"target_username": "collaborator",
                      "permission_level": "edit"}

        # Act
        share_response = await client.post(
            f"/sharing/tasks/{task_id}/shares", json=share_data, headers=owner_headers)

        # Assert
        assert share_response.status_code == 200

        # --- 4. Коллаборатор видит расшаренную задачу ---
        # Act
        list_shared_response = await client.get(
            "/sharing/shared-tasks", headers=collab_headers)

        # Assert
        assert list_shared_response.status_code == 200
        assert len(list_shared_response.json()) == 1

        # --- 5. Коллаборатор редактирует задачу ---
        # Arrange
        update_data = {"name": "Updated by Collaborator",
                       "text": "Modified text"}

        # Act
        update_response = await client.put(
            f"/sharing/shared-tasks/{task_id}", json=update_data, headers=collab_headers)

        # Assert
        assert update_response.status_code == 200

        # --- 6. Владелец видит изменения ---
        # Act
        verify_response = await client.get(
            f"/tasks/{task_id}", headers=owner_headers)

        # Assert
        assert verify_response.status_code == 200
        assert verify_response.json()["task_name"] == "Updated by Collaborator"

        # --- 7. Владелец отзывает доступ ---
        # Act
        unshare_response = await client.delete(
            f"/sharing/tasks/{task_id}/shares/collaborator", headers=owner_headers)

        # Assert
        assert unshare_response.status_code == 200

        # --- 8. Коллаборатор больше не может получить доступ к задаче ---
        # Act
        response = await client.get(
            f"/sharing/shared-tasks/{task_id}", headers=collab_headers
        )
        data = response.json()

        # Assert
        assert response.status_code == 404
        assert data["error_code"] == "RESOURCE_NOT_FOUND"

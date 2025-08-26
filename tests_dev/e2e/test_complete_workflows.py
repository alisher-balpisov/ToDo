import pytest

from src.core.exception import ResourceNotFoundException


class TestCompleteWorkflows:
    """End-to-end тесты полных пользовательских сценариев."""

    def test_user_registration_and_task_management_workflow(self, client):
        """Полный сценарий: регистрация, создание задач, управление."""

        user_data = {
            "username": "workflowuser",
            "password": "Password123"
        }

        # 1. Регистрация
        response = client.post("/register", json=user_data)
        assert response.status_code == 200

        # 2. Вход в систему
        response = client.post("/login", data=user_data)
        assert response.status_code == 200

        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Создание задачи
        task_data = {
            "name": "My First Task",
            "text": "This is my first task"
        }

        response = client.post("/tasks/", json=task_data, headers=headers)
        assert response.status_code == 201

        task_id = response.json()["task_id"]

        # 4. Получение списка задач
        response = client.get("/tasks/", headers=headers)
        assert response.status_code == 200
        assert len(response.json()["tasks"]) == 1

        # 5. Обновление задачи
        update_data = {
            "name": "Updated Task Name",
            "text": "Updated task description"
        }

        response = client.put(
            f"/tasks/{task_id}", json=update_data, headers=headers)
        assert response.status_code == 200

        # 6. Переключение статуса выполнения
        response = client.patch(f"/tasks/{task_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["new_status"] is True

        # 7. Получение статистики
        response = client.get("/stats", headers=headers)
        assert response.status_code == 200

        stats = response.json()
        assert stats["total_tasks"] == 1
        assert stats["completed_tasks"] == 1
        assert stats["completion_percentage"] == 100.0

    def test_task_sharing_workflow(self, client, db_session):
        """Полный сценарий совместного доступа к задачам."""
        # Создаем двух пользователей
        users_data = [
            {"username": "owner", "password": "Password123"},
            {"username": "collaborator", "password": "Password123"}
        ]

        tokens = []
        for user_data in users_data:
            # Регистрация
            response = client.post("/register", json=user_data)
            assert response.status_code == 200

            # Вход
            response = client.post("/login", data=user_data)
            assert response.status_code == 200
            tokens.append(response.json()["access_token"])

        owner_headers = {"Authorization": f"Bearer {tokens[0]}"}
        collab_headers = {"Authorization": f"Bearer {tokens[1]}"}

        # Владелец создает задачу
        task_data = {"name": "Shared Task", "text": "Task to be shared"}
        response = client.post("/tasks/", json=task_data,
                               headers=owner_headers)
        assert response.status_code == 201
        task_id = response.json()["task_id"]

        # Владелец предоставляет доступ коллаборатору
        share_data = {
            "target_username": "collaborator",
            "permission_level": "edit"
        }
        response = client.post(
            f"/sharing/tasks/{task_id}/shares",
            json=share_data,
            headers=owner_headers
        )
        assert response.status_code == 200

        # Коллаборатор видит расшаренную задачу
        response = client.get("/sharing/shared-tasks", headers=collab_headers)
        assert response.status_code == 200
        assert len(response.json()) == 1

        # Коллаборатор редактирует задачу
        update_data = {"name": "Updated by Collaborator",
                       "text": "Modified text"}
        response = client.put(
            f"/sharing/shared-tasks/{task_id}",
            json=update_data,
            headers=collab_headers
        )
        assert response.status_code == 200

        # Владелец видит изменения
        response = client.get(f"/tasks/{task_id}", headers=owner_headers)
        assert response.status_code == 200
        assert response.json()["task_name"] == "Updated by Collaborator"

        # Владелец отзывает доступ
        response = client.delete(
            f"/sharing/tasks/{task_id}/shares/collaborator",
            headers=owner_headers
        )
        assert response.status_code == 200

        # Коллаборатор больше не видит задачу
        with pytest.raises(Exception) as exc_info:
            client.get("/sharing/shared-tasks", headers=collab_headers)

        assert ResourceNotFoundException("Список", "данные") == exc_info.value

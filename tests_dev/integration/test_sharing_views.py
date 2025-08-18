class TestSharingEndpoints:
    """Интеграционные тесты совместного доступа."""

    def test_share_task(self, client, auth_headers, test_task, test_user2):
        """Тест предоставления доступа к задаче."""
        share_data = {
            "target_username": test_user2.username,
            "permission_level": "view"
        }

        response = client.post(
            f"/sharing/tasks/{test_task.id}/shares",
            json=share_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "успешно расшарена" in data["msg"]

    def test_get_shared_tasks(self, client, auth_headers2, shared_task):
        """Тест получения расшаренных задач."""
        response = client.get("/sharing/shared-tasks", headers=auth_headers2)

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(task["id"] == shared_task.id for task in data)

    def test_get_shared_task_details(self, client, auth_headers2, shared_task):
        """Тест получения деталей расшаренной задачи."""
        response = client.get(
            f"/sharing/shared-tasks/{shared_task.id}", headers=auth_headers2)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == shared_task.id
        assert data["task_name"] == shared_task.name
        assert "owner_username" in data
        assert "permission_level" in data

    def test_update_shared_task_with_edit_permission(self, client, auth_headers2, shared_task):
        """Тест редактирования расшаренной задачи с правами edit."""
        update_data = {
            "name": "Updated Shared Task",
            "text": "Updated by collaborator"
        }

        response = client.put(
            f"/sharing/shared-tasks/{shared_task.id}",
            json=update_data,
            headers=auth_headers2
        )

        assert response.status_code == 200
        data = response.json()
        assert data["task_name"] == "Updated Shared Task"

    def test_update_share_permission(self, client, auth_headers, shared_task, test_user2):
        """Тест изменения уровня доступа."""
        response = client.put(
            f"/sharing/tasks/{shared_task.id}/shares/{test_user2.username}?new_permission=view",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "успешно обновлен" in data["msg"]

    def test_unshare_task(self, client, auth_headers, shared_task, test_user2):
        """Тест отзыва доступа к задаче."""
        response = client.delete(
            f"/sharing/tasks/{shared_task.id}/shares/{test_user2.username}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "успешно отозван" in data["msg"]

    def test_get_task_collaborators(self, client, auth_headers, shared_task):
        """Тест получения списка соавторов задачи."""
        response = client.get(
            f"/sharing/tasks/{shared_task.id}/collaborators", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "collaborators" in data
        assert data["total_collaborators"] >= 2  # Владелец + один коллаборатор

    def test_get_task_permissions(self, client, auth_headers2, shared_task):
        """Тест получения прав доступа к задаче."""
        response = client.get(
            f"/sharing/shared-tasks/{shared_task.id}/permissions", headers=auth_headers2)

        assert response.status_code == 200
        data = response.json()
        assert "permissions" in data
        assert data["permissions"]["can_view"] is True
        # Так как у нас edit permission
        assert data["permissions"]["can_edit"] is True

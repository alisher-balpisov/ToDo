import pytest

pytestmark = pytest.mark.asyncio


@pytest.mark.integration
class TestSharingEndpoints:
    """Интеграционные тесты для эндпоинтов совместного доступа к задачам."""

    async def test_share_task_with_valid_user_succeeds(self, client, auth_headers, test_task, test_user2):
        """Тест успешного предоставления доступа к задаче другому пользователю."""
        # Arrange
        share_data = {
            "target_username": test_user2.username,
            "permission_level": "view"
        }

        # Act
        response = await client.post(
            f"/sharing/tasks/{test_task.id}/shares",
            json=share_data,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        assert "успешно расшарена" in response.json()["msg"]

    async def test_get_shared_tasks_for_collaborator_succeeds(self, client, auth_headers2, shared_task):
        """Тест получения списка задач, расшаренных для текущего пользователя."""
        # Arrange (shared_task fixture already shared a task with user2)

        # Act
        response = await client.get("/sharing/shared-tasks", headers=auth_headers2)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(task["id"] == shared_task.id for task in data)

    async def test_get_shared_task_details_by_collaborator_succeeds(self, client, auth_headers2, shared_task):
        """Тест получения деталей конкретной расшаренной задачи."""
        # Arrange (shared_task fixture)

        # Act
        response = await client.get(
            f"/sharing/shared-tasks/{shared_task.id}", headers=auth_headers2)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == shared_task.id
        assert data["task_name"] == shared_task.name
        assert "owner_username" in data
        assert "permission_level" in data

    async def test_update_shared_task_with_edit_permission_succeeds(self, client, auth_headers2, shared_task):
        """Тест редактирования расшаренной задачи пользователем с правами 'edit'."""
        # Arrange (shared_task fixture grants 'edit' permission)
        update_data = {
            "name": "Updated Shared Task",
            "text": "Updated by collaborator"
        }

        # Act
        response = await client.put(
            f"/sharing/shared-tasks/{shared_task.id}",
            json=update_data,
            headers=auth_headers2
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["task_name"] == "Updated Shared Task"
        assert data["text"] == "Updated by collaborator"

    async def test_update_share_permission_by_owner_succeeds(self, client, auth_headers, shared_task, test_user2):
        """Тест изменения владельцем уровня доступа для соавтора."""
        # Arrange
        target_username = test_user2.username
        new_permission = "view"

        # Act
        response = await client.put(
            f"/sharing/tasks/{shared_task.id}/shares/{target_username}?new_permission={new_permission}",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        assert "успешно обновлен" in response.json()["msg"]

    async def test_unshare_task_by_owner_succeeds(self, client, auth_headers, shared_task, test_user2):
        """Тест успешного отзыва владельцем доступа к задаче."""
        # Arrange
        target_username = test_user2.username

        # Act
        response = await client.delete(
            f"/sharing/tasks/{shared_task.id}/shares/{target_username}",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        assert "успешно отозван" in response.json()["msg"]

    async def test_get_task_collaborators_by_owner_succeeds(self, client, auth_headers, shared_task):
        """Тест получения владельцем списка соавторов задачи."""
        # Arrange (shared_task fixture)

        # Act
        response = await client.get(
            f"/sharing/tasks/{shared_task.id}/collaborators", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "collaborators" in data
        assert data["total_collaborators"] >= 1

    async def test_get_task_permissions_by_collaborator_succeeds(self, client, auth_headers2, shared_task):
        """Тест получения соавтором своих прав доступа к задаче."""
        # Arrange (shared_task fixture)

        # Act
        response = await client.get(
            f"/sharing/shared-tasks/{shared_task.id}/permissions", headers=auth_headers2)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "permissions" in data
        assert data["permissions"]["can_view"] is True
        # Based on shared_task fixture
        assert data["permissions"]["can_edit"] is True

import pytest
from sqlalchemy import delete

from src.common.models import Task
from src.core.exception import (MissingRequiredFieldException,
                                ResourceNotFoundException)

pytestmark = pytest.mark.asyncio


@pytest.mark.integration
class TestTaskEndpoints:
    """Интеграционные тесты для эндпоинтов управления задачами."""

    async def test_create_task_with_valid_data_succeeds(self, client, auth_headers):
        """Тест успешного создания задачи с валидными данными."""
        # Arrange
        task_data = {
            "name": "New Task",
            "text": "Task description"
        }

        # Act
        response = await client.post("/tasks/", json=task_data, headers=auth_headers)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["task_name"] == "New Task"
        assert "task_id" in data
        assert data["msg"] == "Задача добавлена"

    async def test_create_task_without_name_raises_missing_field(self, client, auth_headers):
        """Тест создания задачи без названия должен вызвать исключение."""
        # Arrange
        task_data = {"text": "Task description"}

        # Act & Assert
        with pytest.raises(MissingRequiredFieldException) as exc_info:
            await client.post("/tasks/", json=task_data, headers=auth_headers)

        assert exc_info.value.error_code == "MISSING_REQUIRED_FIELD"
        assert "имя задачи" in str(exc_info.value)

    async def test_get_tasks_without_pagination_returns_all_tasks(self, client, auth_headers, test_task):
        """Тест получения списка всех задач пользователя."""
        # Arrange (test_task fixture)

        # Act
        response = await client.get("/tasks/", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert len(data["tasks"]) >= 1
        assert any(t["task_name"] == test_task.name for t in data["tasks"])

    async def test_get_tasks_with_pagination_returns_correct_slice(self, client, auth_headers, db_session, test_user):
        """Тест получения задач с пагинацией должен вернуть корректный срез данных."""
        # Arrange
        from src.tasks.crud.service import create_task_service
        for i in range(5):
            await create_task_service(db_session, test_user.id,
                                      f"Task {i}", f"Desc {i}")

        # Act
        response = await client.get("/tasks/?skip=2&limit=2", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 2
        assert data["skip"] == 2
        assert data["limit"] == 2

    async def test_get_task_by_id_for_existing_task_succeeds(self, client, auth_headers, test_task):
        """Тест успешного получения задачи по её ID."""
        # Arrange
        task_id = test_task.id

        # Act
        response = await client.get(f"/tasks/{task_id}", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["task_name"] == test_task.name

    async def test_get_task_by_id_for_nonexistent_task_raises_not_found(self, client, auth_headers):
        """Тест получения несуществующей задачи по ID должен вызвать исключение."""
        # Arrange
        task_id = 9999

        # Act & Assert
        with pytest.raises(ResourceNotFoundException) as exc_info:
            await client.get(f"/tasks/{task_id}", headers=auth_headers)

        assert exc_info.value.error_code == "RESOURCE_NOT_FOUND"
        assert exc_info.value.resource_type == "Задача"
        assert exc_info.value.resource_id == str(task_id)

    async def test_update_task_with_valid_data_succeeds(self, client, auth_headers, test_task):
        """Тест успешного обновления данных задачи."""
        # Arrange
        update_data = {"name": "Updated Task", "text": "Updated description"}
        task_id = test_task.id

        # Act
        response = await client.put(
            f"/tasks/{task_id}", json=update_data, headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["task_name"] == "Updated Task"
        assert data["text"] == "Updated description"

    async def test_delete_task_with_valid_id_succeeds(self, client, auth_headers, test_task):
        """Тест успешного удаления существующей задачи."""
        # Arrange
        task_id = test_task.id

        # Act
        response = await client.delete(f"/tasks/{task_id}", headers=auth_headers)

        # Assert
        assert response.status_code == 204

    async def test_toggle_task_completion_status_succeeds(self, client, auth_headers, test_task):
        """Тест успешного переключения статуса выполнения задачи."""
        # Arrange
        original_status = test_task.completion_status
        task_id = test_task.id

        # Act
        response = await client.patch(f"/tasks/{task_id}", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["new_status"] is not original_status

    async def test_search_tasks_with_matching_query_returns_results(self, client, auth_headers, test_task):
        """Тест поиска задач по существующему ключевому слову."""
        # Arrange
        query = test_task.name

        # Act
        response = await client.get(
            f"/search?search_query={query}", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(task["task_name"] == test_task.name for task in data)

    async def test_get_tasks_stats_returns_correct_statistics(self, client, auth_headers, db_session, test_user):
        """Тест получения корректной статистики по задачам пользователя."""
        # Arrange
        from src.tasks.crud.service import create_task_service

        # Ensure a clean state for stats
        await db_session.execute(delete(Task).filter(Task.user_id == test_user.id))
        await db_session.commit()

        task1 = await create_task_service(
            db_session, test_user.id, "Completed Task", "")
        await create_task_service(db_session, test_user.id, "Uncompleted Task", "")

        # Mark one as completed
        task1.completion_status = True
        await db_session.commit()

        # Act
        response = await client.get("/stats", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_tasks"] == 2
        assert data["completed_tasks"] == 1
        assert data["uncompleted_tasks"] == 1
        assert data["completion_percentage"] == 50.0

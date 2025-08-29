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

    async def test_create_task_without_name_returns_400(self, client, auth_headers):
        """Тест создания задачи без названия должен вернуть 400 Bad Request."""
        # Arrange
        task_data = {"text": "Task description"}

        # Act
        response = await client.post("/tasks/", json=task_data, headers=auth_headers)
        data = response.json()

        # Assert
        assert response.status_code == 400
        assert data["error_code"] == "MISSING_REQUIRED_FIELD"
        assert "имя задачи" in data["detail"]["missing_fields"]

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

    async def test_get_task_by_id_for_nonexistent_task_returns_404(self, client, auth_headers):
        """Тест получения несуществующей задачи по ID должен вернуть 404 Not Found."""
        # Arrange
        task_id = 9999

        # Act
        response = await client.get(f"/tasks/{task_id}", headers=auth_headers)
        data = response.json()

        # Assert
        assert response.status_code == 404
        assert data["error_code"] == "RESOURCE_NOT_FOUND"
        assert data["detail"]["resource_type"] == "Задача"
        assert data["detail"]["resource_id"] == str(task_id)

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
        from src.tasks.crud.service import create_task_service
        await db_session.execute(delete(Task).where(Task.user_id == test_user.id))
        await db_session.commit()

        task1 = await create_task_service(
            session=db_session,
            current_user_id=test_user.id,
            task_name="Completed Task",
            task_text=""
        )
        await create_task_service(
            session=db_session,
            current_user_id=test_user.id,
            task_name="Uncompleted Task",
            task_text=""
        )

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

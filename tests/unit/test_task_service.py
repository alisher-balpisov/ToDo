from datetime import datetime

import pytest

from src.core.exception import (MissingRequiredFieldException,
                                ResourceNotFoundException)
from src.tasks.crud.service import (create_task_service, delete_task_service,
                                    get_task_service, get_tasks_service,
                                    update_task_service)


@pytest.mark.unit
class TestTaskService:
    """Юнит-тесты для сервисного слоя управления задачами."""

    async def test_create_task_with_valid_data_succeeds(self, db_session, test_user):
        """Тест успешного создания задачи с корректными данными."""
        # Arrange
        task_name = "New Test Task"
        task_text = "Test description"

        # Act
        task = await create_task_service(
            session=db_session,
            current_user_id=test_user.id,
            task_name=task_name,
            task_text=task_text
        )

        # Assert
        assert task.name == task_name
        assert task.text == task_text
        assert task.user_id == test_user.id
        assert task.completion_status is False
        assert isinstance(task.date_time, datetime)

    @pytest.mark.parametrize("name", ["", None])
    async def test_create_task_with_empty_or_none_name_raises_missing_field(self, db_session, test_user, name):
        """Тест создания задачи с пустым или None названием должен вызвать исключение."""
        # Arrange (name from parametrize)

        # Act & Assert
        with pytest.raises(MissingRequiredFieldException) as exc_info:
            await create_task_service(
                session=db_session,
                current_user_id=test_user.id,
                task_name=name,
                task_text="Test description"
            )
        assert exc_info.value.error_code == "MISSING_REQUIRED_FIELD"
        assert "имя задачи" in exc_info.value.missing_fields

    async def test_get_tasks_service_returns_user_tasks(self, db_session, test_user):
        """Тест получения списка задач должен вернуть все задачи пользователя."""
        for i in range(3):
            await create_task_service(
                session=db_session,
                current_user_id=test_user.id,
                task_name=f"Task {i}",
                task_text="")

        tasks = await get_tasks_service(
            session=db_session,
            current_user_id=test_user.id,
            sort=[], skip=0, limit=100)

        assert len(tasks) == 3
        assert all(task.user_id == test_user.id for task in tasks)

    async def test_get_task_service_for_existing_task_returns_task(self, db_session, test_user, test_task):
        """Тест получения существующей задачи по ID должен вернуть объект задачи."""
        # Arrange
        task_id = test_task.id

        # Act
        task = await get_task_service(session=db_session,
                                      current_user_id=test_user.id,
                                      task_id=task_id)

        # Assert
        assert task is not None
        assert task.id == task_id
        assert task.name == test_task.name

    async def test_get_task_service_for_nonexistent_task_raises_not_found(self, db_session, test_user):
        """Тест получения несуществующей задачи по ID должен вызвать исключение."""
        # Arrange
        task_id = 9999

        # Act & Assert
        with pytest.raises(ResourceNotFoundException) as exc_info:
            await get_task_service(db_session, test_user.id, task_id)
        assert exc_info.value.error_code == "RESOURCE_NOT_FOUND"
        assert exc_info.value.resource_type == "Задача"
        assert exc_info.value.resource_id == str(task_id)

    async def test_get_task_service_for_other_user_task_raises_not_found(self, db_session, test_user2, test_task):
        """Тест получения задачи другого пользователя должен вызвать исключение."""
        # Arrange
        task_id = test_task.id  # Belongs to test_user

        # Act & Assert
        with pytest.raises(ResourceNotFoundException) as exc_info:
            await get_task_service(db_session, test_user2.id, task_id)
        assert exc_info.value.error_code == "RESOURCE_NOT_FOUND"
        assert exc_info.value.resource_id == str(task_id)

    async def test_update_task_service_with_valid_data_succeeds(self, db_session, test_user, test_task):
        """Тест успешного обновления данных существующей задачи."""
        # Arrange
        update_data = {"name": "Updated Task", "text": "Updated description"}

        # Act
        updated_task = await update_task_service(
            session=db_session, current_user_id=test_user.id, task_id=test_task.id,
            name_update=update_data["name"], text_update=update_data["text"]
        )

        # Assert
        assert updated_task.name == update_data["name"]
        assert updated_task.text == update_data["text"]

    async def test_delete_task_service_for_existing_task_succeeds(self, db_session, test_user, test_task):
        """Тест успешного удаления существующей задачи."""
        # Arrange
        task_id = test_task.id

        # Act
        await delete_task_service(db_session, test_user.id, task_id)

        # Assert
        with pytest.raises(ResourceNotFoundException):
            await get_task_service(db_session, test_user.id, task_id)

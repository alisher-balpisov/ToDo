from datetime import datetime

import pytest

from src.core.exception import (MissingRequiredFieldException,
                                ResourceNotFoundException)
from src.tasks.crud.service import (create_task_service, delete_task_service,
                                    get_task_service, get_tasks_service,
                                    update_task_service)


class TestTaskService:
    """Тесты сервиса управления задачами."""

    def test_create_task_success(self, db_session, test_user):
        """Тест успешного создания задачи."""
        task = create_task_service(
            session=db_session,
            current_user_id=test_user.id,
            task_name="Test Task",
            task_text="Test description"
        )

        assert task.name == "Test Task"
        assert task.text == "Test description"
        assert task.user_id == test_user.id
        assert task.completion_status is False
        assert isinstance(task.date_time, datetime)

    @pytest.mark.parametrize("task_name, expected_exception", [
        ("", MissingRequiredFieldException("имя задачи")),
        (None, MissingRequiredFieldException("имя задачи"))
    ])
    def test_create_task_without_name(self, db_session, test_user, task_name, expected_exception):
        """Тест создания задачи без названия."""
        with pytest.raises(Exception) as exc_info:
            create_task_service(
                session=db_session,
                current_user_id=test_user.id,
                task_name=task_name,
                task_text="Test description"
            )

        assert expected_exception == exc_info.value

    def test_create_task_with_none_name(self, db_session, test_user):
        """Тест создания задачи с None в названии."""
        with pytest.raises(MissingRequiredFieldException, match="Отсутствует обязательное поле 'имя задачи'") as exc_info:
            create_task_service(
                session=db_session,
                current_user_id=test_user.id,
                task_name=None,
                task_text="Test description"
            )

    def test_get_tasks_service(self, db_session, test_user):
        """Тест получения списка задач."""
        # Создаем несколько задач
        for i in range(3):
            create_task_service(
                session=db_session,
                current_user_id=test_user.id,
                task_name=f"Task {i}",
                task_text=f"Description {i}"
            )

        tasks = get_tasks_service(
            session=db_session,
            current_user_id=test_user.id,
            sort=[],
            skip=0,
            limit=10
        )

        assert len(tasks) == 3
        assert all(task.user_id == test_user.id for task in tasks)

    def test_get_tasks_with_pagination(self, db_session, test_user):
        """Тест получения задач с пагинацией."""
        # Создаем 5 задач
        for i in range(5):
            create_task_service(
                session=db_session,
                current_user_id=test_user.id,
                task_name=f"Task {i}",
                task_text=f"Description {i}"
            )

        # Получаем только 2 задачи, пропуская первую
        tasks = get_tasks_service(
            session=db_session,
            current_user_id=test_user.id,
            sort=[],
            skip=1,
            limit=2
        )

        assert len(tasks) == 2

    def test_get_task_service_found(self, db_session, test_user, test_task):
        """Тест получения существующей задачи."""
        task = get_task_service(
            session=db_session,
            current_user_id=test_user.id,
            task_id=test_task.id
        )

        assert task.id == test_task.id
        assert task.name == test_task.name

    def test_get_task_service_not_found(self, db_session, test_user):
        """Тест получения несуществующей задачи."""
        task_id = 999
        with pytest.raises(Exception) as exc_info:
            get_task_service(
                session=db_session,
                current_user_id=test_user.id,
                task_id=task_id
            )

        assert isinstance(exc_info.value, ResourceNotFoundException)

    def test_get_task_service_other_user(self, db_session, test_user2, test_task):
        """Тест получения задачи другого пользователя."""
        with pytest.raises(Exception) as exc_info:
            get_task_service(
                session=db_session,
                current_user_id=test_user2.id,
                task_id=test_task.id
            )

        assert isinstance(exc_info.value, ResourceNotFoundException)

    def test_update_task_service_success(self, db_session, test_user, test_task):
        """Тест успешного обновления задачи."""
        updated_task = update_task_service(
            session=db_session,
            current_user_id=test_user.id,
            task_id=test_task.id,
            name_update="Updated Task",
            text_update="Updated description"
        )

        assert updated_task.name == "Updated Task"
        assert updated_task.text == "Updated description"

    def test_update_task_partial(self, db_session, test_user, test_task):
        """Тест частичного обновления задачи."""
        original_text = test_task.text

        updated_task = update_task_service(
            session=db_session,
            current_user_id=test_user.id,
            task_id=test_task.id,
            name_update="Updated Task",
            text_update=None
        )

        assert updated_task.name == "Updated Task"
        assert updated_task.text == original_text

    def test_delete_task_service_success(self, db_session, test_user, test_task):
        """Тест успешного удаления задачи."""
        task_id = test_task.id

        delete_task_service(
            session=db_session,
            current_user_id=test_user.id,
            task_id=task_id
        )

        # Проверяем, что задача удалена
        with pytest.raises(Exception) as exc_info:
            get_task_service(
                session=db_session,
                current_user_id=test_user.id,
                task_id=task_id
            )

        assert isinstance(exc_info.value, ResourceNotFoundException)

    def test_delete_task_not_found(self, db_session, test_user):
        """Тест удаления несуществующей задачи."""
        task_id = 999
        with pytest.raises(Exception) as exc_info:
            delete_task_service(
                session=db_session,
                current_user_id=test_user.id,
                task_id=task_id
            )

        assert isinstance(exc_info.value, ResourceNotFoundException)

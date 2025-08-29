import pytest

from src.core.exception import (InvalidOperationException,
                                ResourceAlreadyExistsException,
                                ResourceNotFoundException)
from src.sharing.models import SharedAccessEnum
from src.sharing.service import (get_permission_level, get_user_shared_task,
                                 is_already_shared, is_sharing_with_self)
from src.sharing.share.service import share_task_service


@pytest.mark.unit
class TestSharingService:
    """Юнит-тесты для сервисного слоя совместного доступа."""

    def test_is_sharing_with_self_with_same_ids_returns_true(self):
        """Тест проверки шаринга с самим собой при одинаковых ID."""
        # Arrange
        owner_id, target_id = 1, 1
        # Act & Assert
        assert is_sharing_with_self(owner_id, target_id) is True

    def test_is_sharing_with_self_with_different_ids_returns_false(self):
        """Тест проверки шаринга с самим собой при разных ID."""
        # Arrange
        owner_id, target_id = 1, 2
        # Act & Assert
        assert is_sharing_with_self(owner_id, target_id) is False

    def test_is_already_shared_for_unshared_task_returns_false(self, db_session, test_task, test_user2):
        """Тест проверки, что задача еще не расшарена, должен вернуть False."""
        # Arrange (unshared task)
        # Act
        result = is_already_shared(db_session, test_user2.id, test_task.id)
        # Assert
        assert result is False

    def test_is_already_shared_for_shared_task_returns_true(self, db_session, shared_task, test_user2):
        """Тест проверки, что задача уже расшарена, должен вернуть True."""
        # Arrange (shared_task fixture)
        # Act
        result = is_already_shared(db_session, test_user2.id, shared_task.id)
        # Assert
        assert result is True

    def test_share_task_service_with_valid_data_succeeds(self, db_session, test_user, test_user2, test_task):
        """Тест успешного предоставления доступа к задаче."""
        # Arrange (valid users and task)

        # Act
        share_task_service(
            session=db_session,
            owner_id=test_user.id,
            task_id=test_task.id,
            target_username=test_user2.username,
            permission_level=SharedAccessEnum.view
        )
        shared_task_check = get_user_shared_task(
            db_session, test_user2.id, test_task.id)

        # Assert
        assert shared_task_check is not None
        assert shared_task_check.id == test_task.id

    def test_share_task_service_to_nonexistent_user_raises_not_found(self, db_session, test_user, test_task):
        """Тест шаринга несуществующему пользователю должен вызвать исключение."""
        # Arrange
        target_username = "nonexistent"

        # Act & Assert
        with pytest.raises(ResourceNotFoundException) as exc_info:
            share_task_service(
                session=db_session, owner_id=test_user.id, task_id=test_task.id,
                target_username=target_username, permission_level=SharedAccessEnum.view
            )
        assert exc_info.value.error_code == "RESOURCE_NOT_FOUND"
        assert exc_info.value.resource_type == "Пользователь"
        assert exc_info.value.resource_id == target_username

    def test_share_task_service_for_already_shared_task_raises_already_exists(self, db_session, test_user, test_user2, shared_task):
        """Тест повторного шаринга уже расшаренной задачи должен вызвать исключение."""
        # Arrange (shared_task fixture)

        # Act & Assert
        with pytest.raises(ResourceAlreadyExistsException) as exc_info:
            share_task_service(
                session=db_session, owner_id=test_user.id, task_id=shared_task.id,
                target_username=test_user2.username, permission_level=SharedAccessEnum.view
            )
        assert exc_info.value.error_code == "RESOURCE_ALREADY_EXISTS"
        assert exc_info.value.resource_type == "Доступ к задаче"

    def test_share_task_with_self_raises_invalid_operation(self, db_session, test_user, test_task):
        """Тест предоставления доступа самому себе должен вызвать исключение."""
        # Arrange (sharing to self)

        # Act & Assert
        with pytest.raises(InvalidOperationException) as exc_info:
            share_task_service(
                session=db_session, owner_id=test_user.id, task_id=test_task.id,
                target_username=test_user.username, permission_level=SharedAccessEnum.view
            )
        assert exc_info.value.error_code == "INVALID_OPERATION"
        assert "с самим собой" in exc_info.value.reason

    def test_get_permission_level_returns_correct_level(self, db_session, test_user2, shared_task):
        """Тест получения уровня разрешений для расшаренной задачи."""
        # Arrange (shared_task has 'edit' permission for test_user2)

        # Act
        permission = get_permission_level(
            db_session, test_user2.id, shared_task.id)

        # Assert
        assert permission == SharedAccessEnum.edit

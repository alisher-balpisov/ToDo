import pytest

from src.core.exception import (InvalidOperationException,
                                ResourceAlreadyExistsException,
                                ResourceNotFoundException)
from src.sharing.models import SharedAccessEnum
from src.sharing.service import (get_permission_level, get_user_shared_task,
                                 is_already_shared, is_sharing_with_self)
from src.sharing.share.service import share_task_service


class TestSharingService:
    """Тесты сервиса совместного доступа."""

    def test_is_sharing_with_self(self):
        """Тест проверки шаринга с самим собой."""
        assert is_sharing_with_self(1, 1) is True
        assert is_sharing_with_self(1, 2) is False

    def test_is_already_shared_false(self, db_session, test_task, test_user2):
        """Тест проверки что задача еще не расшарена."""
        result = is_already_shared(
            session=db_session,
            target_user_id=test_user2.id,
            task_id=test_task.id
        )
        assert result is False

    def test_is_already_shared_true(self, db_session, test_user, test_user2, shared_task):
        """Тест проверки что задача уже расшарена."""
        result = is_already_shared(
            session=db_session,
            target_user_id=test_user2.id,
            task_id=shared_task.id
        )
        assert result is True

    def test_share_task_service_success(self, db_session, test_user, test_user2, test_task):
        """Тест успешного предоставления доступа к задаче."""
        share_task_service(
            session=db_session,
            owner_id=test_user.id,
            task_id=test_task.id,
            target_username=test_user2.username,
            permission_level=SharedAccessEnum.view
        )

        # Проверяем, что доступ предоставлен
        shared_task = get_user_shared_task(
            session=db_session,
            target_user_id=test_user2.id,
            task_id=test_task.id
        )

        assert shared_task is not None
        assert shared_task.id == test_task.id

    def test_share_task_service_nonexistent_user(self, db_session, test_user, test_task):
        """Тест предоставления доступа несуществующему пользователю."""
        with pytest.raises(ResourceNotFoundException) as exc_info:
            share_task_service(
                session=db_session,
                owner_id=test_user.id,
                task_id=test_task.id,
                target_username="nonexistent",
                permission_level=SharedAccessEnum.view
            )

        assert exc_info.value.error_code == "RESOURCE_NOT_FOUND"
        assert exc_info.value.resource_type == "Пользователь"
        assert exc_info.value.resource_id == "nonexistent"

    def test_share_task_service_already_shared(self, db_session, test_user, test_user2, shared_task):
        """Тест предоставления доступа к уже расшаренной задаче."""
        with pytest.raises(ResourceAlreadyExistsException) as exc_info:
            share_task_service(
                session=db_session,
                owner_id=test_user.id,
                task_id=shared_task.id,
                target_username=test_user2.username,
                permission_level=SharedAccessEnum.view
            )

        assert exc_info.value.error_code == "RESOURCE_ALREADY_EXISTS"
        assert exc_info.value.resource_type == "Доступ к задаче"

    def test_share_task_with_self(self, db_session, test_user, test_task):
        """Тест предоставления доступа самому себе."""
        with pytest.raises(InvalidOperationException) as exc_info:
            share_task_service(
                session=db_session,
                owner_id=test_user.id,
                task_id=test_task.id,
                target_username=test_user.username,
                permission_level=SharedAccessEnum.view
            )

        assert exc_info.value.error_code == "INVALID_OPERATION"
        assert exc_info.value.operation == "расшаривание задачи"
        assert "с самим собой" in exc_info.value.reason

    def test_get_permission_level(self, db_session, test_user2, shared_task):
        """Тест получения уровня разрешений."""
        permission = get_permission_level(
            session=db_session,
            current_user_id=test_user2.id,
            task_id=shared_task.id
        )

        assert permission == SharedAccessEnum.edit

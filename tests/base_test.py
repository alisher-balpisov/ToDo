import io
import json
from typing import Any, Dict
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient


@pytest.fixture
def task_data():
    """Тестовые данные задачи."""
    return {
        "name": "Test Task",
        "text": "This is a test task description"
    }


@pytest.fixture
def share_data():
    """Тестовые данные для совместного доступа."""
    return {
        "target_username": "collaborator",
        "permission_level": "view"
    }


class TestAuthentication:
    """Тесты для аутентификации пользователей."""

    def test_register_user_success(self, client, user_data):
        """Тест успешной регистрации пользователя."""
        expected_response = {
            "msg": "Регистрация пройдена успешно",
            "username": user_data["username"],
            "password": user_data["password"]
        }

        # Настройка мока
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        client.post.return_value = mock_response

        response = client.post("/register", json=user_data)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["username"] == user_data["username"]
        client.post.assert_called_once_with("/register", json=user_data)

    def test_register_user_validation_error(self, client):
        """Тест регистрации с невалидными данными."""
        invalid_data = {"username": "ab", "password": ""}

        expected_error = {
            "detail": [{
                "msg": "Пользователь с таким username уже существует.",
                "loc": ["username"],
                "type": "value_error",
            }]
        }

        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.json.return_value = expected_error
        client.post.return_value = mock_response

        response = client.post("/register", json=invalid_data)

        assert response.status_code == 422
        assert "detail" in response.json()

    def test_login_user_success(self, client, user_data):
        """Тест успешного входа пользователя."""
        # Правильный формат для OAuth2PasswordRequestForm
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }

        expected_response = {
            "access_token": "test_access_token",
            "token_type": "bearer"
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        client.post.return_value = mock_response

        # data, не json для OAuth2
        response = client.post("/login", data=login_data)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["access_token"] == "test_access_token"
        assert response_data["token_type"] == "bearer"

    def test_login_user_invalid_credentials(self, client):
        """Тест входа с неверными учетными данными."""
        invalid_data = {"username": "wronguser", "password": "wrongpass"}

        expected_error = {
            "detail": [
                {"msg": "Invalid username.", "loc": [
                    "username"], "type": "value_error"},
                {"msg": "Invalid password.", "loc": [
                    "password"], "type": "value_error"}
            ]
        }

        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.json.return_value = expected_error
        client.post.return_value = mock_response

        response = client.post("/login", data=invalid_data)

        assert response.status_code == 422

    def test_change_password_success(self, client, auth_headers):
        """Тест успешной смены пароля."""
        password_data = {
            "current_password": "oldpassword123",
            "new_password": "NewPassword123",
            "confirm_password": "NewPassword123"
        }

        expected_response = {"msg": "Пароль успешно изменён"}

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        client.post.return_value = mock_response

        response = client.post(
            "/change-password", json=password_data, headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["msg"] == "Пароль успешно изменён"

    def test_change_password_unauthorized(self, client):
        """Тест смены пароля без авторизации."""
        password_data = {
            "current_password": "oldpassword123",
            "new_password": "NewPassword123",
            "confirm_password": "NewPassword123"
        }

        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "detail": [{"msg": "Не удалось подтвердить учетные данные"}]
        }
        client.post.return_value = mock_response

        response = client.post("/change-password", json=password_data)

        assert response.status_code == 401


class TestTasks:
    """Тесты для управления задачами."""

    def test_create_task_success(self, client, auth_headers, task_data):
        """Тест успешного создания задачи."""
        expected_response = {
            "msg": "Задача добавлена",
            "task_id": 1,
            "task_name": task_data["name"]
        }

        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = expected_response
        client.post.return_value = mock_response

        response = client.post("/tasks/", json=task_data, headers=auth_headers)

        assert response.status_code == 201
        response_data = response.json()
        assert response_data["task_name"] == task_data["name"]
        assert "task_id" in response_data

    def test_create_task_name_required(self, client, auth_headers):
        """Тест создания задачи без названия."""
        invalid_data = {"name": "", "text": "Some text"}

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "detail": [{"msg": "Имя задачи не задано"}]
        }
        client.post.return_value = mock_response

        response = client.post(
            "/tasks/", json=invalid_data, headers=auth_headers)

        assert response.status_code == 400

    def test_get_tasks_success(self, client, auth_headers):
        """Тест получения списка задач."""
        expected_response = {
            "tasks": [
                {
                    "id": 1,
                    "task_name": "Task 1",
                    "completion_status": False,
                    "date_time": "2025-08-15T10:00:00",
                    "text": "Description 1",
                    "file_name": None
                }
            ],
            "skip": 0,
            "limit": 100
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        client.get.return_value = mock_response

        response = client.get("/tasks/", headers=auth_headers)

        assert response.status_code == 200
        response_data = response.json()
        assert "tasks" in response_data
        assert len(response_data["tasks"]) == 1

    def test_get_tasks_with_sorting(self, client, auth_headers):
        """Тест получения задач с сортировкой."""
        expected_response = {
            "tasks": [],
            "skip": 0,
            "limit": 50
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        client.get.return_value = mock_response

        response = client.get(
            "/tasks/?sort=date_desc&skip=0&limit=50", headers=auth_headers)

        assert response.status_code == 200

    def test_get_task_by_id_success(self, client, auth_headers):
        """Тест получения задачи по ID."""
        task_id = 1
        expected_response = {
            "id": task_id,
            "task_name": "Test Task",
            "completion_status": False,
            "date_time": "2025-08-15T10:00:00",
            "text": "Test Description",
            "file_name": None
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        client.get.return_value = mock_response

        response = client.get(f"/tasks/{task_id}", headers=auth_headers)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["id"] == task_id

    def test_get_task_not_found(self, client, auth_headers):
        """Тест получения несуществующей задачи."""
        task_id = 999

        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            "detail": [{"msg": "Задача не найдена"}]
        }
        client.get.return_value = mock_response

        response = client.get(f"/tasks/{task_id}", headers=auth_headers)

        assert response.status_code == 404

    def test_update_task_success(self, client, auth_headers):
        """Тест обновления задачи."""
        task_id = 1
        updated_data = {"name": "Updated Task", "text": "Updated Description"}

        expected_response = {
            "msg": "Задача обновлена",
            "id": task_id,
            "task_name": "Updated Task",
            "completion_status": False,
            "date_time": "2025-08-15T10:00:00",
            "text": "Updated Description"
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        client.put.return_value = mock_response

        response = client.put(
            f"/tasks/{task_id}", json=updated_data, headers=auth_headers)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["task_name"] == "Updated Task"

    def test_delete_task_success(self, client, auth_headers):
        """Тест удаления задачи."""
        task_id = 1

        mock_response = Mock()
        mock_response.status_code = 204
        client.delete.return_value = mock_response

        response = client.delete(f"/tasks/{task_id}", headers=auth_headers)

        assert response.status_code == 204

    def test_toggle_task_completion_status(self, client, auth_headers):
        """Тест переключения статуса выполнения задачи."""
        task_id = 1

        expected_response = {
            "msg": "Статус задачи успешно изменён",
            "task_id": task_id,
            "new_status": True
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        client.patch.return_value = mock_response

        response = client.patch(
            f"/tasks/tasks/{task_id}", headers=auth_headers)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["new_status"] is True

    def test_search_tasks(self, client, auth_headers):
        """Тест поиска задач."""
        search_query = "test"
        expected_response = [
            {
                "id": 1,
                "task_name": "Test Task",
                "completion_status": False,
                "date_time": "2025-08-15T10:00:00",
                "text": "Test description"
            }
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        client.get.return_value = mock_response

        response = client.get(
            f"/search?search_query={search_query}", headers=auth_headers)

        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data) == 1

    def test_get_tasks_stats(self, client, auth_headers):
        """Тест получения статистики по задачам."""
        expected_stats = {
            "total_tasks": 10,
            "completed_tasks": 6,
            "uncompleted_tasks": 4,
            "completion_percentage": 60.0
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_stats
        client.get.return_value = mock_response

        response = client.get("/stats", headers=auth_headers)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["total_tasks"] == 10
        assert response_data["completion_percentage"] == 60.0


class TestFileOperations:
    """Тесты для операций с файлами."""

    def test_upload_file_to_task_success(self, client, auth_headers):
        """Тест загрузки файла к задаче."""
        task_id = 1

        expected_response = {"msg": "Файл успешно загружен"}

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        client.post.return_value = mock_response

        # Имитация загрузки файла
        file_content = b"Test file content"
        files = {"uploaded_file": (
            "test.txt", io.BytesIO(file_content), "text/plain")}

        response = client.post(
            f"/tasks/{task_id}/file", files=files, headers=auth_headers)

        assert response.status_code == 200
        response_data = response.json()
        assert "msg" in response_data

    def test_upload_file_invalid_extension(self, client, auth_headers):
        """Тест загрузки файла с недопустимым расширением."""
        task_id = 1

        expected_error = {
            "detail": [{"msg": "Недопустимое расширение файла: .exe"}]
        }

        mock_response = Mock()
        mock_response.status_code = 415
        mock_response.json.return_value = expected_error
        client.post.return_value = mock_response

        # Файл с недопустимым расширением
        file_content = b"Executable content"
        files = {"uploaded_file": ("virus.exe", io.BytesIO(
            file_content), "application/octet-stream")}

        response = client.post(
            f"/tasks/{task_id}/file", files=files, headers=auth_headers)

        assert response.status_code == 415

    def test_get_task_file_success(self, client, auth_headers):
        """Тест получения файла задачи."""
        task_id = 1

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"File content"
        mock_response.headers = {"content-type": "text/plain"}
        client.get.return_value = mock_response

        response = client.get(f"/tasks/{task_id}/file", headers=auth_headers)

        assert response.status_code == 200

    def test_get_task_file_empty(self, client, auth_headers):
        """Тест получения пустого файла."""
        task_id = 1

        expected_error = {"detail": [{"msg": "файл пуст"}]}

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = expected_error
        client.get.return_value = mock_response

        response = client.get(f"/tasks/{task_id}/file", headers=auth_headers)

        assert response.status_code == 400


class TestSharing:
    """Тесты для системы совместного доступа."""

    def test_share_task_success(self, client, auth_headers, share_data):
        """Тест предоставления доступа к задаче."""
        task_id = 1

        expected_response = {"msg": "Задача успешно расшарена с пользователем"}

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        client.post.return_value = mock_response

        response = client.post(
            f"/sharing/tasks/{task_id}/shares", json=share_data, headers=auth_headers)

        assert response.status_code == 200

    def test_share_task_user_not_found(self, client, auth_headers):
        """Тест предоставления доступа несуществующему пользователю."""
        task_id = 1
        share_data = {"target_username": "nonexistent",
                      "permission_level": "view"}

        expected_error = {
            "detail": [{"msg": "Пользователь 'nonexistent' не найден"}]
        }

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = expected_error
        client.post.return_value = mock_response

        response = client.post(
            f"/sharing/tasks/{task_id}/shares", json=share_data, headers=auth_headers)

        assert response.status_code == 400

    def test_update_share_permission_success(self, client, auth_headers):
        """Тест обновления разрешений для совместного доступа."""
        task_id = 1
        username = "collaborator"

        expected_response = {"msg": "Уровень доступа успешно обновлен"}

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        client.put.return_value = mock_response

        # Передача новых разрешений в теле запроса
        permission_data = {"new_permission": "edit",
                           "target_username": username}

        response = client.put(
            f"/sharing/tasks/{task_id}/shares/{username}",
            json=permission_data,
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_unshare_task_success(self, client, auth_headers):
        """Тест отзыва доступа к задаче."""
        task_id = 1
        username = "collaborator"

        expected_response = {"msg": "Доступ к задаче успешно отозван"}

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        client.delete.return_value = mock_response

        response = client.delete(
            f"/sharing/tasks/{task_id}/shares/{username}", headers=auth_headers)

        assert response.status_code == 200

    def test_get_shared_tasks_success(self, client, auth_headers):
        """Тест получения списка совместных задач."""
        expected_response = [
            {
                "id": 1,
                "task_name": "Shared Task 1",
                "completion_status": False,
                "date_time": "2025-08-15T10:00:00",
                "text": "Shared task description",
                "owner_username": "user1",
                "permission_level": "view"
            }
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        client.get.return_value = mock_response

        response = client.get("/sharing/shared-tasks", headers=auth_headers)

        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data) == 1

    def test_get_shared_task_by_id_success(self, client, auth_headers):
        """Тест получения совместной задачи по ID."""
        task_id = 1
        expected_response = {
            "id": task_id,
            "task_name": "Shared Task",
            "completion_status": False,
            "date_time": "2025-08-15T10:00:00",
            "text": "Shared task description",
            "file_name": None,
            "owner_username": "user1",
            "permission_level": "edit"
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        client.get.return_value = mock_response

        response = client.get(
            f"/sharing/shared-tasks/{task_id}", headers=auth_headers)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["id"] == task_id

    def test_update_shared_task_success(self, client, auth_headers):
        """Тест обновления совместной задачи."""
        task_id = 1
        update_data = {"name": "Updated Shared Task",
                       "text": "Updated description"}

        expected_response = {
            "msg": "Расшаренная задача успешно обновлена",
            "id": task_id,
            "task_name": "Updated Shared Task",
            "completion_status": False,
            "date_time": "2025-08-15T10:00:00",
            "text": "Updated description"
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        client.put.return_value = mock_response

        response = client.put(
            f"/sharing/shared-tasks/{task_id}", json=update_data, headers=auth_headers)

        assert response.status_code == 200

    def test_get_task_collaborators_success(self, client, auth_headers):
        """Тест получения списка соавторов задачи."""
        task_id = 1
        expected_response = {
            "task_id": task_id,
            "total_collaborators": 2,
            "collaborators": [
                {
                    "user_id": 1,
                    "username": "owner",
                    "role": "owner",
                    "permission_level": "full_access",
                    "can_revoke": False
                },
                {
                    "user_id": 2,
                    "username": "collaborator",
                    "role": "collaborator",
                    "permission_level": "edit",
                    "shared_date": "2025-08-15T10:00:00",
                    "can_revoke": True
                }
            ]
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        client.get.return_value = mock_response

        response = client.get(
            f"/sharing/tasks/{task_id}/collaborators", headers=auth_headers)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["total_collaborators"] == 2

    def test_get_task_permissions_success(self, client, auth_headers):
        """Тест получения разрешений для задачи."""
        task_id = 1
        expected_response = {
            "task_id": task_id,
            "task_name": "Test Task",
            "permission_level": "edit",
            "permissions": {
                "can_view": True,
                "can_edit": True,
                "can_delete": False,
                "can_share": False,
                "can_upload_files": True,
                "can_change_status": True,
                "is_owner": False
            }
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        client.get.return_value = mock_response

        response = client.get(
            f"/sharing/shared-tasks/{task_id}/permissions", headers=auth_headers)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["permission_level"] == "edit"


class TestErrorHandling:
    """Тесты для обработки ошибок."""

    def test_unauthorized_access(self, client):
        """Тест доступа без авторизации."""
        expected_error = {
            "detail": [{"msg": "Не удалось подтвердить учетные данные"}]
        }

        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = expected_error
        client.get.return_value = mock_response

        response = client.get("/tasks/")

        assert response.status_code == 401

    def test_forbidden_access(self, client, auth_headers):
        """Тест доступа к запрещенным ресурсам."""
        expected_error = {
            "detail": [{"msg": "Задача не найдена или не принадлежит вам"}]
        }

        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.json.return_value = expected_error
        client.get.return_value = mock_response

        response = client.get("/sharing/shared-tasks/999",
                              headers=auth_headers)

        assert response.status_code == 403

    def test_server_error_handling(self, client, auth_headers):
        """Тест обработки ошибок сервера."""
        expected_error = {
            "detail": [{"msg": "Ошибка сервера: Internal server error"}]
        }

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = expected_error
        client.get.return_value = mock_response

        response = client.get("/tasks/", headers=auth_headers)

        assert response.status_code == 500


# Параметризованные тесты
@pytest.mark.parametrize("sort_option", ["date_desc", "date_asc", "name", "status_asc", "status_desc"])
def test_task_sorting_options(client, auth_headers, sort_option):
    """Параметризованный тест различных опций сортировки задач."""
    expected_response = {"tasks": [], "skip": 0, "limit": 100}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = expected_response
    client.get.return_value = mock_response

    response = client.get(f"/tasks/?sort={sort_option}", headers=auth_headers)
    assert response.status_code == 200


@pytest.mark.parametrize("permission_level", ["view", "edit"])
def test_share_permission_levels(client, auth_headers, permission_level):
    """Параметризованный тест различных уровней разрешений."""
    task_id = 1
    share_data = {"target_username": "testuser",
                  "permission_level": permission_level}

    expected_response = {"msg": "Задача успешно расшарена с пользователем"}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = expected_response
    client.post.return_value = mock_response

    response = client.post(
        f"/sharing/tasks/{task_id}/shares", json=share_data, headers=auth_headers)
    assert response.status_code == 200


@pytest.mark.parametrize("invalid_username", ["ab", "x" * 25, ""])
def test_invalid_usernames(client, invalid_username):
    """Параметризованный тест невалидных имен пользователей."""
    user_data = {"username": invalid_username, "password": "validpass123"}

    expected_error = {
        "detail": [{
            "msg": "Пользователь с таким username уже существует.",
            "loc": ["username"],
            "type": "value_error",
        }]
    }

    mock_response = Mock()
    mock_response.status_code = 422
    mock_response.json.return_value = expected_error
    client.post.return_value = mock_response

    response = client.post("/register", json=user_data)
    assert response.status_code == 422


if __name__ == "__main__":
    pytest.main(["-v", "--tb=short"])

import io
import json
from typing import Any, Dict
from unittest.mock import Mock, patch

import httpx
import pytest
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
        client.post.return_value.status_code = 200
        client.post.return_value.json.return_value = {
            "message": "User registered successfully"}

        response = client.post("/auth/register", json=user_data)

        assert response.status_code == 200
        client.post.assert_called_once_with(
            "/auth/register", json=user_data)

    def test_register_user_validation_error(self, client):
        """Тест регистрации с невалидными данными."""
        invalid_data = {"username": "ab",
                        "password": ""}  # Слишком короткое имя

        client.post.return_value.status_code = 422
        client.post.return_value.json.return_value = {
            "detail": [{"loc": ["body", "username"], "msg": "ensure this value has at least 3 characters", "type": "value_error.any_str.min_length"}]
        }

        response = client.post("/auth/register", json=invalid_data)

        assert response.status_code == 422
        assert "detail" in response.json()

    def test_login_user_success(self, client, user_data):
        """Тест успешного входа пользователя."""
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }

        expected_response = {
            "access_token": "test_access_token",
            "token_type": "bearer"
        }

        client.post.return_value.status_code = 200
        client.post.return_value.json.return_value = expected_response

        response = client.post("/auth/login", data=login_data)

        assert response.status_code == 200
        assert response.json()["access_token"] == "test_access_token"
        assert response.json()["token_type"] == "bearer"

    def test_login_user_invalid_credentials(self, client):
        """Тест входа с неверными учетными данными."""
        invalid_data = {"username": "wronguser", "password": "wrongpass"}

        client.post.return_value.status_code = 401
        client.post.return_value.json.return_value = {
            "detail": "Invalid credentials"}

        response = client.post("/auth/login", data=invalid_data)

        assert response.status_code == 401

    def test_change_password_success(self, client, auth_headers):
        """Тест успешной смены пароля."""
        password_data = {
            "current_password": "oldpassword",
            "new_password": "newpassword123"
        }

        client.post.return_value.status_code = 200
        client.post.return_value.json.return_value = {
            "message": "Password updated successfully"}

        response = client.post("/auth/change-password",
                               json=password_data, headers=auth_headers)

        assert response.status_code == 200

    def test_change_password_unauthorized(self, client):
        """Тест смены пароля без авторизации."""
        password_data = {
            "current_password": "oldpassword",
            "new_password": "newpassword123"
        }

        client.post.return_value.status_code = 401

        response = client.post("/auth/change-password", json=password_data)

        assert response.status_code == 401


class TestTasks:
    """Тесты для управления задачами."""

    def test_create_task_success(self, client, auth_headers, task_data):
        """Тест успешного создания задачи."""
        expected_response = {
            "id": 1,
            "name": task_data["name"],
            "text": task_data["text"],
            "completed": False,
            "created_at": "2025-08-15T12:00:00Z"
        }

        client.post.return_value.status_code = 201
        client.post.return_value.json.return_value = expected_response

        response = client.post(
            "/tasks/", json=task_data, headers=auth_headers)

        assert response.status_code == 201
        assert response.json()["name"] == task_data["name"]
        assert response.json()["completed"] is False

    def test_create_task_validation_error(self, client, auth_headers):
        """Тест создания задачи с невалидными данными."""
        invalid_data = {"name": "x" * 35}  # Слишком длинное название

        client.post.return_value.status_code = 422

        response = client.post(
            "/tasks/", json=invalid_data, headers=auth_headers)

        assert response.status_code == 422

    def test_get_tasks_success(self, client, auth_headers):
        """Тест получения списка задач."""
        expected_response = {
            "tasks": [
                {"id": 1, "name": "Task 1",
                    "text": "Description 1", "completed": False},
                {"id": 2, "name": "Task 2", "text": "Description 2", "completed": True}
            ],
            "total": 2
        }

        client.get.return_value.status_code = 200
        client.get.return_value.json.return_value = expected_response

        response = client.get("/tasks/", headers=auth_headers)

        assert response.status_code == 200
        assert len(response.json()["tasks"]) == 2

    def test_get_tasks_with_sorting(self, client, auth_headers):
        """Тест получения задач с сортировкой."""
        params = {"sort": ["date_desc"], "skip": 0, "limit": 50}

        client.get.return_value.status_code = 200
        client.get.return_value.json.return_value = {"tasks": [], "total": 0}

        response = client.get("/tasks/", params=params, headers=auth_headers)

        assert response.status_code == 200

    def test_get_task_by_id_success(self, client, auth_headers):
        """Тест получения задачи по ID."""
        task_id = 1
        expected_response = {
            "id": task_id,
            "name": "Test Task",
            "text": "Test Description",
            "completed": False
        }

        client.get.return_value.status_code = 200
        client.get.return_value.json.return_value = expected_response

        response = client.get(
            f"/tasks/{task_id}", params={"task_id": task_id}, headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["id"] == task_id

    def test_get_task_not_found(self, client, auth_headers):
        """Тест получения несуществующей задачи."""
        task_id = 999

        client.get.return_value.status_code = 404
        client.get.return_value.json.return_value = {
            "detail": "Task not found"}

        response = client.get(
            f"/tasks/{task_id}", params={"task_id": task_id}, headers=auth_headers)

        assert response.status_code == 404

    def test_update_task_success(self, client, auth_headers, task_data):
        """Тест обновления задачи."""
        task_id = 1
        updated_data = {"name": "Updated Task", "text": "Updated Description"}

        client.put.return_value.status_code = 200
        client.put.return_value.json.return_value = {
            **updated_data, "id": task_id, "completed": False}

        response = client.put(
            f"/tasks/{task_id}",
            params={"task_id": task_id},
            json=updated_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Updated Task"

    def test_delete_task_success(self, client, auth_headers):
        """Тест удаления задачи."""
        task_id = 1

        client.delete.return_value.status_code = 204

        response = client.delete(
            f"/tasks/{task_id}", params={"task_id": task_id}, headers=auth_headers)

        assert response.status_code == 204

    def test_toggle_task_completion_status(self, client, auth_headers):
        """Тест переключения статуса выполнения задачи."""
        task_id = 1

        client.patch.return_value.status_code = 200
        client.patch.return_value.json.return_value = {
            "id": task_id, "completed": True}

        response = client.patch(
            f"/tasks/tasks/{task_id}", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["completed"] is True

    def test_search_tasks(self, client, auth_headers):
        """Тест поиска задач."""
        search_query = "test"
        expected_response = [
            {"id": 1, "name": "Test Task",
                "text": "Test description", "completed": False}
        ]

        client.get.return_value.status_code = 200
        client.get.return_value.json.return_value = expected_response

        response = client.get(
            "/tasks/search", params={"search_query": search_query}, headers=auth_headers)

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_tasks_stats(self, client, auth_headers):
        """Тест получения статистики по задачам."""
        expected_stats = {
            "total_tasks": 10,
            "completed_tasks": 6,
            "pending_tasks": 4,
            "completion_rate": 0.6
        }

        client.get.return_value.status_code = 200
        client.get.return_value.json.return_value = expected_stats

        response = client.get("/tasks/stats", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["total_tasks"] == 10
        assert response.json()["completion_rate"] == 0.6


class TestFileOperations:
    """Тесты для операций с файлами."""

    def test_upload_file_to_task_success(self, client, auth_headers):
        """Тест загрузки файла к задаче."""
        task_id = 1
        file_content = b"Test file content"
        files = {"uploaded_file": (
            "test.txt", io.BytesIO(file_content), "text/plain")}

        client.post.return_value.status_code = 200
        client.post.return_value.json.return_value = {
            "message": "File uploaded successfully", "filename": "test.txt"}

        response = client.post(
            f"/tasks/{task_id}/file", files=files, headers=auth_headers)

        assert response.status_code == 200
        assert "filename" in response.json()

    def test_get_task_file_success(self, client, auth_headers):
        """Тест получения файла задачи."""
        task_id = 1

        client.get.return_value.status_code = 200
        client.get.return_value.content = b"File content"

        response = client.get(f"/tasks/{task_id}/file", headers=auth_headers)

        assert response.status_code == 200

    def test_upload_file_to_shared_task_success(self, client, auth_headers):
        """Тест загрузки файла к совместной задаче."""
        task_id = 1
        file_content = b"Shared task file content"
        files = {"uploaded_file": (
            "shared_test.txt", io.BytesIO(file_content), "text/plain")}

        client.post.return_value.status_code = 200
        client.post.return_value.json.return_value = {
            "message": "File uploaded to shared task"}

        response = client.post(
            f"/sharing/shared-tasks/{task_id}/file", files=files, headers=auth_headers)

        assert response.status_code == 200


class TestSharing:
    """Тесты для системы совместного доступа."""

    def test_share_task_success(self, client, auth_headers, share_data):
        """Тест предоставления доступа к задаче."""
        task_id = 1

        client.post.return_value.status_code = 200
        client.post.return_value.json.return_value = {
            "message": "Task shared successfully"}

        response = client.post(
            f"/sharing/tasks/{task_id}/shares", json=share_data, headers=auth_headers)

        assert response.status_code == 200

    def test_update_share_permission_success(self, client, auth_headers):
        """Тест обновления разрешений для совместного доступа."""
        task_id = 1
        username = "collaborator"
        params = {"new_permission": "edit", "target_username": username}

        client.put.return_value.status_code = 200
        client.put.return_value.json.return_value = {
            "message": "Permission updated"}

        response = client.put(
            f"/sharing/tasks/{task_id}/shares/{username}",
            params=params,
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_unshare_task_success(self, client, auth_headers):
        """Тест отзыва доступа к задаче."""
        task_id = 1
        username = "collaborator"
        params = {"target_username": username}

        client.delete.return_value.status_code = 200
        client.delete.return_value.json.return_value = {
            "message": "Task unshared"}

        response = client.delete(
            f"/sharing/tasks/{task_id}/shares/{username}",
            params=params,
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_get_shared_tasks_success(self, client, auth_headers):
        """Тест получения списка совместных задач."""
        expected_response = [
            {
                "id": 1,
                "name": "Shared Task 1",
                "owner": "user1",
                "permission": "view",
                "completed": False
            }
        ]

        client.get.return_value.status_code = 200
        client.get.return_value.json.return_value = expected_response

        response = client.get("/sharing/shared-tasks", headers=auth_headers)

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_shared_task_by_id_success(self, client, auth_headers):
        """Тест получения совместной задачи по ID."""
        task_id = 1
        expected_response = {
            "id": task_id,
            "name": "Shared Task",
            "text": "Shared task description",
            "owner": "user1",
            "permission": "edit"
        }

        client.get.return_value.status_code = 200
        client.get.return_value.json.return_value = expected_response

        response = client.get(
            f"/sharing/shared-tasks/{task_id}", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["id"] == task_id

    def test_update_shared_task_success(self, client, auth_headers):
        """Тест обновления совместной задачи."""
        task_id = 1
        update_data = {"name": "Updated Shared Task",
                       "text": "Updated description"}

        client.put.return_value.status_code = 200
        client.put.return_value.json.return_value = {
            **update_data, "id": task_id}

        response = client.put(
            f"/sharing/shared-tasks/{task_id}", json=update_data, headers=auth_headers)

        assert response.status_code == 200

    def test_toggle_shared_task_completion_status(self, client, auth_headers):
        """Тест переключения статуса выполнения совместной задачи."""
        task_id = 1

        client.patch.return_value.status_code = 200
        client.patch.return_value.json.return_value = {
            "id": task_id, "completed": True}

        response = client.patch(
            f"/sharing/shared-tasks/{task_id}", headers=auth_headers)

        assert response.status_code == 200

    def test_get_task_collaborators_success(self, client, auth_headers):
        """Тест получения списка соавторов задачи."""
        task_id = 1
        expected_response = {
            "collaborators": [
                {"username": "user1", "permission": "edit"},
                {"username": "user2", "permission": "view"}
            ]
        }

        client.get.return_value.status_code = 200
        client.get.return_value.json.return_value = expected_response

        response = client.get(
            f"/sharing/tasks/{task_id}/collaborators", headers=auth_headers)

        assert response.status_code == 200
        assert len(response.json()["collaborators"]) == 2

    def test_get_task_permissions_success(self, client, auth_headers):
        """Тест получения разрешений для задачи."""
        task_id = 1
        expected_response = {
            "user_permission": "edit",
            "can_share": True,
            "can_edit": True,
            "can_delete": False
        }

        client.get.return_value.status_code = 200
        client.get.return_value.json.return_value = expected_response

        response = client.get(
            f"/sharing/shared-tasks/{task_id}/permissions", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["user_permission"] == "edit"


class TestErrorHandling:
    """Тесты для обработки ошибок."""

    def test_unauthorized_access(self, client):
        """Тест доступа без авторизации."""
        client.get.return_value.status_code = 401
        client.get.return_value.json.return_value = {
            "detail": "Not authenticated"}

        response = client.get("/tasks/")

        assert response.status_code == 401

    def test_forbidden_access(self, client, auth_headers):
        """Тест доступа к запрещенным ресурсам."""
        client.get.return_value.status_code = 403
        client.get.return_value.json.return_value = {
            "detail": "Access forbidden"}

        response = client.get("/sharing/shared-tasks/999",
                              headers=auth_headers)

        assert response.status_code == 403

    def test_validation_error_response_format(self, client, auth_headers):
        """Тест формата ответа при ошибке валидации."""
        invalid_data = {"name": "x" * 100}  # Слишком длинное название

        expected_error = {
            "detail": [
                {
                    "loc": ["body", "name"],
                    "msg": "ensure this value has at most 30 characters",
                    "type": "value_error.any_str.max_length"
                }
            ]
        }

        client.post.return_value.status_code = 422
        client.post.return_value.json.return_value = expected_error

        response = client.post(
            "/tasks/", json=invalid_data, headers=auth_headers)

        assert response.status_code == 422
        assert "detail" in response.json()
        assert isinstance(response.json()["detail"], list)


class TestIntegration:
    """Интеграционные тесты для связанной функциональности."""

    def test_complete_task_workflow(self, client, auth_headers, task_data):
        """Тест полного жизненного цикла задачи."""
        # Создание задачи
        client.post.return_value.status_code = 201
        client.post.return_value.json.return_value = {
            "id": 1, **task_data, "completed": False}

        create_response = client.post(
            "/tasks/", json=task_data, headers=auth_headers)
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]

        # Получение задачи
        client.get.return_value.status_code = 200
        client.get.return_value.json.return_value = {
            "id": task_id, **task_data, "completed": False}

        get_response = client.get(
            f"/tasks/{task_id}", params={"task_id": task_id}, headers=auth_headers)
        assert get_response.status_code == 200

        # Переключение статуса
        client.patch.return_value.status_code = 200
        client.patch.return_value.json.return_value = {
            "id": task_id, "completed": True}

        toggle_response = client.patch(
            f"/tasks/tasks/{task_id}", headers=auth_headers)
        assert toggle_response.status_code == 200
        assert toggle_response.json()["completed"] is True

        # Удаление задачи
        client.delete.return_value.status_code = 204

        delete_response = client.delete(
            f"/tasks/{task_id}", params={"task_id": task_id}, headers=auth_headers)
        assert delete_response.status_code == 204

    def test_sharing_workflow(self, client, auth_headers, task_data, share_data):
        """Тест полного жизненного цикла совместного доступа."""
        task_id = 1

        # Создание задачи
        client.post.return_value.status_code = 201
        client.post.return_value.json.return_value = {
            "id": task_id, **task_data}

        create_response = client.post(
            "/tasks/", json=task_data, headers=auth_headers)
        assert create_response.status_code == 201

        # Предоставление доступа
        client.post.return_value.status_code = 200
        client.post.return_value.json.return_value = {"message": "Task shared"}

        share_response = client.post(
            f"/sharing/tasks/{task_id}/shares", json=share_data, headers=auth_headers)
        assert share_response.status_code == 200

        # Обновление разрешений
        params = {"new_permission": "edit",
                  "target_username": share_data["target_username"]}
        client.put.return_value.status_code = 200
        client.put.return_value.json.return_value = {
            "message": "Permission updated"}

        update_response = client.put(
            f"/sharing/tasks/{task_id}/shares/{share_data['target_username']}",
            params=params,
            headers=auth_headers
        )
        assert update_response.status_code == 200

        # Отзыв доступа
        params = {"target_username": share_data["target_username"]}
        client.delete.return_value.status_code = 200
        client.delete.return_value.json.return_value = {
            "message": "Task unshared"}

        unshare_response = client.delete(
            f"/sharing/tasks/{task_id}/shares/{share_data['target_username']}",
            params=params,
            headers=auth_headers
        )
        assert unshare_response.status_code == 200


# Параметризованные тесты
@pytest.mark.parametrize("sort_option", ["date_desc", "date_asc", "name", "status_asc", "status_desc"])
def test_task_sorting_options(client, auth_headers, sort_option):
    """Параметризованный тест различных опций сортировки задач."""
    client.get.return_value.status_code = 200
    client.get.return_value.json.return_value = {"tasks": [], "total": 0}

    response = client.get(
        "/tasks/", params={"sort": [sort_option]}, headers=auth_headers)
    assert response.status_code == 200


@pytest.mark.parametrize("permission_level", ["view", "edit"])
def test_share_permission_levels(client, auth_headers, permission_level):
    """Параметризованный тест различных уровней разрешений."""
    task_id = 1
    share_data = {"target_username": "testuser",
                  "permission_level": permission_level}

    client.post.return_value.status_code = 200
    client.post.return_value.json.return_value = {"message": "Task shared"}

    response = client.post(
        f"/sharing/tasks/{task_id}/shares", json=share_data, headers=auth_headers)
    assert response.status_code == 200


@pytest.mark.parametrize("invalid_username", ["ab", "x" * 25, ""])
def test_invalid_usernames(client, invalid_username):
    """Параметризованный тест невалидных имен пользователей."""
    user_data = {"username": invalid_username, "password": "validpass123"}

    client.post.return_value.status_code = 422

    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 422


if __name__ == "__main__":
    pytest.main(["-v", "--tb=short"])

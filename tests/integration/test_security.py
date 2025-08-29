import pytest

from src.core.exception import (InvalidCredentialsException,
                                ResourceNotFoundException)

pytestmark = pytest.mark.asyncio


@pytest.mark.integration
class TestSecurity:
    """Интеграционные тесты аспектов безопасности."""

    async def test_search_with_sql_injection_payload_is_handled_safely(self, client, auth_headers):
        """Тест защиты от SQL-инъекций в параметре поиска."""
        # Arrange
        malicious_query = "; DROP TABLE tasks; --"

        # Act
        response = await client.get(
            f"/search?search_query={malicious_query}", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        assert response.json() == []  # Ожидаем пустой результат, а не ошибку БД

    async def test_create_task_with_xss_payload_stores_raw_data(self, client, auth_headers):
        """Тест защиты от XSS: API должен сохранять данные как есть, не экранируя их."""
        # Arrange
        xss_payload = "<script>alert('xss')</script>"
        task_data = {
            "name": xss_payload,
            "text": f"Description with {xss_payload}"
        }

        # Act
        create_response = await client.post(
            "/tasks/", json=task_data, headers=auth_headers)

        # Assert - создание прошло успешно
        assert create_response.status_code == 201
        task_id = create_response.json()["task_id"]

        # Act 2 - получаем задачу обратно
        get_response = await client.get(f"/tasks/{task_id}", headers=auth_headers)

        # Assert 2 - данные сохранились как есть (фильтрация - задача фронтенда)
        assert get_response.status_code == 200
        retrieved_data = get_response.json()
        assert retrieved_data["task_name"] == xss_payload
        assert retrieved_data["text"] == f"Description with {xss_payload}"

    async def test_access_tasks_without_token_returns_401(self, client):
        """Тест доступа к задачам без токена авторизации возвращает 401."""
        # Arrange (no headers)

        # Act
        response = await client.get("/tasks/")

        # Assert
        assert response.status_code == 401

    async def test_access_other_user_task_raises_resource_not_found(self, client, auth_headers2, test_task):
        """Тест доступа к задаче другого пользователя должен вызвать исключение."""
        # Arrange
        # test_task принадлежит test_user (auth_headers)
        # auth_headers2 принадлежит test_user2

        # Act & Assert
        with pytest.raises(ResourceNotFoundException) as exc_info:
            await client.get(f"/tasks/{test_task.id}", headers=auth_headers2)

        assert exc_info.value.error_code == "RESOURCE_NOT_FOUND"
        assert exc_info.value.resource_type == "Задача"
        assert exc_info.value.resource_id == str(test_task.id)

    async def test_access_with_invalid_token_raises_invalid_credentials(self, client):
        """Тест доступа с невалидным (несуществующим) токеном должен вызвать исключение."""
        # Arrange
        invalid_headers = {"Authorization": "Bearer invalid.jwt.token"}

        # Act & Assert
        with pytest.raises(InvalidCredentialsException) as exc_info:
            await client.get("/tasks/", headers=invalid_headers)

        assert exc_info.value.error_code == "INVALID_CREDENTIALS"

    async def test_access_with_malformed_token_returns_401(self, client):
        """Тест доступа с некорректно сформированным токеном возвращает 401."""
        # Arrange
        malformed_headers = {"Authorization": "InvalidFormat NoBearer"}

        # Act
        response = await client.get("/tasks/", headers=malformed_headers)

        # Assert
        assert response.status_code == 401

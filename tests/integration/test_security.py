import pytest

from src.core.exception import (InvalidCredentialsException,
                                ResourceNotFoundException)

pytestmark = pytest.mark.asyncio


@pytest.mark.integration
class TestSecurity:
    """Интеграционные тесты аспектов безопасности."""

    async def test_search_with_sql_injection_payload_is_handled_safely(self, client, auth_headers):
        """Тест защиты от SQL-инъекций в параметре поиска."""
        malicious_query = "; DROP TABLE tasks; --"
        response = await client.get(
            f"/search?search_query={malicious_query}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    async def test_create_task_with_xss_payload_stores_raw_data(self, client, auth_headers):
        """Тест защиты от XSS: API должен сохранять данные как есть, не экранируя их."""
        xss_payload = "<script>alert('xss')</script>"
        task_data = {"name": xss_payload,
                     "text": f"Description with {xss_payload}"}
        create_response = await client.post("/tasks/", json=task_data, headers=auth_headers)
        assert create_response.status_code == 201
        task_id = create_response.json()["task_id"]
        get_response = await client.get(f"/tasks/{task_id}", headers=auth_headers)
        assert get_response.status_code == 200
        retrieved_data = get_response.json()
        assert retrieved_data["task_name"] == xss_payload
        assert retrieved_data["text"] == f"Description with {xss_payload}"

    async def test_access_tasks_without_token_returns_401(self, client):
        """Тест доступа к задачам без токена авторизации возвращает 401."""
        response = await client.get("/tasks/")
        assert response.status_code == 401

    async def test_access_other_user_task_returns_404(self, client, auth_headers2, test_task):
        """Тест доступа к задаче другого пользователя должен вернуть 404 Not Found."""
        response = await client.get(f"/tasks/{test_task.id}", headers=auth_headers2)
        data = response.json()
        assert response.status_code == 404
        assert data["error_code"] == "RESOURCE_NOT_FOUND"
        assert data["detail"]["resource_type"] == "Задача"
        assert data["detail"]["resource_id"] == str(test_task.id)

    async def test_access_with_invalid_token_returns_401(self, client):
        """Тест доступа с невалидным (несуществующим) токеном должен вернуть 401 Unauthorized."""
        invalid_headers = {"Authorization": "Bearer invalid.jwt.token"}
        response = await client.get("/tasks/", headers=invalid_headers)
        data = response.json()
        assert response.status_code == 401
        assert data["error_code"] == "INVALID_CREDENTIALS"

    async def test_access_with_malformed_token_returns_401(self, client):
        """Тест доступа с некорректно сформированным токеном возвращает 401."""
        malformed_headers = {"Authorization": "InvalidFormat NoBearer"}
        response = await client.get("/tasks/", headers=malformed_headers)
        assert response.status_code == 401

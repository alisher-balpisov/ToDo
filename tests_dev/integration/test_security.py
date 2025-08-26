import pytest

from src.core.exception import (InvalidCredentialsException,
                                ResourceNotFoundException)


class TestSecurity:
    """Интеграционные тесты безопасности."""

    def test_sql_injection_protection(self, client, auth_headers):
        """Тест защиты от SQL инъекций."""
        malicious_query = "; DROP TABLE tasks; --"

        response = client.get(
            f"/search?search_query={malicious_query}", headers=auth_headers)

        assert response.status_code == 200
        assert response.json() == []

    def test_xss_protection(self, client, auth_headers):
        """Тест защиты от XSS."""
        xss_payload = "<script>alert('xss')</script>"
        task_data = {
            "name": xss_payload,
            "text": f"Description with {xss_payload}"
        }

        response = client.post("/tasks/", json=task_data, headers=auth_headers)

        # API должен принять данные
        assert response.status_code == 201

        # Получаем задачу обратно
        task_id = response.json()["task_id"]
        response = client.get(f"/tasks/{task_id}", headers=auth_headers)

        assert response.status_code == 200
        # Проверяем, что данные сохранились как есть (фильтрация на фронтенде)
        data = response.json()
        assert data["task_name"] == xss_payload

    def test_unauthorized_task_access(self, client):
        """Тест доступа к задачам без токена."""
        response = client.get("/tasks/")

        assert response.status_code == 401

    def test_access_other_user_task(self, client, auth_headers2, test_task):
        """Тест доступа к задаче другого пользователя."""
        # with pytest.raises(Exception) as exc_info:
        resp = client.get(f"/tasks/{test_task.id}", headers=auth_headers2)
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Задача с ID '1' не найденa"

        # assert ResourceNotFoundException(
        #     "Задача", test_task.id) == exc_info.value

    def test_invalid_token(self, client):
        """Тест с невалидным токеном."""
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        with pytest.raises(Exception) as exc_info:
            client.get("/tasks/", headers=invalid_headers)

        assert InvalidCredentialsException() == exc_info.value

    def test_malformed_token(self, client):
        """Тест с неправильно сформированным токеном."""
        malformed_headers = {"Authorization": "InvalidFormat"}
        exc_info = client.get("/tasks/", headers=malformed_headers)

        assert exc_info.status_code == 401

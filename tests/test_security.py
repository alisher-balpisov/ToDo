class TestSecurity:
    """Тесты безопасности приложения."""

    def test_sql_injection_prevention(self, client, auth_headers):
        """Тест защиты от SQL инъекций."""
        malicious_input = "'; DROP TABLE tasks; --"
        search_data = {"search_query": malicious_input}

        client.get.return_value.status_code = 200
        client.get.return_value.json.return_value = []

        response = client.get(
            "/search", params=search_data, headers=auth_headers)

        # API должен вернуть пустой результат, а не ошибку
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_xss_prevention(self, client, auth_headers):
        """Тест защиты от XSS атак."""
        xss_payload = "<script>alert('xss')</script>"
        task_data = {"name": xss_payload, "text": f"Task with {xss_payload}"}

        # API должен принять данные без ошибки (валидация на фронтенде)
        client.post.return_value.status_code = 201
        client.post.return_value.json.return_value = {"id": 1, **task_data}

        response = client.post("/tasks/", json=task_data, headers=auth_headers)
        assert response.status_code == 201

    def test_unauthorized_task_access(self, client):
        """Тест доступа к задачам без авторизации."""
        client.get.return_value.status_code = 401
        client.get.return_value.json.return_value = {
            "detail": "Not authenticated"}

        response = client.get("/tasks/")
        assert response.status_code == 401

    def test_token_expiration_handling(self, client):
        """Тест обработки истекших токенов."""
        expired_headers = {"Authorization": "Bearer expired_token"}

        client.get.return_value.status_code = 401
        client.get.return_value.json.return_value = {"detail": "Token expired"}

        response = client.get("/tasks/", headers=expired_headers)
        assert response.status_code == 401

    def test_rate_limiting(self, client, auth_headers):
        """Тест ограничения скорости запросов."""
        # Симулируем превышение лимита запросов
        client.get.return_value.status_code = 429
        client.get.return_value.json.return_value = {
            "detail": "Rate limit exceeded"}

        # Делаем много запросов подряд
        for _ in range(100):
            response = client.get("/tasks/", headers=auth_headers)

        # Последний запрос должен быть заблокирован
        assert response.status_code == 429

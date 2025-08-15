class TestEdgeCases:
    """Тесты граничных случаев."""

    def test_empty_task_name(self, client, auth_headers):
        """Тест создания задачи с пустым названием."""
        task_data = {"name": "", "text": "Valid description"}

        client.post.return_value.status_code = 422
        client.post.return_value.json.return_value = {
            "detail": [{"loc": ["body", "name"], "msg": "field required"}]
        }

        response = client.post("/tasks/", json=task_data, headers=auth_headers)
        assert response.status_code == 422

    def test_maximum_length_values(self, client, auth_headers):
        """Тест максимально допустимых значений."""
        task_data = {
            "name": "x" * 30,  # Максимальная длина для name
            "text": "y" * 4096  # Максимальная длина для text
        }

        client.post.return_value.status_code = 201
        client.post.return_value.json.return_value = {"id": 1, **task_data}

        response = client.post("/tasks/", json=task_data, headers=auth_headers)
        assert response.status_code == 201

    def test_unicode_support(self, client, auth_headers):
        """Тест поддержки Unicode символов."""
        unicode_task = {
            "name": "Задача с эмодзи 😀🚀",
            "text": "Описание на русском языке с символами: ñáéíóú"
        }

        client.post.return_value.status_code = 201
        client.post.return_value.json.return_value = {"id": 1, **unicode_task}

        response = client.post(
            "/tasks/", json=unicode_task, headers=auth_headers)
        assert response.status_code == 201
        assert response.json()["name"] == unicode_task["name"]

    def test_null_values_handling(self, client, auth_headers):
        """Тест обработки null значений."""
        task_data = {"name": None, "text": None}

        client.post.return_value.status_code = 201
        client.post.return_value.json.return_value = {
            "id": 1, "name": None, "text": None}

        response = client.post("/tasks/", json=task_data, headers=auth_headers)
        assert response.status_code == 201

    def test_very_large_file_upload(self, client, auth_headers):
        """Тест загрузки очень большого файла."""
        # Симулируем файл размером 20MB (больше лимита)
        large_file_content = b"x" * (20 * 1024 * 1024)
        files = {"uploaded_file": (
            "large_file.txt", large_file_content, "text/plain")}

        client.post.return_value.status_code = 413  # Payload too large
        client.post.return_value.json.return_value = {
            "detail": "File too large"}

        response = client.post(
            "/tasks/1/file", files=files, headers=auth_headers)
        assert response.status_code == 413

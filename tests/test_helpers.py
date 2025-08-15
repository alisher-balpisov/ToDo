class TestHelpers:
    """Вспомогательные функции и утилиты для тестирования."""

    @staticmethod
    def create_test_task(name="Test Task", text="Test Description", completed=False):
        """Создает тестовую задачу с заданными параметрами."""
        return {
            "name": name,
            "text": text,
            "completed": completed,
            "created_at": "2025-08-15T12:00:00Z",
            "updated_at": "2025-08-15T12:00:00Z"
        }

    @staticmethod
    def create_test_user(username="testuser", email="test@example.com"):
        """Создает тестового пользователя."""
        return {
            "username": username,
            "email": email,
            "is_active": True,
            "created_at": "2025-08-15T10:00:00Z"
        }

    @staticmethod
    def assert_task_response_structure(response_data):
        """Проверяет структуру ответа для задачи."""
        required_fields = ["id", "name", "text", "completed"]
        for field in required_fields:
            assert field in response_data, f"Missing field: {field}"

    @staticmethod
    def assert_error_response_structure(response_data):
        """Проверяет структуру ответа с ошибкой."""
        assert "detail" in response_data, "Error response must contain 'detail' field"

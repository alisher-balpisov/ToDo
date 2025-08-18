def assert_error_response(response, expected_status: int, expected_message: str = None):
    """Вспомогательная функция для проверки ошибок API."""
    assert response.status_code == expected_status

    if expected_message:
        data = response.json()
        if "detail" in data:
            if isinstance(data["detail"], list):
                assert any(expected_message in item.get("msg", "")
                           for item in data["detail"])
            else:
                assert expected_message in data["detail"]


def assert_task_structure(task_data: dict):
    """Проверяет структуру данных задачи."""
    required_fields = ["id", "task_name", "completion_status", "date_time"]
    for field in required_fields:
        assert field in task_data, f"Missing required field: {field}"

    assert isinstance(task_data["id"], int)
    assert isinstance(task_data["task_name"], str)
    assert isinstance(task_data["completion_status"], bool)


def create_test_tasks_batch(session, user_id: int, count: int = 5):
    """Создает несколько тестовых задач."""
    from src.tasks.crud.service import create_task_service

    tasks = []
    for i in range(count):
        task = create_task_service(
            session=session,
            current_user_id=user_id,
            task_name=f"Batch Task {i}",
            task_text=f"Batch description {i}"
        )
        tasks.append(task)

    return tasks

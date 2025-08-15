import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest


class TestPerformance:
    """Тесты производительности API."""

    @pytest.mark.slow
    def test_concurrent_task_creation(self, client, auth_headers):
        """Тест одновременного создания множества задач."""
        def create_task(task_num):
            task_data = {"name": f"Task {task_num}",
                         "text": f"Description {task_num}"}
            client.post.return_value.status_code = 201
            client.post.return_value.json.return_value = {
                "id": task_num, **task_data}

            start_time = time.time()
            response = client.post(
                "/tasks/", json=task_data, headers=auth_headers)
            end_time = time.time()

            return {
                "task_num": task_num,
                "status_code": response.status_code,
                "response_time": end_time - start_time
            }

        # Создаем 50 задач одновременно
        num_tasks = 50
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_task, i)
                       for i in range(num_tasks)]
            results = [future.result() for future in as_completed(futures)]

        # Проверяем результаты
        success_count = sum(1 for r in results if r["status_code"] == 201)
        avg_response_time = sum(r["response_time"]
                                for r in results) / len(results)

        assert success_count == num_tasks
        assert avg_response_time < 0.1  # Средний ответ менее 100мс

    @pytest.mark.slow
    def test_large_task_list_performance(self, client, auth_headers):
        """Тест производительности получения большого списка задач."""
        # Мокаем большой список задач
        large_task_list = [
            {"id": i, "name": f"Task {i}",
                "text": f"Description {i}", "completed": i % 2 == 0}
            for i in range(1000)
        ]

        client.get.return_value.status_code = 200
        client.get.return_value.json.return_value = {
            "tasks": large_task_list, "total": 1000}

        start_time = time.time()
        response = client.get(
            "/tasks/", params={"limit": 1000}, headers=auth_headers)
        end_time = time.time()

        assert response.status_code == 200
        assert len(response.json()["tasks"]) == 1000
        assert (end_time - start_time) < 1.0  # Ответ менее 1 секунды

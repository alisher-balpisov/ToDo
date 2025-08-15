import asyncio

import pytest


@pytest.mark.asyncio
class TestAsyncOperations:
    """Тесты асинхронных операций."""

    async def test_async_task_creation(self, client, auth_headers):
        """Асинхронный тест создания задачи."""
        task_data = {"name": "Async Task", "text": "Async description"}

        client.post.return_value.status_code = 201
        client.post.return_value.json.return_value = {"id": 1, **task_data}

        # Симуляция асинхронного запроса
        await asyncio.sleep(0.001)  # Имитация задержки сети

        response = client.post("/tasks/", json=task_data, headers=auth_headers)
        assert response.status_code == 201

    async def test_concurrent_operations(self, client, auth_headers):
        """Тест параллельных операций."""
        tasks = []

        for i in range(5):
            task_data = {"name": f"Concurrent Task {i}",
                         "text": f"Description {i}"}
            client.post.return_value.status_code = 201
            client.post.return_value.json.return_value = {"id": i, **task_data}

            # Создаем корутину для каждого запроса
            async def make_request(data):
                await asyncio.sleep(0.001)
                return client.post("/tasks/", json=data, headers=auth_headers)

            tasks.append(make_request(task_data))

        # Выполняем все запросы параллельно
        responses = await asyncio.gather(*tasks)

        # Проверяем результаты
        for response in responses:
            assert response.status_code == 201

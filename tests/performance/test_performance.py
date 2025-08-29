import asyncio
import time

import pytest

from src.tasks.crud.service import create_task_service


@pytest.mark.slow
class TestPerformance:
    """Тесты производительности для оценки времени отклика под нагрузкой."""

    async def test_concurrent_task_creation_response_time_is_low(self, client, auth_headers):
        """Тест одновременного создания множества задач для проверки времени отклика."""
        num_tasks = 20

        async def create_task(task_num):
            task_data = {"name": f"Concurrent Task {task_num}",
                         "text": f"Desc {task_num}"}
            start_time = time.time()
            response = await client.post("/tasks/", json=task_data, headers=auth_headers)
            end_time = time.time()
            return {"status_code": response.status_code, "response_time": end_time - start_time}

        tasks = [create_task(i) for i in range(num_tasks)]
        results = await asyncio.gather(*tasks)

        success_count = sum(1 for r in results if r["status_code"] == 201)
        avg_response_time = sum(r["response_time"]
                                for r in results) / len(results) if results else 0
        max_response_time = max(r["response_time"]
                                for r in results) if results else 0

        assert success_count == num_tasks, "Не все задачи были успешно созданы"
        assert avg_response_time < 0.5, f"Среднее время отклика {avg_response_time:.2f}с превышает 0.5с"
        assert max_response_time < 2.0, f"Максимальное время отклика {max_response_time:.2f}с превышает 2.0с"

    async def test_get_large_task_list_response_time_is_low(self, client, auth_headers, db_session, test_user):
        """Тест производительности получения большого списка (100+) задач."""
        num_tasks_to_create = 100
        for i in range(num_tasks_to_create):
            # FIX: Pass the session explicitly as a keyword argument for direct service calls
            await create_task_service(
                session=db_session,
                current_user_id=test_user.id,
                task_name=f"Perf Task {i}",
                task_text=f"Desc {i}"
            )

        start_time = time.time()
        response = await client.get(f"/tasks/?limit={num_tasks_to_create}", headers=auth_headers)
        end_time = time.time()
        response_time = end_time - start_time

        assert response.status_code == 200
        assert len(response.json()["tasks"]) == num_tasks_to_create
        assert response_time < 1.0, f"Время получения списка задач {response_time:.2f}с превышает 1.0с"

    async def test_search_in_large_task_list_response_time_is_low(self, client, auth_headers, db_session, test_user):
        """Тест производительности поиска в большом списке задач."""
        search_terms = ["urgent", "important", "meeting", "project", "review"]
        for i in range(50):
            term = search_terms[i % len(search_terms)]
            # FIX: Pass the session explicitly as a keyword argument for direct service calls
            await create_task_service(
                session=db_session,
                current_user_id=test_user.id,
                task_name=f"{term} task {i}",
                task_text=f"Task with {term}"
            )

        start_time = time.time()
        response = await client.get("/search?search_query=urgent", headers=auth_headers)
        end_time = time.time()
        response_time = end_time - start_time

        assert response.status_code == 200
        assert len(response.json()) >= 10
        assert response_time < 0.5, f"Время поиска {response_time:.2f}с превышает 0.5с"

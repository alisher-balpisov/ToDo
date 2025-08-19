import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest


@pytest.mark.slow
class TestPerformance:
    """Тесты производительности."""

    def test_concurrent_task_creation(self, client, auth_headers):
        """Тест одновременного создания множества задач."""
        def create_task(task_num):
            task_data = {"name": f"Task {task_num}",
                         "text": f"Description {task_num}"}
            start_time = time.time()
            response = client.post(
                "/tasks/", json=task_data, headers=auth_headers)
            end_time = time.time()

            return {
                "task_num": task_num,
                "status_code": response.status_code,
                "response_time": end_time - start_time
            }

        # Создаем 20 задач одновременно
        num_tasks = 20
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_task, i)
                       for i in range(num_tasks)]
            results = [future.result() for future in as_completed(futures)]

        # Анализ результатов
        success_count = sum(1 for r in results if r["status_code"] == 201)
        avg_response_time = sum(r["response_time"]
                                for r in results) / len(results)
        max_response_time = max(r["response_time"] for r in results)

        assert success_count == num_tasks
        assert avg_response_time < 0.5  # Средний ответ менее 500мс
        assert max_response_time < 2.0   # Максимальный ответ менее 2с

    def test_large_task_list_performance(self, client, auth_headers, db_session, test_user):
        """Тест производительности получения большого списка задач."""
        # Создаем много задач
        from src.tasks.crud.service import create_task_service

        for i in range(100):
            create_task_service(
                session=db_session,
                current_user_id=test_user.id,
                task_name=f"Performance Task {i}",
                task_text=f"Description {i}"
            )

        # Измеряем время получения списка
        start_time = time.time()
        response = client.get("/tasks/?limit=100", headers=auth_headers)
        end_time = time.time()

        assert response.status_code == 200
        assert len(response.json()["tasks"]) == 100
        assert (end_time - start_time) < 1.0  # Ответ менее 1 секунды

    def test_search_performance(self, client, auth_headers, db_session, test_user):
        """Тест производительности поиска."""
        # Создаем задачи с разными названиями
        from src.tasks.crud.service import create_task_service

        search_terms = ["urgent", "important", "meeting", "project", "review"]
        for i in range(50):
            term = search_terms[i % len(search_terms)]
            create_task_service(
                session=db_session,
                current_user_id=test_user.id,
                task_name=f"{term} task {i}",
                task_text=f"Task with {term} in it"
            )

        # Тестируем поиск
        start_time = time.time()
        response = client.get(
            "/search?search_query=urgent", headers=auth_headers)
        end_time = time.time()

        assert response.status_code == 200
        assert len(response.json()) >= 10  # Должно найти несколько задач
        assert (end_time - start_time) < 0.5  # Поиск менее 500мс

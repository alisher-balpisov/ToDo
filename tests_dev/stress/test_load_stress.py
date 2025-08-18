import statistics
import time
from concurrent.futures import ThreadPoolExecutor

import pytest


@pytest.mark.slow
class TestLoadTesting:
    """Нагрузочные тесты."""

    def test_high_concurrency_task_creation(self, client, auth_headers):
        """Тест создания задач при высокой нагрузке."""
        def create_task_worker(worker_id, num_tasks):
            results = []
            for i in range(num_tasks):
                task_data = {
                    "name": f"Load Test Task {worker_id}-{i}",
                    "text": f"Created by worker {worker_id}"
                }

                start_time = time.time()
                try:
                    response = client.post(
                        "/tasks/", json=task_data, headers=auth_headers)
                    success = response.status_code == 201
                except Exception as e:
                    success = False

                results.append({
                    "success": success,
                    "response_time": time.time() - start_time
                })

            return results

        # Запускаем 10 воркеров, каждый создает 20 задач
        num_workers = 10
        tasks_per_worker = 20

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [
                executor.submit(create_task_worker, i, tasks_per_worker)
                for i in range(num_workers)
            ]

            all_results = []
            for future in futures:
                all_results.extend(future.result())

        # Анализ результатов
        successful_requests = [r for r in all_results if r["success"]]
        response_times = [r["response_time"] for r in successful_requests]

        success_rate = len(successful_requests) / len(all_results)
        avg_response_time = statistics.mean(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[
            18]  # 95th percentile

        # Ассерты для проверки производительности
        assert success_rate >= 0.95  # 95% успешных запросов
        assert avg_response_time < 1.0  # Средний ответ менее 1 секунды
        assert p95_response_time < 2.0  # 95% запросов менее 2 секунд

    def test_database_connection_pool(self, client, auth_headers):
        """Тест пула соединений с БД."""
        def db_intensive_operation():
            # Операция, которая требует подключения к БД
            response = client.get("/tasks/stats", headers=auth_headers)
            return response.status_code == 200

        # Одновременные запросы к БД
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(db_intensive_operation)
                       for _ in range(100)]
            results = [future.result() for future in futures]

        # Все запросы должны быть успешными
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.98

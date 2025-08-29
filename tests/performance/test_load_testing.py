import statistics
import time
from concurrent.futures import ThreadPoolExecutor

import pytest


@pytest.mark.slow
class TestLoadTesting:
    """Нагрузочные тесты для проверки стабильности и производительности системы при большом количестве одновременных запросов."""

    def test_task_creation_under_high_concurrency_is_stable(self, client, auth_headers):
        """Тест создания задач при высокой конкурентной нагрузке на стабильность и производительность."""
        # Arrange
        num_workers = 10
        tasks_per_worker = 20
        total_tasks = num_workers * tasks_per_worker

        def create_task_worker(worker_id):
            results = []
            for i in range(tasks_per_worker):
                task_data = {"name": f"Load Test {worker_id}-{i}",
                             "text": f"Worker {worker_id}"}
                start_time = time.time()
                try:
                    response = client.post(
                        "/tasks/", json=task_data, headers=auth_headers)
                    success = response.status_code == 201
                except Exception:
                    success = False
                response_time = time.time() - start_time
                results.append(
                    {"success": success, "response_time": response_time})
            return results

        # Act
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(create_task_worker, i)
                       for i in range(num_workers)]
            all_results = [
                item for future in futures for item in future.result()]

        # Assert
        successful_requests = [r for r in all_results if r["success"]]
        response_times = [r["response_time"] for r in successful_requests]
        success_rate = len(successful_requests) / total_tasks
        avg_response_time = statistics.mean(
            response_times) if response_times else 0
        p95_response_time = statistics.quantiles(response_times, n=20)[
            18] if len(response_times) > 1 else 0

        assert success_rate >= 0.95, f"Коэффициент успеха {success_rate:.2f} ниже порога 0.95"
        assert avg_response_time < 1.0, f"Среднее время отклика {avg_response_time:.2f}с превышает 1.0с"
        assert p95_response_time < 2.0, f"95-й перцентиль времени отклика {p95_response_time:.2f}с превышает 2.0с"

    def test_database_connection_pool_under_concurrency_is_stable(self, client, auth_headers):
        """Тест стабильности пула соединений с БД при множестве одновременных запросов."""
        # Arrange
        num_workers = 8
        requests_per_worker = 15
        total_requests = num_workers * requests_per_worker

        def db_intensive_operation():
            response = client.get("/stats", headers=auth_headers)
            return response.status_code == 200

        # Act
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(db_intensive_operation)
                       for _ in range(total_requests)]
            results = [future.result() for future in futures]

        # Assert
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.98, f"Коэффициент успеха {success_rate:.2f} ниже порога 0.98"

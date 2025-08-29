import asyncio
import time

import pytest


@pytest.mark.slow
class TestLoadTesting:
    """Нагрузочные тесты."""

    async def test_high_concurrency_task_creation(self, client, auth_headers):
        async def create_task_worker(worker_id, num_tasks):
            results = []
            for i in range(num_tasks):
                task_data = {
                    "name": f"Load Test Task {worker_id}-{i}",
                    "text": f"Created by worker {worker_id}"
                }
                start_time = time.time()
                try:
                    response = await client.post(
                        "/tasks/", json=task_data, headers=auth_headers)
                    success = response.status_code == 201
                except Exception:
                    success = False

                results.append({
                    "success": success,
                    "response_time": time.time() - start_time
                })
            return results

        num_workers = 10
        tasks_per_worker = 20
        coros = [create_task_worker(i, tasks_per_worker)
                 for i in range(num_workers)]
        all_results_nested = await asyncio.gather(*coros)
        all_results = [
            item for sublist in all_results_nested for item in sublist]

        # assert: все успешны?
        assert all(r["success"] for r in all_results)
        print(
            f"Average response time: {sum(r['response_time'] for r in all_results) / len(all_results)}")

    async def test_database_connection_pool(self, client, auth_headers):
        async def db_intensive_operation():
            response = await client.get("/stats", headers=auth_headers)
            return response.status_code == 200

        tasks = [db_intensive_operation() for _ in range(100)]
        results = await asyncio.gather(*tasks)
        success_rate = sum(results) / len(results)
        assert success_rate == 1.0

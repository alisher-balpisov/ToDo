class TestTaskEndpoints:
    """Интеграционные тесты эндпоинтов задач."""

    def test_create_task_success(self, client, auth_headers):
        """Тест успешного создания задачи."""
        task_data = {
            "name": "New Task",
            "text": "Task description"
        }

        response = client.post("/tasks/", json=task_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["task_name"] == "New Task"
        assert "task_id" in data
        assert data["msg"] == "Задача добавлена"

    def test_create_task_without_name(self, client, auth_headers):
        """Тест создания задачи без названия."""
        task_data = {
            "text": "Task description"
        }

        response = client.post("/tasks/", json=task_data, headers=auth_headers)

        assert response.status_code == 400

    def test_get_tasks(self, client, auth_headers, test_task):
        """Тест получения списка задач."""
        response = client.get("/tasks/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert len(data["tasks"]) >= 1
        assert data["tasks"][0]["task_name"] == test_task.name

    def test_get_tasks_with_pagination(self, client, auth_headers, db_session, test_user):
        """Тест получения задач с пагинацией."""
        # Создаем дополнительные задачи
        from src.tasks.crud.service import create_task_service
        for i in range(5):
            create_task_service(
                session=db_session,
                current_user_id=test_user.id,
                task_name=f"Task {i}",
                task_text=f"Description {i}"
            )

        response = client.get("/tasks/?skip=2&limit=2", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 2
        assert data["skip"] == 2
        assert data["limit"] == 2

    def test_get_task_by_id(self, client, auth_headers, test_task):
        """Тест получения задачи по ID."""
        response = client.get(f"/tasks/{test_task.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_task.id
        assert data["task_name"] == test_task.name

    def test_get_task_not_found(self, client, auth_headers):
        """Тест получения несуществующей задачи."""
        response = client.get("/tasks/999", headers=auth_headers)

        assert response.status_code == 404

    def test_update_task_success(self, client, auth_headers, test_task):
        """Тест успешного обновления задачи."""
        update_data = {
            "name": "Updated Task",
            "text": "Updated description"
        }

        response = client.put(
            f"/tasks/{test_task.id}", json=update_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["task_name"] == "Updated Task"
        assert data["text"] == "Updated description"

    def test_delete_task_success(self, client, auth_headers, test_task):
        """Тест успешного удаления задачи."""
        response = client.delete(
            f"/tasks/{test_task.id}", headers=auth_headers)

        assert response.status_code == 204

    def test_toggle_task_completion(self, client, auth_headers, test_task):
        """Тест переключения статуса выполнения задачи."""
        original_status = test_task.completion_status

        response = client.patch(
            f"/tasks/{test_task.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["new_status"] != original_status

    def test_search_tasks(self, client, auth_headers, test_task):
        """Тест поиска задач."""
        response = client.get(
            f"/search?search_query={test_task.name}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(task["task_name"] == test_task.name for task in data)

    def test_get_tasks_stats(self, client, auth_headers, db_session, test_user):
        """Тест получения статистики задач."""
        # Создаем несколько задач с разными статусами
        from src.tasks.crud.service import create_task_service
        task1 = create_task_service(
            db_session, test_user.id, "Task 1", "Desc 1")
        task2 = create_task_service(
            db_session, test_user.id, "Task 2", "Desc 2")

        # Помечаем одну как выполненную
        task1.completion_status = True
        db_session.commit()
        db_session.refresh(task1)
        db_session.refresh(task2)

        response = client.get("/stats", headers=auth_headers)
        print(response.json(), '<- resp')

        assert response.status_code == 200
        data = response.json()
        assert "total_tasks" in data
        assert "completed_tasks" in data
        assert "uncompleted_tasks" in data
        assert "completion_percentage" in data
        assert data["total_tasks"] >= 2

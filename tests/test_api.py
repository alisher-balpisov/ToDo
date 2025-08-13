# from unittest.mock import MagicMock

# import pytest
# from fastapi.testclient import TestClient
# # db.py
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker

# from src.main import app
# from src.tasks.crud.views import create_task

# DATABASE_URL = "postgresql+psycopg2://user:pass@localhost/db_name"

# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# # ======== Тест ========


# def test_create_task_success(client, monkeypatch):
#     # Мокаем create_task_service
#     fake_task = MagicMock()
#     fake_task.id = 1
#     fake_task.name = "Test Task"
#     monkeypatch.setattr(
#         "src.tasks.routes.create_task_service",  # путь к функции
#         lambda session, current_user_id, task_name, task_text: fake_task
#     )

#     payload = {
#         "name": "Test Task",
#         "text": "Some description"
#     }

#     response = client.post("/tasks/", json=payload)

#     assert response.status_code == 201
#     data = response.json()
#     assert data["msg"] == "Задача добавлена"
#     assert data["task_id"] == "1"
#     assert data["task_name"] == "Test Task"

import pytest
from fastapi.testclient import TestClient
from src.main import app
from tests.database import setup_database

@pytest.fixture(scope="function")
def auth_clients():
    client1 = TestClient(app)
    client1.post("/auth/register", json={"username": "testuser1", "password": "Testpassword1"})
    response1 = client1.post("/auth/login", data={"username": "testuser1", "password": "Testpassword1"})
    token1 = response1.json()["access_token"]
    client1.headers = {"Authorization": f"Bearer {token1}"}

    client2 = TestClient(app)
    client2.post("/auth/register", json={"username": "testuser2", "password": "Testpassword2"})
    response2 = client2.post("/auth/login", data={"username": "testuser2", "password": "Testpassword2"})
    token2 = response2.json()["access_token"]
    client2.headers = {"Authorization": f"Bearer {token2}"}
    
    return client1, client2

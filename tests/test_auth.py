import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_register_user():
    response = client.post(
        "/auth/register",
        json={"username": "testuser", "password": "Testpassword1"},
    )
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

def test_login_for_access_token():
    client.post(
        "/auth/register",
        json={"username": "testuser2", "password": "Testpassword2"},
    )
    response = client.post(
        "/auth/login",
        data={"username": "testuser2", "password": "Testpassword2"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

import pytest

from src.auth.models import User


class TestAuthEndpoints:
    """Интеграционные тесты эндпоинтов аутентификации."""

    def test_register_success(self, client, db_session):
        """Тест успешной регистрации."""
        user_data = {
            "username": "newuser",
            "password": "Password123"
        }

        response = client.post("/register", json=user_data)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert "password" in data
        assert data["msg"] == "Регистрация пройдена успешно"

        # Проверяем, что пользователь создан в БД
        user = db_session.query(User).filter(
            User.username == "newuser"
        ).first()
        assert user is not None

    def test_register_duplicate_username(self, client, test_user):
        """Тест регистрации с существующим именем пользователя."""
        user_data = {
            "username": test_user.username,
            "password": "Password123"
        }

        response = client.post("/register", json=user_data)

        assert response.status_code == 422
        data = response.json()
        assert "уже существует" in data["detail"]["msg"]

    def test_register_invalid_password(self, client):
        """Тест регистрации с невалидным паролем."""
        user_data = {
            "username": "newuser",
            "password": "123"  # Слишком короткий
        }

        response = client.post("/register", json=user_data)

        assert response.status_code == 422

    def test_login_success(self, client, test_user):
        """Тест успешного входа в систему."""
        login_data = {
            "username": test_user.username,
            "password": "Password123"
        }

        response = client.post("/login", data=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["type"] == "bearer"

    def test_login_wrong_password(self, client, test_user):
        """Тест входа с неправильным паролем."""
        login_data = {
            "username": test_user.username,
            "password": "WrongPassword"
        }

        response = client.post("/login", data=login_data)

        assert response.status_code == 401
        data = response.json()
        assert "Неверное имя пользователя или пароль" in data["detail"]["msg"]

    def test_login_nonexistent_user(self, client):
        """Тест входа несуществующего пользователя."""
        login_data = {
            "username": "nonexistent",
            "password": "Password123"
        }

        response = client.post("/login", data=login_data)

        assert response.status_code == 401

    def test_change_password_success(self, client, test_user, auth_headers):
        """Тест успешной смены пароля."""
        password_data = {
            "current_password": "Password123",
            "new_password": "NewPassword123",
            "confirm_password": "NewPassword123"
        }

        response = client.post(
            "/change-password", json=password_data, headers=auth_headers)
        print(response.json())
        assert response.status_code == 200
        data = response.json()
        assert "успешно изменён" in data["msg"]

    def test_change_password_wrong_current(self, client, auth_headers):
        """Тест смены пароля с неправильным текущим паролем."""
        password_data = {
            "current_password": "WrongPassword",
            "new_password": "NewPassword123",
            "confirm_password": "NewPassword123"
        }

        response = client.post(
            "/change-password", json=password_data, headers=auth_headers)

        assert response.status_code == 400
        data = response.json()
        assert "Неверный текущий пароль" in data["detail"]["msg"]

    def test_unauthorized_access(self, client):
        """Тест доступа без авторизации."""
        response = client.post("/change-password", json={})

        assert response.status_code == 401

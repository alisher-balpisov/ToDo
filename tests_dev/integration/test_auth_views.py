import pytest

from src.auth.models import User
from src.core.config import settings
from src.core.exception import (InvalidCredentialsException,
                                InvalidInputException, ValidationException)


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
        with pytest.raises(Exception) as exc_info:
            client.post("/register", json=user_data)

        assert ValidationException(
            "Пользователь с такими данными уже существует "
            "или введенные данные некорректны") == exc_info.value

    def test_register_invalid_password(self, client):
        """Тест регистрации с невалидным паролем."""
        user_data = {
            "username": "newuser",
            "password": "123"  # Слишком короткий
        }
        with pytest.raises(Exception) as exc_info:
            client.post("/register", json=user_data)

        assert InvalidInputException(
            "пароль", "короткий пароль",
            f"минимум {settings.PASSWORD_MIN_LENGTH} символов") == exc_info.value

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
        with pytest.raises(Exception) as exc_info:
            client.post("/login", data=login_data)

        assert InvalidCredentialsException('testuser') == exc_info.value

    def test_login_nonexistent_user(self, client):
        """Тест входа несуществующего пользователя."""
        login_data = {
            "username": "nonexistent",
            "password": "Password123"
        }
        with pytest.raises(Exception) as exc_info:
            client.post("/login", data=login_data)

        assert InvalidCredentialsException('nonexistent') == exc_info.value

    def test_change_password_success(self, client, test_user, auth_headers):
        """Тест успешной смены пароля."""
        password_data = {
            "current_password": "Password123",
            "new_password": "NewPassword123",
            "confirm_password": "NewPassword123"
        }

        response = client.post(
            "/change-password", json=password_data, headers=auth_headers)
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
        with pytest.raises(Exception) as exc_info:
            client.post(
                "/change-password", json=password_data, headers=auth_headers)

        assert InvalidCredentialsException() == exc_info.value

    def test_unauthorized_access(self, client):
        """Тест доступа без авторизации."""
        response = client.post("/change-password", json={})

        assert response.status_code == 401

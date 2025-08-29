# tests_dev/integration/test_auth_views_fixed.py
"""
Исправленная версия тестов аутентификации
"""
import pytest

from src.auth.models import User


class TestAuthEndpoints:
    """Интеграционные тесты эндпоинтов аутентификации."""

    async def test_register_success(self, client, db_session):
        """Тест успешной регистрации."""
        user_data = {
            "username": "newuser",
            "password": "Password123"
        }

        response = await client.post("/register", json=user_data)

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

        response = client.post("/register", json=user_data)

        # Должен возвращать ошибку HTTP вместо исключения
        assert response.status_code == 400
        data = response.json()
        assert "error_type" in data
        assert "ValidationException" in data["error_type"]

    def test_register_invalid_password(self, client):
        """Тест регистрации с невалидным паролем."""
        user_data = {
            "username": "newuser",
            "password": "123"  # Слишком короткий
        }

        response = client.post("/register", json=user_data)

        # FastAPI возвращает ошибку валидации Pydantic
        assert response.status_code == 422  # Unprocessable Entity
        data = response.json()
        assert "detail" in data

    def test_register_auto_generated_password(self, client, db_session):
        """Тест регистрации с автогенерацией пароля."""
        user_data = {
            "username": "autouser"
            # Пароль не указан - должен сгенерироваться автоматически
        }

        response = client.post("/register", json=user_data)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "autouser"
        assert "generated_password" in data
        assert len(data["generated_password"]) >= 8

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
        assert "refresh_token" in data
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
        assert "error_code" in data
        assert data["error_code"] == "INVALID_CREDENTIALS"

    def test_login_nonexistent_user(self, client):
        """Тест входа несуществующего пользователя."""
        login_data = {
            "username": "nonexistent",
            "password": "Password123"
        }

        response = client.post("/login", data=login_data)

        assert response.status_code == 401
        data = response.json()
        assert "error_code" in data
        assert data["error_code"] == "INVALID_CREDENTIALS"

    def test_login_account_lockout(self, client, test_user, db_session):
        """Тест блокировки аккаунта после неудачных попыток входа."""
        login_data = {
            "username": test_user.username,
            "password": "WrongPassword"
        }

        # Делаем максимальное количество неудачных попыток
        for _ in range(5):  # MAX_LOGIN_ATTEMPTS = 5
            response = client.post("/login", data=login_data)
            assert response.status_code == 401

        # Следующая попытка должна показать блокировку
        response = client.post("/login", data=login_data)
        assert response.status_code == 401
        data = response.json()
        assert "заблокирована" in data["message"].lower()

    def test_refresh_token(self, client, test_user):
        """Тест обновления токена."""
        # Сначала получаем токены
        login_data = {
            "username": test_user.username,
            "password": "Password123"
        }
        login_response = client.post("/login", data=login_data)
        tokens = login_response.json()

        # Используем refresh токен для получения нового access токена
        refresh_headers = {
            "Authorization": f"Bearer {tokens['refresh_token']}"}
        response = client.post("/refresh", headers=refresh_headers)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

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

        response = client.post(
            "/change-password", json=password_data, headers=auth_headers)

        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == "INVALID_CREDENTIALS"

    def test_change_password_mismatch(self, client, auth_headers):
        """Тест смены пароля с несовпадающим подтверждением."""
        password_data = {
            "current_password": "Password123",
            "new_password": "NewPassword123",
            "confirm_password": "DifferentPassword123"
        }

        response = client.post(
            "/change-password", json=password_data, headers=auth_headers)

        assert response.status_code == 422  # Validation error

    def test_change_password_same_as_current(self, client, auth_headers):
        """Тест смены пароля на тот же самый."""
        password_data = {
            "current_password": "Password123",
            "new_password": "Password123",  # Тот же пароль
            "confirm_password": "Password123"
        }

        response = client.post(
            "/change-password", json=password_data, headers=auth_headers)

        assert response.status_code == 400
        data = response.json()
        assert "совпадает со старым" in data["message"]

    def test_unauthorized_access(self, client):
        """Тест доступа без авторизации."""
        response = client.post("/change-password", json={})
        assert response.status_code == 401

    def test_invalid_token(self, client):
        """Тест с недействительным токеном."""
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = client.post(
            "/change-password", json={}, headers=invalid_headers)
        assert response.status_code == 401

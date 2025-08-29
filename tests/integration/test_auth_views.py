# tests/integration/test_auth_views.py
"""
Исправленная версия тестов аутентификации
"""
import pytest
from sqlalchemy import select

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

        # Исправление: используем async select вместо query
        result = await db_session.execute(
            select(User).where(User.username == "newuser")
        )
        user = result.scalar_one_or_none()
        assert user is not None

    async def test_register_duplicate_username(self, client, test_user):
        """Тест регистрации с существующим именем пользователя."""
        user_data = {
            "username": test_user.username,
            "password": "Password123"
        }

        response = await client.post("/register", json=user_data)

        # Должен возвращать ошибку HTTP вместо исключения
        assert response.status_code == 400
        data = response.json()
        assert "error_type" in data
        assert "ValidationException" in data["error_type"]

    async def test_register_invalid_password(self, client):
        """Тест регистрации с невалидным паролем."""
        user_data = {
            "username": "newuser",
            "password": "123"  # Слишком короткий
        }

        response = await client.post("/register", json=user_data)

        # Схема валидирует пароль при инициализации
        assert response.status_code == 400  # Bad Request от InvalidInputException
        data = response.json()
        assert data["error_code"] == "INVALID_INPUT"

    async def test_register_auto_generated_password(self, client, db_session):
        """Тест регистрации с автогенерацией пароля."""
        user_data = {
            "username": "autouser"
            # Пароль не указан - должен сгенерироваться автоматически
        }

        response = await client.post("/register", json=user_data)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "autouser"
        assert "generated_password" in data
        assert len(data["generated_password"]) >= 8

    async def test_login_success(self, client, test_user):
        """Тест успешного входа в систему."""
        login_data = {
            "username": test_user.username,
            "password": "Password123"
        }

        response = await client.post("/login", data=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["type"] == "bearer"

    async def test_login_wrong_password(self, client, test_user):
        """Тест входа с неправильным паролем."""
        login_data = {
            "username": test_user.username,
            "password": "WrongPassword"
        }

        response = await client.post("/login", data=login_data)

        assert response.status_code == 401
        data = response.json()
        assert "error_code" in data
        assert data["error_code"] == "INVALID_CREDENTIALS"

    async def test_login_nonexistent_user(self, client):
        """Тест входа несуществующего пользователя."""
        login_data = {
            "username": "nonexistent",
            "password": "Password123"
        }

        response = await client.post("/login", data=login_data)

        assert response.status_code == 401
        data = response.json()
        assert "error_code" in data
        assert data["error_code"] == "INVALID_CREDENTIALS"

    async def test_login_account_lockout(self, client, test_user, db_session):
        """Тест блокировки аккаунта после неудачных попыток входа."""
        login_data = {
            "username": test_user.username,
            "password": "WrongPassword"
        }

        # Делаем максимальное количество неудачных попыток
        for _ in range(5):  # MAX_LOGIN_ATTEMPTS = 5
            response = await client.post("/login", data=login_data)
            assert response.status_code == 401

        # Обязательно коммитим изменения после неудачных попыток
        await db_session.commit()

        # Следующая попытка должна показать блокировку
        response = await client.post("/login", data=login_data)
        assert response.status_code == 401
        data = response.json()
        assert "заблокирована" in data["message"].lower()

    async def test_refresh_token(self, client, test_user):
        """Тест обновления токена."""
        # Сначала получаем токены
        login_data = {
            "username": test_user.username,
            "password": "Password123"
        }
        login_response = await client.post("/login", data=login_data)
        tokens = login_response.json()

        # Используем refresh токен для получения нового access токена
        refresh_headers = {
            "Authorization": f"Bearer {tokens['refresh_token']}"}
        response = await client.post("/refresh", headers=refresh_headers)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_change_password_success(self, client, test_user, auth_headers):
        """Тест успешной смены пароля."""
        password_data = {
            "current_password": "Password123",
            "new_password": "NewPassword123",
            "confirm_password": "NewPassword123"
        }

        response = await client.post(
            "/change-password", json=password_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "успешно изменён" in data["msg"]

    async def test_change_password_wrong_current(self, client, auth_headers):
        """Тест смены пароля с неправильным текущим паролем."""
        password_data = {
            "current_password": "WrongPassword",
            "new_password": "NewPassword123",
            "confirm_password": "NewPassword123"
        }

        response = await client.post(
            "/change-password", json=password_data, headers=auth_headers)

        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == "INVALID_CREDENTIALS"

    async def test_change_password_mismatch(self, client, auth_headers):
        """Тест смены пароля с несовпадающим подтверждением."""
        password_data = {
            "current_password": "Password123",
            "new_password": "NewPassword123",
            "confirm_password": "DifferentPassword123"
        }
        response = await client.post(
            "/change-password", json=password_data, headers=auth_headers)

        # Fix: Change expected status code from 422 to 400
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "INVALID_INPUT"
        assert "подтверждение пароля" in data["detail"]["field_name"]

    async def test_change_password_same_as_current(self, client, auth_headers):
        """Тест смены пароля на тот же самый."""
        password_data = {
            "current_password": "Password123",
            "new_password": "Password123",  # Тот же пароль
            "confirm_password": "Password123"
        }

        response = await client.post(
            "/change-password", json=password_data, headers=auth_headers)

        assert response.status_code == 400
        data = response.json()
        assert "совпадает со старым" in data["message"]

    async def test_unauthorized_access(self, client):
        """Тест доступа без авторизации."""
        response = await client.post("/change-password", json={})
        assert response.status_code == 401

    async def test_invalid_token(self, client):
        """Тест с недействительным токеном."""
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = await client.post(
            "/change-password", json={}, headers=invalid_headers)
        assert response.status_code == 401

    # Дополнительные тесты для улучшения покрытия
    async def test_register_empty_password_generates_auto(self, client, db_session):
        """Тест регистрации с пустым паролем - должен автогенерироваться."""
        user_data = {
            "username": "emptypassuser",
            "password": ""  # Пустой пароль
        }

        response = await client.post("/register", json=user_data)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "emptypassuser"
        assert "generated_password" in data

    async def test_refresh_with_access_token_should_fail(self, client, test_user):
        """Тест использования access токена вместо refresh токена."""
        # Получаем токены
        login_data = {
            "username": test_user.username,
            "password": "Password123"
        }
        login_response = await client.post("/login", data=login_data)
        tokens = login_response.json()

        # Пытаемся использовать access токен для refresh
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        response = await client.post("/refresh", headers=headers)

        assert response.status_code == 401

    async def test_change_password_weak_new_password(self, client, auth_headers):
        """Тест смены пароля на слабый пароль."""
        password_data = {
            "current_password": "Password123",
            "new_password": "weak",  # Слабый пароль
            "confirm_password": "weak"
        }

        response = await client.post(
            "/change-password", json=password_data, headers=auth_headers)

        assert response.status_code == 400  # Bad Request от InvalidInputException
        data = response.json()
        assert data["error_code"] == "INVALID_INPUT"

    async def test_register_username_too_short(self, client):
        """Тест регистрации с коротким именем пользователя."""
        user_data = {
            "username": "ab",  # Меньше минимума (3 символа)
            "password": "Password123"
        }

        response = await client.post("/register", json=user_data)
        assert response.status_code == 422

    async def test_register_username_too_long(self, client):
        """Тест регистрации с длинным именем пользователя."""
        user_data = {
            "username": "a" * 31,  # Больше максимума (30 символов)
            "password": "Password123"
        }

        response = await client.post("/register", json=user_data)
        assert response.status_code == 422

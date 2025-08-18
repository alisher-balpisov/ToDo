import os

import bcrypt
import pytest

from src.auth.models import ToDoUser, get_hash_password


class TestToDoUserModel:
    """Тесты модели пользователя."""

    def test_password_hashing(self):
        """Тест хеширования пароля."""
        password = "testpassword123"
        hashed = get_hash_password(password)

        assert isinstance(hashed, bytes)
        assert hashed != password.encode()
        assert bcrypt.checkpw(password.encode(), hashed)

    def test_set_password(self, db_session):
        """Тест установки пароля."""
        user = ToDoUser(username="testuser", email="test@example.com")
        password = "NewPassword123"

        user.set_password(password)

        assert user.password is not None
        assert user.verify_password(password)

    def test_set_empty_password_raises_error(self, db_session):
        """Тест ошибки при пустом пароле."""
        user = ToDoUser(username="testuser", email="test@example.com")

        with pytest.raises(ValueError, match="Password cannot be empty"):
            user.set_password("")

    def test_verify_password_success(self):
        """Тест успешной проверки пароля."""
        user = ToDoUser(username="testuser", email="test@example.com")
        password = "TestPassword123"
        user.set_password(password)

        assert user.verify_password(password)

    def test_verify_password_failure(self):
        """Тест неуспешной проверки пароля."""
        user = ToDoUser(username="testuser", email="test@example.com")
        user.set_password("correct_password")

        assert not user.verify_password("wrong_password")

    def test_verify_password_empty(self):
        """Тест проверки пустого пароля."""
        user = ToDoUser(username="testuser", email="test@example.com")
        user.set_password("password")

        assert not user.verify_password("")
        assert not user.verify_password(None)

    def test_get_token(self):
        """Тест генерации JWT токена."""
        user = ToDoUser(username="testuser", email="test@example.com")
        token = user.get_token

        assert isinstance(token, str)
        assert len(token) > 0

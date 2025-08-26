import bcrypt
import pytest

from src.auth.models import User, hash_password
from src.core.exception import MissingRequiredFieldException


class TestToDoUserModel:
    """Тесты модели пользователя."""

    def test_password_hashing(self):
        """Тест хеширования пароля."""
        password = "testpassword123"
        hashed = hash_password(password)

        assert isinstance(hashed, bytes)
        assert hashed != password.encode()
        assert bcrypt.checkpw(password.encode(), hashed)

    def test_set_password(self, db_session):
        """Тест установки пароля."""
        user = User(username="testuser", email="test@example.com")
        password = "NewPassword123"

        user.set_password(password)

        assert user.password_hash is not None
        assert user.verify_password(password)

    def test_set_empty_password_raises_error(self, db_session):
        """Тест ошибки при пустом пароле."""
        user = User(username="testuser", email="test@example.com")

        with pytest.raises(MissingRequiredFieldException) as exc_info:
            user.set_password("")

        assert exc_info.value.error_code == "MISSING_REQUIRED_FIELD"
        assert "новый пароль" in str(exc_info.value)
        assert exc_info.value.details["missing_fields"] == ["новый пароль"]

    @pytest.mark.parametrize("set_pw, verify_pw, expected_bool", [
        ("TestPassword123", "TestPassword123", True),
        ("correct_password", "wrong_password", False),
        ("password", "", False),
        ("password", None, False)
    ])
    def test_verify_password(self, set_pw, verify_pw, expected_bool):
        """Тест проверки пароля."""
        user = User(username="testuser", email="test@example.com")
        user.set_password(set_pw)

        assert user.verify_password(verify_pw) is expected_bool

    def test_token(self):
        """Тест генерации JWT токена."""
        user = User(username="testuser", email="test@example.com")
        token = user.token()

        assert isinstance(token, str)
        assert len(token) > 0

import bcrypt
import pytest

from src.auth.models import User, hash_password
from src.core.exception import MissingRequiredFieldException


@pytest.mark.unit
class TestUserModel:
    """Юнит-тесты для модели пользователя (User)."""

    def test_hash_password_returns_valid_bcrypt_hash(self):
        """Тест хеширования пароля, проверяющий корректность хеша."""
        # Arrange
        password = "testpassword123"

        # Act
        hashed = hash_password(password)

        # Assert
        assert isinstance(hashed, bytes)
        assert hashed != password.encode()
        assert bcrypt.checkpw(password.encode(), hashed)

    def test_set_password_correctly_hashes_and_sets_password(self):
        """Тест установки пароля пользователю."""
        # Arrange
        user = User(username="testuser", email="test@example.com")
        password = "NewPassword123"

        # Act
        user.set_password(password)

        # Assert
        assert user.password_hash is not None
        assert user.verify_password(password) is True

    def test_set_empty_password_raises_missing_field_exception(self):
        """Тест установки пустого пароля должен вызвать исключение."""
        # Arrange
        user = User(username="testuser")

        # Act & Assert
        with pytest.raises(MissingRequiredFieldException) as exc_info:
            user.set_password("")

        assert exc_info.value.error_code == "MISSING_REQUIRED_FIELD"
        assert "новый пароль" in exc_info.value.missing_fields

    @pytest.mark.parametrize("set_pw, verify_pw, expected_result", [
        ("TestPassword123", "TestPassword123", True),
        ("correct_password", "wrong_password", False),
        ("password", "", False),
        ("password", None, False)
    ])
    def test_verify_password_with_various_inputs_returns_correct_bool(self, set_pw, verify_pw, expected_result):
        """Параметризованный тест проверки пароля с разными входными данными."""
        # Arrange
        user = User(username="testuser")
        user.set_password(set_pw)

        # Act
        result = user.verify_password(verify_pw)

        # Assert
        assert result is expected_result

    def test_token_generation_returns_valid_jwt_string(self):
        """Тест генерации JWT токена для пользователя."""
        # Arrange
        user = User(username="testuser", email="test@example.com")

        # Act
        token = user.token()

        # Assert
        assert isinstance(token, str)
        assert len(token) > 0
        # Basic check for JWT structure (header.payload.signature)
        assert token.count('.') == 2

import pytest

from src.auth.schemas import (UserPasswordUpdateSchema, UserRegisterSchema,
                              generate_password, validate_strong_password)
from src.common.constants import LENGTH_GENERATED_PASSWORD
from src.core.config import settings
from src.core.exception import (InvalidInputException,
                                MissingRequiredFieldException)


@pytest.mark.unit
class TestUserRegisterSchema:
    """Юнит-тесты для схемы регистрации пользователя (UserRegisterSchema)."""

    def test_init_without_password_autogenerates_strong_password(self):
        """Тест автогенерации пароля, если он не предоставлен."""
        # Arrange
        data = {"username": "testuser"}

        # Act
        schema = UserRegisterSchema(**data)

        # Assert
        assert schema.username == "testuser"
        assert len(schema.password) >= 8
        assert validate_strong_password(schema.password) == schema.password

    @pytest.mark.parametrize("password, expected_part_of_message", [
        ("123", f"минимум {settings.PASSWORD_MIN_LENGTH} символов"),
        ("password123", "заглавными буквами"),
        ("PASSWORD123", "строчными буквами"),
        ("Password", "цифрами"),
        ("Password 123", "без пробелов"),
    ])
    def test_init_with_invalid_password_raises_invalid_input(self, password, expected_part_of_message):
        """Тест валидации невалидных паролей должен вызвать InvalidInputException."""
        # Arrange
        data = {"username": "testuser", "password": password}

        # Act & Assert
        with pytest.raises(InvalidInputException) as exc_info:
            UserRegisterSchema(**data)

        assert exc_info.value.field_name == "пароль"
        assert expected_part_of_message in exc_info.value.expected_format


@pytest.mark.unit
class TestUserPasswordUpdateSchema:
    """Юнит-тесты для схемы обновления пароля (UserPasswordUpdateSchema)."""

    def test_init_with_mismatched_passwords_raises_invalid_input(self):
        """Тест с несовпадающими новым и подтвержденным паролями должен вызвать исключение."""
        # Arrange
        data = {
            "current_password": "OldPassword123",
            "new_password": "NewPassword123",
            "confirm_password": "DifferentPassword123"
        }

        # Act & Assert
        with pytest.raises(InvalidInputException) as exc_info:
            UserPasswordUpdateSchema(**data)

        assert exc_info.value.field_name == "подтверждение пароля"
        assert "совпадение с новым паролем" in exc_info.value.expected_format

    def test_init_with_same_new_and_current_password_raises_invalid_input(self):
        """Тест, где новый пароль совпадает с текущим, должен вызвать исключение."""
        # Arrange
        data = {
            "current_password": "Password123",
            "new_password": "Password123",
            "confirm_password": "Password123"
        }

        # Act & Assert
        with pytest.raises(InvalidInputException) as exc_info:
            UserPasswordUpdateSchema(**data)

        assert exc_info.value.field_name == "новый пароль"
        assert "отличный от текущего" in exc_info.value.expected_format

    def test_init_with_empty_current_password_raises_missing_field(self):
        """Тест с пустым текущим паролем должен вызвать исключение."""
        # Arrange
        data = {"current_password": "", "new_password": "NewPassword123",
                "confirm_password": "NewPassword123"}

        # Act & Assert
        with pytest.raises(MissingRequiredFieldException) as exc_info:
            UserPasswordUpdateSchema(**data)

        assert "текущий пароль" in exc_info.value.missing_fields

    def test_init_with_empty_new_password_raises_missing_field(self):
        """Тест с пустым новым паролем должен вызвать исключение."""
        # Arrange
        data = {"current_password": "OldPassword123",
                "new_password": "", "confirm_password": ""}

        # Act & Assert
        with pytest.raises(MissingRequiredFieldException) as exc_info:
            UserPasswordUpdateSchema(**data)

        assert "новый пароль" in exc_info.value.missing_fields


@pytest.mark.unit
class TestPasswordGeneration:
    """Юнит-тесты для функций генерации и валидации паролей."""

    @pytest.mark.parametrize("length", [LENGTH_GENERATED_PASSWORD, 15, 32])
    def test_generate_password_returns_password_of_correct_length_and_strength(self, length):
        """Тест генерации пароля заданной длины, проверяющий его соответствие требованиям."""
        # Arrange (length from parametrize)

        # Act
        password = generate_password(length)

        # Assert
        assert len(password) == length
        assert validate_strong_password(password) == password

    def test_validate_strong_password_with_valid_password_succeeds(self):
        """Тест валидации сильного пароля с корректным входным значением."""
        # Arrange
        password = "ValidPassword123"

        # Act
        result = validate_strong_password(password)

        # Assert
        assert result == password

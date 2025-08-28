import pytest

from src.auth.schemas import (UserPasswordUpdateSchema, UserRegisterSchema,
                              generate_password, validate_strong_password)
from src.common.constants import LENGTH_GENERATED_PASSWORD
from src.core.config import settings
from src.core.exception import (InvalidInputException,
                                MissingRequiredFieldException)


class TestUserRegisterSchema:
    """Тесты схемы регистрации пользователя."""

    def test_auto_generate_password(self):
        """Тест автогенерации пароля."""
        data = {"username": "testuser"}
        schema = UserRegisterSchema(**data)

        assert schema.username == "testuser"
        assert len(schema.password) >= 8
        assert any(c.isupper() for c in schema.password)
        assert any(c.islower() for c in schema.password)
        assert sum(c.isdigit() for c in schema.password) >= 3

    @pytest.mark.parametrize(
        "password, expected_part_of_message",
        [
            ("123", f"минимум {settings.PASSWORD_MIN_LENGTH} символов"),
            ("password123", "заглавными буквами"),
            ("PASSWORD123", "строчными буквами"),
            ("Password", "цифрами"),
            ("Password 123", "без пробелов"),
        ]
    )
    def test_invalid_password_validation(self, password, expected_part_of_message):
        """Тест валидации невалидных паролей."""
        with pytest.raises(InvalidInputException) as exc_info:
            UserRegisterSchema(username="testuser", password=password)

        assert exc_info.value.field_name == "пароль"
        assert expected_part_of_message in exc_info.value.expected_format


class TestUserPasswordUpdateSchema:
    """Тесты схемы обновления пароля."""

    def test_password_mismatch_raises_error(self):
        """Тест несовпадающих паролей."""
        with pytest.raises(InvalidInputException) as exc_info:
            UserPasswordUpdateSchema(
                current_password="OldPassword123",
                new_password="NewPassword123",
                confirm_password="DifferentPassword123"
            )

        assert exc_info.value.field_name == "подтверждение пароля"
        assert exc_info.value.expected_format == "совпадение с новым паролем"

    def test_same_password_raises_error(self):
        """Тест когда новый пароль совпадает с текущим."""
        with pytest.raises(InvalidInputException) as exc_info:
            UserPasswordUpdateSchema(
                current_password="Password123",
                new_password="Password123",
                confirm_password="Password123"
            )

        assert exc_info.value.field_name == "новый пароль"
        assert "отличный от текущего" in exc_info.value.expected_format

    def test_empty_current_password_raises_error(self):
        """Тест пустого текущего пароля."""
        with pytest.raises(MissingRequiredFieldException) as exc_info:
            UserPasswordUpdateSchema(
                current_password="",
                new_password="NewPassword123",
                confirm_password="NewPassword123"
            )

        assert exc_info.value.error_code == "MISSING_REQUIRED_FIELD"
        assert "текущий пароль" in exc_info.value.missing_fields

    def test_empty_new_password_raises_error(self):
        """Тест пустого нового пароля."""
        with pytest.raises(MissingRequiredFieldException) as exc_info:
            UserPasswordUpdateSchema(
                current_password="OldPassword123",
                new_password="",
                confirm_password=""
            )

        assert exc_info.value.error_code == "MISSING_REQUIRED_FIELD"
        assert "новый пароль" in exc_info.value.missing_fields


class TestPasswordGeneration:
    """Тесты генерации паролей."""

    @pytest.mark.parametrize("length, expected", [
        (LENGTH_GENERATED_PASSWORD, LENGTH_GENERATED_PASSWORD),
        (15, 15),
        (32, 32)
    ])
    def test_generate_password_length(self, length, expected):
        """Тест генерации пароля разной длины."""
        password = generate_password(length)

        assert len(password) == expected
        assert any(c.islower() for c in password)
        assert any(c.isupper() for c in password)
        assert sum(c.isdigit() for c in password) >= 3

    def test_validate_strong_password_valid(self):
        """Тест валидации сильного пароля."""
        password = "ValidPassword123"
        result = validate_strong_password(password)
        assert result == password

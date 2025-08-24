import pytest
from pydantic import ValidationError

from src.auth.schemas import (UserPasswordUpdateSchema, UserRegisterSchema,
                              generate_password, validate_strong_password)
from src.constants import LENGTH_GENERATED_PASSWORD


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

    def test_password_validation_too_short(self):
        """Тест валидации короткого пароля."""
        with pytest.raises(ValueError) as exc_info:
            UserRegisterSchema(username="testuser", password="123")

        assert "Длина пароля должна быть не менее 8 символов" in str(
            exc_info.value)

    def test_password_validation_no_uppercase(self):
        """Тест валидации пароля без заглавных букв."""
        with pytest.raises(ValueError) as exc_info:
            UserRegisterSchema(username="testuser", password="password123")

        assert "заглавную букву" in str(exc_info.value)

    def test_password_validation_no_lowercase(self):
        """Тест валидации пароля без строчных букв."""
        with pytest.raises(ValueError) as exc_info:
            UserRegisterSchema(username="testuser", password="PASSWORD123")

        assert "строчную букву" in str(exc_info.value)

    def test_password_validation_no_digit(self):
        """Тест валидации пароля без цифр."""
        with pytest.raises(ValueError) as exc_info:
            UserRegisterSchema(username="testuser", password="Password")

        assert "цифру" in str(exc_info.value)

    def test_password_validation_with_spaces(self):
        """Тест валидации пароля с пробелами."""
        with pytest.raises(ValueError) as exc_info:
            UserRegisterSchema(username="testuser", password="Password 123")

        assert "пробелы" in str(exc_info.value)


class TestUserPasswordUpdateSchema:
    """Тесты схемы обновления пароля."""

    def test_valid_password_update(self):
        """Тест валидного обновления пароля."""
        data = {
            "current_password": "OldPassword123",
            "new_password": "NewPassword123",
            "confirm_password": "NewPassword123"
        }
        schema = UserPasswordUpdateSchema(**data)

        assert schema.current_password == "OldPassword123"
        assert schema.new_password == "NewPassword123"
        assert schema.confirm_password == "NewPassword123"

    def test_passwords_dont_match(self):
        """Тест несовпадающих паролей."""
        with pytest.raises(ValidationError) as exc_info:
            UserPasswordUpdateSchema(
                current_password="OldPassword123",
                new_password="NewPassword123",
                confirm_password="DifferentPassword123"
            )

        assert "не совпадают" in str(exc_info.value)

    def test_new_password_same_as_current(self):
        """Тест когда новый пароль совпадает с текущим."""
        with pytest.raises(ValidationError) as exc_info:
            UserPasswordUpdateSchema(
                current_password="Password123",
                new_password="Password123",
                confirm_password="Password123"
            )

        assert "не должен совпадать с текущим" in str(exc_info.value)

    def test_empty_current_password(self):
        """Тест пустого текущего пароля."""
        with pytest.raises(ValidationError) as exc_info:
            UserPasswordUpdateSchema(
                current_password="",
                new_password="NewPassword123",
                confirm_password="NewPassword123"
            )

        assert "Требуется текущий пароль" in str(exc_info.value)

    def test_empty_new_password(self):
        """Тест пустого нового пароля."""
        with pytest.raises(ValidationError) as exc_info:
            UserPasswordUpdateSchema(
                current_password="OldPassword123",
                new_password="",
                confirm_password=""
            )

        assert "не ввели новый пароль" in str(exc_info.value)


class TestPasswordGeneration:
    """Тесты генерации паролей."""

    def test_generate_password_default_length(self):
        """Тест генерации пароля стандартной длины."""
        password = generate_password()

        assert len(password) == LENGTH_GENERATED_PASSWORD
        assert any(c.islower() for c in password)
        assert any(c.isupper() for c in password)
        assert sum(c.isdigit() for c in password) >= 3

    def test_generate_password_custom_length(self):
        """Тест генерации пароля заданной длины."""
        password = generate_password(15)

        assert len(password) == 15
        assert any(c.islower() for c in password)
        assert any(c.isupper() for c in password)
        assert sum(c.isdigit() for c in password) >= 3

    def test_validate_strong_password_valid(self):
        """Тест валидации сильного пароля."""
        password = "ValidPassword123"
        result = validate_strong_password(password)

        assert result == password

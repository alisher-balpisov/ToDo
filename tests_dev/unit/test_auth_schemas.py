import pytest
from pydantic import ValidationError

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

    @pytest.mark.parametrize("kwargs, expected_exception", [
        # Тест валидации короткого пароля.
        ({"password": "123"},
         InvalidInputException(
            "пароль", "короткий пароль", f"минимум {settings.PASSWORD_MIN_LENGTH} символов")),

        # Тест валидации пароля без заглавных букв.
        ({"password": "password123"},
         InvalidInputException(
            "пароль", "пароль без заглавных", "пароль с заглавными буквами")),

        # Тест валидации пароля без строчных букв.
        ({"password": "PASSWORD123"},
         InvalidInputException(
            "пароль", "пароль без строчных", "пароль со строчными буквами")),

        # Тест валидации пароля без цифр.
        ({"password": "Password"},
         InvalidInputException(
            "пароль", "пароль без цифр", "пароль с цифрами")),

        # Тест валидации пароля с пробелами.
        ({"password": "Password 123"},
         InvalidInputException(
            "пароль", "пароль с пробелами", "пароль без пробелов"))
    ])
    def test_password_validation(self, kwargs, expected_exception):
        """Тест валидации пароля."""
        with pytest.raises(Exception) as exc_info:
            UserRegisterSchema(username="testuser", **kwargs)

        assert expected_exception == exc_info.value


class TestUserPasswordUpdateSchema:
    """Тесты схемы обновления пароля."""


@pytest.mark.parametrize("kwargs, expected_exception", [
    # Тест несовпадающих паролей
    ({
        "current_password": "OldPassword123",
        "new_password": "NewPassword123",
        "confirm_password": "DifferentPassword123",
    }, InvalidInputException(
        "подтверждение пароля", "не совпадает", "совпадение с новым паролем")),

    # Тест когда новый пароль совпадает с текущим
    ({
        "current_password": "Password123",
        "new_password": "Password123",
        "confirm_password": "Password123",
    }, InvalidInputException(
        "новый пароль", "совпадает со старым", "отличный от текущего пароль")),

    # Тест пустого текущего пароля
    ({
        "current_password": "",
        "new_password": "NewPassword123",
        "confirm_password": "NewPassword123",
    }, MissingRequiredFieldException("текущий пароль")),

    # Тест пустого нового пароля
    ({
        "current_password": "OldPassword123",
        "new_password": "",
        "confirm_password": "",
    }, MissingRequiredFieldException("новый пароль")),
])
def test_password_update_validation(kwargs, expected_exception):
    """Тесты валидации обновления пароля."""
    with pytest.raises(Exception) as exc_info:
        UserPasswordUpdateSchema(**kwargs)

    assert expected_exception == exc_info.value


class TestPasswordGeneration:
    """Тесты генерации паролей."""

    @pytest.mark.parametrize("length, expected", [
        (LENGTH_GENERATED_PASSWORD, LENGTH_GENERATED_PASSWORD),
        (15, 15),
        (32, 32)
    ])
    def test_generate_password_default_length(self, length, expected):
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

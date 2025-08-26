import secrets
import string

from pydantic import BaseModel, Field, field_validator, model_validator

from src.common.constants import (LENGTH_GENERATED_PASSWORD,
                                  USERNAME_MAX_LENGTH, USERNAME_MIN_LENGTH)
from src.core.config import settings
from src.core.exception import (InvalidInputException,
                                MissingRequiredFieldException)


def generate_password(length: int = LENGTH_GENERATED_PASSWORD) -> str:
    """
    Сгенерируйте случайный надежный пароль,
    состоящий как минимум из одной строчной буквы,
    одной прописной буквы и трех цифр.
     """
    if length < settings.PASSWORD_MIN_LENGTH:
        raise InvalidInputException(
            "пароль", "короткий пароль", f"минимум {settings.PASSWORD_MIN_LENGTH} символов")
    while True:
        password = "".join(secrets.choice(
            string.ascii_letters + string.digits) for _ in range(length))
        if (
            any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and sum(c.isdigit() for c in password) >= 3
        ):
            return password


def validate_strong_password(v: str) -> str:
    """Проверка сложности пароля."""
    if not v or len(v) < settings.PASSWORD_MIN_LENGTH:
        raise InvalidInputException(
            "пароль", "короткий пароль", f"минимум {settings.PASSWORD_MIN_LENGTH} символов")
    if any(c.isspace() for c in v):
        raise InvalidInputException(
            "пароль", "пароль с пробелами", "пароль без пробелов")
    if not any(c.isdigit() for c in v):
        raise InvalidInputException(
            "пароль", "пароль без цифр", "пароль с цифрами")
    if not any(c.isupper() for c in v):
        raise InvalidInputException(
            "пароль", "пароль без заглавных", "пароль с заглавными буквами")
    if not any(c.islower() for c in v):
        raise InvalidInputException(
            "пароль", "пароль без строчных", "пароль со строчными буквами")
    return v


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    type: str


class UserRegisterSchema(BaseModel):
    username: str = Field(min_length=USERNAME_MIN_LENGTH,
                          max_length=USERNAME_MAX_LENGTH)
    password: str | None = None
    is_password_generated: bool = False

    def __init__(self, **data):
        super().__init__(**data)
        if not self.password or not self.password.strip():
            object.__setattr__(self, "password", generate_password())
            object.__setattr__(self, "is_password_generated", True)
        else:
            validate_strong_password(self.password)


class UserPasswordUpdateSchema(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v.strip():
            raise MissingRequiredFieldException("новый пароль")
        return validate_strong_password(v)

    @field_validator("current_password")
    @classmethod
    def password_required(cls, v):
        if not v.strip():
            raise MissingRequiredFieldException("текущий пароль")
        return v

    @field_validator("confirm_password")
    @classmethod
    def validate_confirm_password(cls, v: str) -> str:
        if not v.strip():
            raise MissingRequiredFieldException("подтверждение пароля")
        return v

    @model_validator(mode="after")
    def check_passwords_match_and_not_same(self):
        if self.new_password != self.confirm_password:
            raise InvalidInputException(
                "подтверждение пароля", "не совпадает", "совпадение с новым паролем")
        if self.new_password == self.current_password:
            raise InvalidInputException(
                "новый пароль", "совпадает со старым", "отличный от текущего пароль")
        return self

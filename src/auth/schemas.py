import secrets
import string
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator

from src.constants import (LENGTH_GENERATED_PASSWORD, USERNAME_MAX_LENGTH,
                           USERNAME_MIN_LENGTH)
from src.core.config import settings


def generate_password(length: int = LENGTH_GENERATED_PASSWORD) -> str:
    """
    Сгенерируйте случайный надежный пароль,
    состоящий как минимум из одной строчной буквы,
    одной прописной буквы и трех цифр.
     """
    if length < settings.PASSWORD_MIN_LENGTH:
        raise ValueError(
            f"Минимальная длина пароля должна быть {settings.PASSWORD_MIN_LENGTH} символов")
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
        raise ValueError(
            "Длина пароля должна быть не менее 8 символов")
    if any(c.isspace() for c in v):
        raise ValueError(
            "Пароль не должен содержать пробелы")
    if not any(c.isdigit() for c in v):
        raise ValueError(
            "Пароль должен содержать хотя бы одну цифру")
    if not any(c.isupper() for c in v):
        raise ValueError(
            "Пароль должен содержать хотя бы одну заглавную букву")
    if not any(c.islower() for c in v):
        raise ValueError(
            "Пароль должен содержать хотя бы одну строчную букву")
    return v


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenType(Enum):
    BEARER = "Bearer"
    REFRESH = "Refresh"


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
            raise ValueError("Вы не ввели новый пароль")
        return validate_strong_password(v)

    @field_validator("current_password")
    @classmethod
    def password_required(cls, v):
        if not v.strip():
            raise ValueError("Требуется текущий пароль")
        return v

    @field_validator("confirm_password")
    @classmethod
    def validate_confirm_password(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Подтвердите новый пароль")
        return v

    @model_validator(mode="after")
    def check_passwords_match_and_not_same(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Пароли не совпадают")
        if self.new_password == self.current_password:
            raise ValueError("Новый пароль не должен совпадать с текущим")
        return self

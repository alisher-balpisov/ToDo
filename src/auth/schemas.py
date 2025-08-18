import secrets
import string

from pydantic import BaseModel, Field, field_validator, model_validator

from src.core.database import UsernameStr


def generate_password(length: int = 10) -> str:
    """
    Сгенерируйте случайный надежный пароль,
    состоящий как минимум из одной строчной буквы,
    одной прописной буквы и трех цифр.
     """
    if length < 8:
        raise ValueError("Минимальная длина пароля должна быть 8 символов")
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
    if not v or len(v) < 8:
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
    token_type: str


class TokenDataSchema(BaseModel):
    username: UsernameStr | None = None


class UserRegisterSchema(BaseModel):
    username: UsernameStr
    password: str = Field(default_factory=generate_password)

    @field_validator("password", mode="after")
    @classmethod
    def password_required(cls, v):
        return v if v and v.strip() else generate_password()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_strong_password(v)


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

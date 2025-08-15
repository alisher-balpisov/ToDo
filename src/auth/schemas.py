import secrets
import string

from pydantic import BaseModel, field_validator

from src.core.database import UsernameStr


def generate_password(length: int = 10) -> str:
    """
    Сгенерируйте случайный надежный пароль,
    состоящий как минимум из одной строчной буквы,
    одной прописной буквы и трех цифр.
     """
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
    password: str = ""

    @field_validator("password", mode="before")
    @classmethod
    def password_required(cls, v):
        return v if isinstance(v, str) and v.strip() else generate_password()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_strong_password(v)


class UserPasswordUpdateSchema(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Вы не ввели новый пароль")
        return validate_strong_password(v)

    @field_validator("current_password", mode="before")
    @classmethod
    def password_required(cls, v):
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Требуется текущий пароль")
        return v

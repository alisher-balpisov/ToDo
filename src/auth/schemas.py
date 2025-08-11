import secrets
import string

from pydantic import BaseModel, field_validator

from src.core.database import UsernameStr


def generate_password() -> str:
    """
    Сгенерируйте случайный надежный пароль,
    состоящий как минимум из одной строчной буквы,
    одной прописной буквы и трех цифр.
     """
    alphanumeric = string.ascii_letters + string.digits
    while True:
        password = "".join(secrets.choice(alphanumeric) for i in range(10))
        if (
            any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and sum(c.isdigit() for c in password) >= 3
        ):
            break
    return password


def validate_strong_password(v: str) -> str:
    """Проверка сложности пароля."""
    if not v or len(v) < 8:
        raise ValueError("Длина пароля должна составлять не менее 8 символов")
    if not any(c.isdigit() for c in v):
        raise ValueError("Пароль должен содержать хотя бы одну цифру")
    if not any(c.isupper() for c in v) or not any(c.islower() for c in v):
        raise ValueError(
            "Пароль должен содержать как заглавные, так и строчные буквы")
    return v


class TokenSchema(BaseModel):
    access_token: str
    token_type: str


class TokenDataSchema(BaseModel):
    username: UsernameStr | None = None


class UserRegisterSchema(BaseModel):
    username: UsernameStr
    password: str = ""

    @field_validator("username")
    @classmethod
    def username_required(cls, v):
        """Убедитесь, что поле не пусто."""
        if not v:
            raise ValueError("Строка username не должна быть пустой'")
        return v

    @field_validator("password", mode="before")
    @classmethod
    def password_required(cls, v):
        if not v:
            password = generate_password()
        else:
            password = v
        return password

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
        if not v:
            raise ValueError("Вы не ввели новый пароль")
        return validate_strong_password(v)

    @field_validator("current_password", mode="before")
    @classmethod
    def password_required(cls, v):
        if not v:
            raise ValueError("Требуется текущий пароль")
        return v

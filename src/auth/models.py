import secrets
import string
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy import Boolean, Column, Integer, LargeBinary, String

from src.core.config import TODO_JWT_ALG, TODO_JWT_EXP, TODO_JWT_SECRET
from src.core.database import Base, UsernameStr


def generate_password():
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


def get_hash_password(password: str):
    pw = bytes(password, "utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw, salt)


class ToDoUser(Base):
    __repr_attrs__ = ['username']

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True)
    password = Column(LargeBinary, nullable=True)
    disabled = Column(Boolean, default=False)

    def verify_password(self, password: str) -> bool:
        if not password or not self.password:
            return False
        return bcrypt.checkpw(password.encode("utf-8"), self.password)

    def set_password(self, password: str) -> None:
        """Установите новый пароль для пользователя."""
        if not password:
            raise ValueError("Password cannot be empty")
        self.password = get_hash_password(password)

    @property
    def token(self) -> str:
        now = datetime.now(timezone.utc).astimezone()
        exp = now + timedelta(minutes=TODO_JWT_EXP)
        data = {
            'exp': exp,
            'email': self.email
        }
        return jwt.encode(data, TODO_JWT_SECRET, algorithm=TODO_JWT_ALG)


class TokenSchema(BaseModel):
    access_token: str
    token_type: str


class TokenDataSchema(BaseModel):
    username: UsernameStr | None = None


class UserBaseSchema(BaseModel):
    username: UsernameStr

    @field_validator("username")
    @classmethod
    def username_required(cls, v):
        """Убедитесь, что поле не пусто."""
        if not v:
            raise ValueError("Строка username не должна быть пустой'")
        return v


class UserLoginSchema(UserBaseSchema):
    password: str

    @field_validator("password")
    @classmethod
    def password_required(cls, v):
        """Убедитесь, что поле для ввода пароля не пустое."""
        if not v:
            raise ValueError("Строка password не должна быть пустой")
        return v


class UserRegisterSchema(UserLoginSchema):
    password: str = ""

    @field_validator("password", mode="before")
    @classmethod
    def password_required(cls, v):
        password = v or generate_password()
        return get_hash_password(password)


class UserPasswordUpdateSchema(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v):
        """Проверка сложности нового пароля."""
        if not v or len(v) < 8:
            raise ValueError(
                "Длина пароля должна составлять не менее 8 символов")
        if not any(c.isdigit() for c in v):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        if not (any(c.isupper() for c in v) and any(c.islower() for c in v)):
            raise ValueError(
                "Пароль должен содержать как заглавные, так и строчные буквы")
        return v

    @field_validator("current_password")
    @classmethod
    def password_required(cls, v):
        if not v:
            raise ValueError("Требуется текущий пароль")
        return v

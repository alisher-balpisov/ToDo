from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt
from sqlalchemy import Boolean, Column, Integer, LargeBinary, String

from src.constants import DEFAULT_ENCODING
from src.core.config import TODO_JWT_ALG, TODO_JWT_EXP, TODO_JWT_SECRET
from src.core.database import Base


def get_hash_password(password: str):
    pw = bytes(password, DEFAULT_ENCODING)
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
        return bcrypt.checkpw(password.encode(DEFAULT_ENCODING), self.password)

    def set_password(self, password: str) -> None:
        """Установите новый пароль для пользователя."""
        if not password:
            raise ValueError("Password cannot be empty")
        self.password = get_hash_password(password)

    @property
    def get_token(self) -> str:
        now = datetime.now(timezone.utc).astimezone()
        exp = now + timedelta(minutes=TODO_JWT_EXP)
        data = {
            'exp': exp,
            'sub': self.username
        }
        return jwt.encode(data, TODO_JWT_SECRET, algorithm=TODO_JWT_ALG)

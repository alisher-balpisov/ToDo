from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt
from sqlalchemy import Boolean, Column, DateTime, Integer, LargeBinary, String

from src.common.constants import USERNAME_MAX_LENGTH
from src.common.enums import TokenType
from src.core.config import settings
from src.core.database import Base
from src.core.exception import MissingRequiredFieldException

from .utils import hash_password


class User(Base):
    __repr_attrs__ = ['username', 'email']

    id = Column(Integer, primary_key=True)
    username = Column(String(USERNAME_MAX_LENGTH),
                      unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True)
    password_hash = Column(LargeBinary, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Счётчик неудачных попыток входа
    failed_login_attempts = Column(Integer, default=0)
    # Время, до которого пользователь заблокирован
    locked_until = Column(DateTime, nullable=True)

    last_login = Column(DateTime, nullable=True)

    def utc_now_naive():
        return datetime.now(timezone.utc).replace(tzinfo=None)

    created_at = Column(DateTime, default=utc_now_naive)
    updated_at = Column(DateTime, default=utc_now_naive,
                        onupdate=utc_now_naive)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.failed_login_attempts is None:
            self.failed_login_attempts = 0

    def verify_password(self, password: str) -> bool:
        """Проверка пароля с защитой от брутфорса."""
        if not password:
            return False

        now = datetime.now(timezone.utc)

        if self.is_locked:
            return False

        is_valid = bcrypt.checkpw(
            password.encode(settings.DEFAULT_ENCODING), self.password_hash)
        if is_valid:
            self.failed_login_attempts = 0
            self.last_login = now
            self.locked_until = None
        else:
            # Увеличение счетчика неудачных попыток
            self.failed_login_attempts += 1
            if self.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                self.locked_until = now + timedelta(
                    minutes=settings.LOCKOUT_TIME_MINUTES)

        return is_valid

    @property
    def is_locked(self) -> bool:
        """Проверка блокировки аккаунта."""
        if not self.locked_until:
            return False
        return datetime.now(timezone.utc) < self.locked_until

    def set_password(self, password: str) -> None:
        """Установите новый пароль для пользователя."""
        if not password or not password.strip():
            raise MissingRequiredFieldException("новый пароль")
        self.password_hash = hash_password(password)

    def token(self, expiration: int = settings.JWT_EXPIRATION_MINUTES, type: TokenType = TokenType.ACCESS) -> str:
        """Создание JWT токена."""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=expiration)
        payload = {
            'sub': self.username,
            'user_id': self.id,
            'exp': expire,
            'iat': now,
            'type': type
        }
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

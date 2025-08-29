import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.common.enums import TokenType
from src.core.config import settings
from src.core.database import get_db
from src.core.decorators import service_method
from src.core.exception import (AuthenticationException,
                                InvalidCredentialsException,
                                ResourceNotFoundException,
                                TokenExpiredException, ValidationException)

from .models import User
from .utils import hash_password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


async def get_user_by_id(session, user_id: int) -> User | None:
    """Возвращает имя пользователя на основе заданного id."""
    return (await session.execute(select(User).where(User.id == user_id))).scalar_one_or_none()


async def get_user_by_username(session, username: str) -> User | None:
    """Возвращает объект User, основанный на username пользователя."""
    return (await session.execute(select(User).where(User.username == username))).scalar_one_or_none()


async def get_user_by_email(session, email: str) -> User | None:
    """Возвращает объект User, основанный на email пользователя."""
    return (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()


def verify_token(token: str, expected_type: TokenType | None = None) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": True,
                     "verify_iat": True,
                     "verify_signature": True}
        )

        if "sub" not in payload or "type" not in payload:
            raise InvalidCredentialsException("некорректная структура токена")

        iat = payload.get("iat")
        if iat and isinstance(iat, (int, float)):
            if datetime.fromtimestamp(iat, timezone.utc) > datetime.now(timezone.utc):
                raise InvalidCredentialsException("токен выдан в будущем")

        actual_type = payload.get("type")
        if expected_type and actual_type != expected_type:
            raise InvalidCredentialsException(
                f"Ожидался токен типа '{expected_type}', получен '{actual_type}'")
        return payload

    except ExpiredSignatureError:
        raise TokenExpiredException("access")
    except JWTError:
        raise InvalidCredentialsException()


@service_method()
async def register_service(
        session,
        username: str,
        password: str,
        email: str | None = None
) -> None:
    USER_DATA_ERROR = ValidationException(
        "Пользователь с такими данными уже существует или введенные данные некорректны")
    if await get_user_by_username(session=session, username=username):
        raise USER_DATA_ERROR
    if email is not None and await get_user_by_email(session=session, email=email):
        raise USER_DATA_ERROR

    password_hash = hash_password(password)

    new_user = User(
        username=username,
        password_hash=password_hash
    )
    session.add(new_user)


@service_method()
async def login_service(
        session,
        username: str,
        password: str
) -> tuple[str, str]:
    user = await get_user_by_username(session=session, username=username)
    if user is None:
        raise InvalidCredentialsException(username)

    if user.is_locked:
        raise AuthenticationException(
            f"Учётная запись временно заблокирована до {user.locked_until.isoformat()}")
    if not user.verify_password(password):
        await session.commit()
        raise InvalidCredentialsException(username)

    access_token = user.token(
        settings.JWT_EXPIRATION_MINUTES, TokenType.ACCESS)
    refresh_token = user.token(
        settings.JWT_REFRESH_EXPIRATION_MINUTES, TokenType.REFRESH)
    return access_token, refresh_token


async def get_user_or_raise(session, username: str):
    """Проверяет состояние пользователя и выбрасывает исключения при проблемах."""
    user = await get_user_by_username(session, username)
    if user is None:
        raise ResourceNotFoundException("Пользователь", username)

    if not user.is_active:
        raise AuthenticationException("Учетная запись пользователя отключена")

    if user.is_locked:
        raise AuthenticationException(
            f"Учётная запись временно заблокирована до {user.locked_until.isoformat()}")
    return user


async def refresh_service(
        session,
        token: str
):
    payload = verify_token(token, TokenType.REFRESH)
    username = payload.get("sub")
    user = await get_user_or_raise(session, username)

    access_token = user.token(
        settings.JWT_EXPIRATION_MINUTES, TokenType.ACCESS)
    refresh_token = user.token(
        settings.JWT_REFRESH_EXPIRATION_MINUTES, TokenType.REFRESH)
    return access_token, refresh_token


logger = logging.getLogger(__name__)


async def get_current_user(
        session: Annotated[Session, Depends(get_db)],
        token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    logger.debug("get_current_user called with token=%s", token)

    payload = verify_token(token, TokenType.ACCESS)
    logger.debug("verify_token result=%s", payload)

    username = payload.get("sub")
    logger.debug("extracted username=%s", username)

    user = await get_user_or_raise(session, username)
    logger.debug("user fetched=%s", user.username if user else None)

    return user


@service_method()
async def change_password_service(
        session,
        current_user: User,
        current_password: str,
        new_password: str
) -> None:
    if not current_user.verify_password(current_password):
        raise InvalidCredentialsException()
    current_user.set_password(new_password)

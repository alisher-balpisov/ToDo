from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt

from src.auth.schemas import TokenType
from src.common.utils import handler, transactional
from src.core.config import settings
from src.core.database import DbSession
from src.exceptions import USER_NOT_FOUND

from .models import User
from .utils import hash_password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def get_user_by_id(session, user_id: int) -> User | None:
    """Возвращает имя пользователя на основе заданного id."""
    return session.query(User).filter(User.id == user_id).one_or_none()


def get_user_by_username(session, username: str) -> User | None:
    """Возвращает объект User, основанный на username пользователя."""
    return session.query(User).filter(User.username == username).one_or_none()


def get_user_by_email(session, email: str) -> User | None:
    """Возвращает объект User, основанный на email пользователя."""
    return session.query(User).filter(User.email == email).one_or_none()


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

        iat = payload.get("iat")
        if iat and datetime.fromtimestamp(iat, timezone.utc) > datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"msg": "Токен выдан в будущем"}
            )

        if expected_type and payload.get("type") != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "msg": f"Ожидался токен типа '{expected_type}', получен '{payload.get('type')}'"}
            )
        return payload

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"msg": "Токен истек"}
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"msg": "Недействительный токен"}
        )


@handler
@transactional
def register_service(
        session,
        username: str,
        password: str,
        email: str | None = None
) -> None:
    if get_user_by_username(session=session, username=username):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"msg": "Пользователь с таким username уже существует."},
        )
    if email is not None and get_user_by_email(session=session, email=email):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"msg": "Пользователь с таким email уже существует."},
        )

    password_hash = hash_password(password)

    new_user = User(
        username=username,
        password_hash=password_hash
    )
    session.add(new_user)


@handler
@transactional
def login_service(
        session,
        username: str,
        password: str
) -> tuple[str, str]:
    user = get_user_by_username(session=session, username=username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"msg": "Неверное имя пользователя или пароль"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "msg": f"Аккаунт заблокирован до {user.locked_until.isoformat()}"},
        )
    if not user.verify_password(password):
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"msg": "Неверное имя пользователя или пароль"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = user.token(
        settings.JWT_EXPIRATION_MINUTES, TokenType.ACCESS)
    refresh_token = user.token(
        settings.JWT_REFRESH_EXPIRATION_MINUTES, TokenType.REFRESH)
    return access_token, refresh_token


def check_user_or_raise(user: User | None) -> None:
    """Проверяет состояние пользователя и выбрасывает исключения при проблемах."""
    if not user:
        raise USER_NOT_FOUND

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"msg": "Учетная запись пользователя отключена"}
        )

    if user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail={"msg": "Учетная запись временно заблокирована"}
        )


def refresh_service(
        session,
        token: str
):
    payload = verify_token(token, TokenType.REFRESH)
    username = payload.get("sub")
    user = get_user_by_username(session, username)
    check_user_or_raise(user)

    access_token = user.token(
        settings.JWT_EXPIRATION_MINUTES, TokenType.ACCESS)
    refresh_token = user.token(
        settings.JWT_REFRESH_EXPIRATION_MINUTES, TokenType.REFRESH)
    return access_token, refresh_token


def get_current_user(
        session: DbSession,
        token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    payload = verify_token(token, TokenType.ACCESS)
    username = payload.get("sub")
    user = get_user_by_username(session, username)
    check_user_or_raise(user)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def credentials_exception():
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"msg": "Не удалось подтвердить учетные данные"},
        headers={"WWW-Authenticate": "Bearer"}
    )

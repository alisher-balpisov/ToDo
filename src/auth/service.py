from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from src.core.config import settings
from src.core.database import DbSession
from src.exceptions import user_not_found

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


def register_service(
        session,
        username: str,
        password: str
) -> None:
    """Создает нового пользователя ToDoUser."""
    user = get_user_by_username(session=session, username=username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[{"msg": "Пользователь с таким username уже существует."}],
        )
    password_hash = hash_password(password)

    new_user = User(
        username=username,
        password_hash=password_hash
    )
    session.add(new_user)
    session.commit()


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
    session.commit()
    access_token = user.token(settings.JWT_EXPIRATION_MINUTES)
    refresh_token = user.token(settings.JWT_REFRESH_EXPIRATION_MINUTES)
    return access_token, refresh_token


def credentials_exception():
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=[{"msg": "Не удалось подтвердить учетные данные"}],
        headers={"WWW-Authenticate": "Bearer"}
    )


def verify_token(token: str) -> dict:
    """Проверка JWT токена."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # Проверка типа токена
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"msg": "Неправильный тип токена"}
            )

        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"msg": "Недействительный или просроченный токен"},
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
        session: DbSession,
        token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    """Получение текущего пользователя."""
    payload = verify_token(token)
    username = payload.get("sub")

    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"msg": "Недействительный токен"}
        )

    user = get_user_by_username(session, username)
    if not user:
        raise user_not_found(user)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"msg": "Учетная запись пользователя отключена"}
        )

    if user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail={
                "msg": "Учетная запись временно заблокирована из-за неудачных попыток входа в систему"}
        )

    return user

CurrentUser = Annotated[User, Depends(get_current_user)]

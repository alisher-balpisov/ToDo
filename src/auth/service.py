from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from src.core.config import settings
from src.core.database import DbSession

from .models import ToDoUser, get_hash_password
from .schemas import TokenDataSchema

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def get_user_by_id(session, user_id: int) -> ToDoUser | None:
    """Возвращает имя пользователя на основе заданного id."""
    return session.query(ToDoUser).filter(ToDoUser.id == user_id).one_or_none()


def get_user_by_username(session, username: str) -> ToDoUser | None:
    """Возвращает объект User, основанный на username пользователя."""
    return session.query(ToDoUser).filter(ToDoUser.username == username).one_or_none()


def get_user_by_email(session, email: str) -> ToDoUser | None:
    """Возвращает объект User, основанный на email пользователя."""
    return session.query(ToDoUser).filter(ToDoUser.email == email).one_or_none()


def register_service(*, session, username: str, password: str) -> ToDoUser:
    """Создает нового пользователя ToDoUser."""
    user = get_user_by_username(session=session, username=username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[
                {
                    "msg": "Пользователь с таким username уже существует.",
                    "loc": ["username"],
                    "type": "value_error",
                }
            ],
        )
    hashed_password = get_hash_password(password)

    new_user = ToDoUser(
        username=username,
        password=hashed_password
    )
    session.add(new_user)
    session.commit()


def credentials_exception():
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=[{"msg": "Не удалось подтвердить учетные данные"}],
        headers={"WWW-Authenticate": "Bearer"}
    )


def get_current_user(
        session: DbSession,
        token: Annotated[str, Depends(oauth2_scheme)]
) -> ToDoUser:
    try:
        payload = jwt.decode(token, settings.TODO_JWT_SECRET, algorithms=[settings.TODO_JWT_ALG])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception()
        token_data = TokenDataSchema(username=username)
    except JWTError:
        raise credentials_exception()

    user = get_user_by_username(
        session=session, username=token_data.username)
    if user is None:
        raise credentials_exception()
    return user


CurrentUser = Annotated[ToDoUser, Depends(get_current_user)]

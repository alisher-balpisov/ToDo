from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from src.core.config import TODO_JWT_ALG, TODO_JWT_SECRET
from src.core.database import DbSession

from .models import ToDoUser, get_hash_password
from .schemas import TokenDataSchema, UserRegisterSchema

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


def create(*, session, user_in: UserRegisterSchema) -> ToDoUser:
    """Создает нового пользователя ToDoUser."""
    # pydantic вводит строковый пароль, но нам нужны байты
    password = get_hash_password(user_in.password)

    user = ToDoUser(
        **user_in.model_dump(exclude={"password"}),
        password=password,
    )
    session.add(user)
    session.commit()
    return user


def credentials_exception():
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=[{"msg": "Не удалось подтвердить учетные данные"}],
        headers={"WWW-Authenticate": "Bearer"}
    )


async def get_current_user(
        session: DbSession,
        token: Annotated[str, Depends(oauth2_scheme)]
) -> ToDoUser:
    try:
        payload = jwt.decode(token, TODO_JWT_SECRET, algorithms=[TODO_JWT_ALG])
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

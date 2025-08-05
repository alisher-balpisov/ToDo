from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.models import (ToDoUser, TokenSchema, UserLoginSchema,
                             UserPasswordUpdateSchema, UserRegisterSchema,
                             get_hash_password)
from src.core.database import DbSession, PrimaryKey
from src.core.exceptions import handle_server_exception

from .service import CurrentUser, create, get, get_token, get_user_by_username

auth_router = APIRouter()


@auth_router.post("/register")
def register_user(
        session: DbSession,
        user_in: UserRegisterSchema,
):

    user = get_user_by_username(session=session, username=user_in.username)
    print(user)
    if user:
        # Pydantic v2 compatible error handling
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
    user = create(session=session, user_in=user_in)
    return user, f"Регистрация пройдена успешно"


@auth_router.post("/login")
async def login_user(
        session: DbSession,
        user_in: UserLoginSchema
) -> TokenSchema:
    user = get_user_by_username(session=session, username=user_in.username)
    if user and user.verify_password(user_in.password):
        return TokenSchema(access_token=user.token, token_type="bearer")

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=[
            {
                "msg": "Invalid username.",
                "loc": ["username"],
                "type": "value_error",
            },
            {
                "msg": "Invalid password.",
                "loc": ["password"],
                "type": "value_error",
            },
        ],
    )


@auth_router.post("/{user_id}/change-password")
def change_password(
        session: DbSession,
        current_user: CurrentUser,
        user_id: PrimaryKey,
        password_update: UserPasswordUpdateSchema,
):
    user = get(session=session, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=[{"msg": "Пользователя с таким id не существует."}],
        )

    # Разрешайте только пользователям изменять свой собственный пароль
    if user.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=[{"msg": "Не имеет права изменять пароли других пользователей"}],
        )

    # Проверьте текущий пароль, если пользователь меняет свой собственный пароль
    if user.id == current_user.id:
        if not user.verify_password(password_update.current_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=[{"msg": "Неверный текущий пароль"}],
            )

    try:
        user.set_password(password_update.new_password)
        session.commit()
    except ValueError as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[{"msg": str(e)}],
        ) from e

    return user

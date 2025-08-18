from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.schemas import (TokenSchema, UserPasswordUpdateSchema,
                              UserRegisterSchema)
from src.core.database import DbSession

from .service import CurrentUser, get_user_by_username, register_service

router = APIRouter()


@router.post("/register")
def register(
        session: DbSession,
        user_in: UserRegisterSchema,
) :
    register_service(session=session,
                     username=user_in.username,
                     password=user_in.password)
    return {
        "msg": "Регистрация пройдена успешно",
        "username": user_in.username,
        "password": user_in.password,
        "is_password_generated": user_in.is_password_generated
    }


@router.post("/login")
async def login(
        session: DbSession,
        user_in: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> TokenSchema:
    user = get_user_by_username(session=session, username=user_in.username)
    if user and user.verify_password(user_in.password):
        return TokenSchema(access_token=user.get_token, token_type="bearer")

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


@router.post("/change-password")
def change_password(
        session: DbSession,
        current_user: CurrentUser,
        password_update: UserPasswordUpdateSchema,
):
    if not current_user.verify_password(password_update.current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[{"msg": "Неверный текущий пароль"}],
        )
    try:
        current_user.set_password(password_update.new_password)
        session.commit()
    except ValueError as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[{"msg": str(e)}],
        ) from e

    return {"msg": "Пароль успешно изменён"}

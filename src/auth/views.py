from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.schemas import (TokenSchema, UserPasswordUpdateSchema,
                              UserRegisterSchema)
from src.core.types import CurrentUser, DbSession

from .service import (change_password_service, login_service, oauth2_scheme,
                      refresh_service, register_service)

router = APIRouter()


@router.post("/register", status_code=status.HTTP_200_OK)
async def register(
        session: DbSession,
        user_in: UserRegisterSchema,
):
    await register_service(session=session,
                           username=user_in.username,
                           password=user_in.password)
    response = {
        "msg": "Регистрация пройдена успешно",
        "username": user_in.username,
    }

    if user_in.is_password_generated:
        response["generated_password"] = user_in.password

    return response


@router.post("/login")
async def login(
        session: DbSession,
        user_in: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> TokenSchema:
    access_token, refresh_token = await login_service(session=session,
                                                      username=user_in.username,
                                                      password=user_in.password)
    return TokenSchema(access_token=access_token, refresh_token=refresh_token, type="bearer")


@router.post("/refresh")
async def refresh(
    session: DbSession,
    token: Annotated[str, Depends(oauth2_scheme)]
):
    """Обновление access токена по refresh токену."""
    access_token, refresh_token = await refresh_service(session=session,
                                                        token=token)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/change-password")
async def change_password(
        session: DbSession,
        current_user: CurrentUser,
        password_update: UserPasswordUpdateSchema,
):
    await change_password_service(session=session,
                                  current_user=current_user,
                                  current_password=password_update.current_password,
                                  new_password=password_update.confirm_password)
    return {"msg": "Пароль успешно изменён"}

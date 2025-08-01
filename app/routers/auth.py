from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.jwt_handler import (ACCESS_TOKEN_EXPIRE_MINUTES,
                                  authenticate_user, create_access_token,
                                  get_hash_password)
from app.db.database import get_db
from app.db.models import User
from app.db.schemas import TokenSchema, UserCreateSchema
from app.handle_exception import handle_server_exception

router = APIRouter()


@router.post("/register")
def register(user_data: UserCreateSchema, db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        if db.query(User).filter(User.username == user_data.username).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Имя пользователя уже зарегистрировано"
            )

        if db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email пользователя уже зарегистрирован"
            )

        hashed_password = get_hash_password(user_data.password)
        new_user = User(
            username=user_data.username,
            email=str(user_data.email),
            hashed_password=hashed_password,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"message": "Пользователь успешно зарегистрировался"}

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        handle_server_exception(
            e, "Ошибка сервера при регистрации пользователя")


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(OAuth2PasswordRequestForm),
    db: Session = Depends(get_db)
) -> TokenSchema | None:
    try:
        user = authenticate_user(form_data.username, form_data.password, db)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверное имя пользователя или пароль",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=access_token_expires
        )
        return TokenSchema(access_token=access_token, token_type="bearer")

    except Exception as e:
        handle_server_exception(e, "Ошибка сервера при входе пользователя")

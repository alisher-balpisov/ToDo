from datetime import timedelta

from fastapi import HTTPException, Depends, APIRouter
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.jwt_handler import (get_hash_password, create_access_token,
                                  authenticate_user, ACCESS_TOKEN_EXPIRE_MINUTES)
from app.db.models import User
from app.db.models import session
from app.db.schemas import TokenSchema, UserCreateSchema
from app.routers.handle_exception import get_handle_exception

router = APIRouter(prefix="/auth")


@router.post("/register")
def register(user_data: UserCreateSchema):
    try:
        if session.query(User).filter(User.username == user_data.username).first():
            raise HTTPException(status_code=400, detail="Имя пользователя уже зарегистрировано")
        if session.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(status_code=400, detail="Email пользователя уже зарегистрирован")
        hashed_password = get_hash_password(user_data.password)
        new_user = User(
            username=user_data.username,
            email=str(user_data.email),
            hashed_password=hashed_password
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        return {"message": "Пользователь успешно зарегистрировался"}
    except Exception as e:
        session.rollback()
        get_handle_exception(e, "Ошибка сервера при регистрации пользователя")


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(OAuth2PasswordRequestForm)):
    try:
        user = authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Неверное имя пользователя или пароль"
            )
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=access_token_expires
        )
        return TokenSchema(access_token=access_token, token_type="bearer")
    except Exception as e:
        get_handle_exception(e, "Ошибка сервера при входе пользователя")

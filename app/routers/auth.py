from fastapi import HTTPException, Depends, APIRouter
from app.db.models import session
from fastapi.security import OAuth2PasswordRequestForm
from app.auth.jwt_handler import (get_hash_password, create_access_token,
                                  authenticate_user, ACCESS_TOKEN_EXPIRE_MINUTES)
from datetime import timedelta
from app.db.schemas import Token, UserCreate
from app.db.models import User

router = APIRouter(prefix="/auth")


@router.post("/register")
def register(user_data: UserCreate):
    if session.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Имя пользователя уже зарегистрировано")
    hashed_password = get_hash_password(user_data.password)
    new_user = User(
        username=user_data.username,
        hashed_password=hashed_password,
        disabled=False
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return {"message": "Пользователь успешно зарегистрировался"}


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(session, form_data.username, form_data.password)
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
    return Token(access_token=access_token, token_type="bearer")

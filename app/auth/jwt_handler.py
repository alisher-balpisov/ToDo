import jwt
from passlib.hash import bcrypt
from jwt.exceptions import InvalidTokenError
from datetime import timedelta, datetime
from fastapi import HTTPException, Depends
from app.db.models import session, Session, User
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY = 'ABCDE'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/login')


def get_hash_password(password: str) -> str:
    return bcrypt.hash(password)


def verify_password(plain_password: str, hash_password: str) -> bool:
    return bcrypt.verify(plain_password, hash_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        to_encode['exp'] = datetime.now() + expires_delta
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(db: Session, username: str, password: str):
    user = session.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail='Не удалось подтвердить учетные данные'
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    user = session.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
        current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Не активный user")
    return current_user

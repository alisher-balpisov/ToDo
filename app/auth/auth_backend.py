from passlib.hash import bcrypt
from jose import jwt, JWTError
from datetime import timedelta, datetime
from fastapi import HTTPException

SECRET_KEY = 'ABCDE'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def hash_password(password: str) -> str:
    return bcrypt.hash(password)


def verify_password(plain_password: str, hash_password: str) -> bool:
    return bcrypt.verify(plain_password, hash_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        to_encode['exp'] = datetime.utcnow() + expires_delta
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="недействительный токен")

import bcrypt

from src.core.config import settings


def hash_password(password: str) -> bytes:
    pw = password.encode(settings.DEFAULT_ENCODING)
    salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    return bcrypt.hashpw(pw, salt)

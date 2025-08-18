from urllib import parse

from starlette.config import Config

config = Config('.env')


class DatabaseCredentials:
    def __init__(self, value: str):
        # оставляем сырые данные для возможного логирования
        self._value = value
        self.username, raw_password = value.split(":", 1)
        # это позволит поддерживать специальные символы для учетных данных
        self.password = parse.quote(str(raw_password))

    def __str__(self):
        return f"{self.username}:{self.password}"


TODO_JWT_SECRET = config("TODO_JWT_SECRET", default="SECRET")
TODO_JWT_ALG = config("TODO_JWT_ALG", default="HS256")
TODO_JWT_EXP = config("TODO_JWT_EXP", cast=int, default=60)  # minuts


DATABASE_HOSTNAME = config("DATABASE_HOSTNAME", default="localhost")
# .env → DATABASE_CREDENTIALS=username:password
DATABASE_CREDENTIALS = config("DATABASE_CREDENTIALS", cast=DatabaseCredentials, default="postgres:200614")
_DATABASE_USER, _DATABASE_PASSWORD = str(DATABASE_CREDENTIALS).split(":")

DATABASE_NAME = config("DATABASE_NAME", default="base_db")
DATABASE_PORT = config("DATABASE_PORT", default="5432")


SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://{_DATABASE_USER}:{_DATABASE_PASSWORD}@{DATABASE_HOSTNAME}:{DATABASE_PORT}/{DATABASE_NAME}"




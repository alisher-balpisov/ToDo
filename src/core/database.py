import re
from typing import Annotated, Generator

from fastapi import Depends, File, Path, UploadFile
from pydantic import AfterValidator, Field
from sqlalchemy import create_engine
from sqlalchemy.orm import (DeclarativeBase, Session, declared_attr,
                            sessionmaker)

from src.constants import USERNAME_MAX_LENGTH, USERNAME_MIN_LENGTH
from src.core.config import settings

engine = create_engine(settings.SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


PrimaryKey = Annotated[int, Path(gt=0, lt=2147483647)]
DbSession = Annotated[Session, Depends(get_db)]
UsernameStr = Annotated[str, AfterValidator(
    lambda x: str.strip(x)), Path(min_length=USERNAME_MIN_LENGTH, max_length=USERNAME_MAX_LENGTH)]
UploadedFile = Annotated[UploadFile, File()]


def resolve_table_name(name: str) -> str:
    """Преобразует CamelCase / PascalCase имя в snake_case (для таблиц)."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    return s2.lower()


class Base(DeclarativeBase):

    __repr_attrs__ = []
    __repr_max_length__ = 15

    @declared_attr.directive
    def __tablename__(cls):
        return resolve_table_name(cls.__name__)

    @property
    def _id_str(self):
        if hasattr(self, "id") and self.id is not None:
            return str(self.id)
        return None

    @property
    def _repr_attrs_str(self):
        max_length = self.__repr_max_length__

        values = []
        single = len(self.__repr_attrs__) == 1
        for key in self.__repr_attrs__:
            if not hasattr(self, key):
                raise KeyError(
                    "{} неверный атрибут'{}' в __repr__attrs__".format(
                        self.__class__, key)
                )
            value = getattr(self, key)
            wrap_in_quote = isinstance(value, str)

            value = str(value)
            if len(value) > max_length:
                value = value[:max_length] + "..."

            if wrap_in_quote:
                value = "'{}'".format(value)
            values.append(value if single else "{}:{}".format(key, value))

        return " ".join(values)

    def __repr__(self):
        id_str = ("#" + self._id_str) if self._id_str else ""
        return "<{} {}{}>".format(
            self.__class__.__name__,
            id_str,
            " " + self._repr_attrs_str if self._repr_attrs_str else "",
        )


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)

import re

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, declared_attr, sessionmaker

from src.core.config import settings

engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    echo=False,
    future=True
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    expire_on_commit=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# 🔹 Создание таблиц (async)
async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


class Base(DeclarativeBase):

    __repr_attrs__: list[str] = []
    __repr_max_length__: int = 15

    @declared_attr.directive
    def __tablename__(cls):
        return cls.resolve_table_name(cls.__name__)

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
                    "{} неверный атрибут '{}' в __repr__attrs__".format(
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

    @staticmethod
    def resolve_table_name(name: str) -> str:
        """Преобразует CamelCase / PascalCase имя в snake_case (для таблиц)."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
        return s2.lower()

import enum
from datetime import datetime
import os

import pytz
from sqlalchemy import (Boolean, Column, DateTime, Enum, ForeignKey, Integer,
                        LargeBinary, String, Text, create_engine)
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL не задан в переменных окружения")

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()


class ToDo(Base):
    __tablename__ = "ToDo"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    user_id = Column(Integer, index=True)
    text = Column(Text)
    completion_status = Column(Boolean, default=False, index=True)
    date_time = Column(DateTime, default=datetime.now(
        pytz.timezone("Asia/Almaty")))

    file_data = Column(LargeBinary, nullable=True, default=None)
    file_name = Column(String, nullable=True, default=None)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True)
    hashed_password = Column(String)
    disabled = Column(Boolean, default=False)


class SharedAccessEnum(enum.Enum):
    VIEW = "view"
    EDIT = "edit"


class TaskShare(Base):
    __tablename__ = "task_shares"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("ToDo.id"), index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), index=True)
    shared_with_id = Column(Integer, ForeignKey("users.id"), index=True)
    permission_level = Column(Enum(SharedAccessEnum),
                              default=SharedAccessEnum.VIEW)
    date_time = Column(DateTime, default=datetime.now(
        pytz.timezone("Asia/Almaty")))


Base.metadata.create_all(engine)

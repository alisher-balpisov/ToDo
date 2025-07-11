from sqlalchemy import (create_engine, Column, Integer,
                        String, Boolean, DateTime, Text, LargeBinary, ForeignKey, Enum)
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
import pytz
import enum

DATABASE_URL = 'postgresql://postgres:200614@localhost:5432/base_db'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()


class ToDo(Base):
    __tablename__ = 'ToDo'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    user_id = Column(Integer)
    text = Column(Text)
    completion_status = Column(Boolean, default=False)
    date_time = Column(DateTime, default=datetime.now(pytz.timezone('Asia/Almaty')))

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
    view = 'view'
    edit = 'edit'


class TaskShare(Base):
    __tablename__ = 'task_shares'

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('ToDo.id'))
    owner_id = Column(Integer, ForeignKey('users.id'))
    shared_with_id = Column(Integer, ForeignKey('users.id'))
    permission_level = Column(Enum(SharedAccessEnum), default=SharedAccessEnum.view)
    date_time = Column(DateTime, default=datetime.now(pytz.timezone('Asia/Almaty')))


Base.metadata.create_all(engine)

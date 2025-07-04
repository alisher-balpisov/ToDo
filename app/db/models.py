from sqlalchemy import (create_engine, Column, Integer,
                        String, Boolean, DateTime, Text)
from sqlalchemy.orm import sessionmaker, declarative_base

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
    date_time = Column(DateTime)
    file_path = Column(String, nullable=True)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True)
    hashed_password = Column(String)
    disabled = Column(Boolean, default=False)


Base.metadata.create_all(engine)

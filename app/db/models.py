from sqlalchemy import (create_engine, Column, Integer,
                        String, Boolean, DateTime)
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = 'postgresql://localhost:5432/base_db'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()


class ToDo(Base):
    __tablename__ = 'ToDo'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    text = Column(String)
    completion_status = Column(Boolean)
    date_time = Column(DateTime)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    disabled = Column(Boolean, default=False)


Base.metadata.create_all(engine)

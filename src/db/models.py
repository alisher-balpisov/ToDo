import enum
from datetime import datetime, timezone

from sqlalchemy import (Boolean, Column, DateTime, Enum, ForeignKey, Integer,
                        LargeBinary, String, Text)

from src.auth.models import ToDoUser
from src.db.database import Base


class ToDo(Base):

    __repr_attrs__ = ['date_time']

    id = Column(Integer, primary_key=True)
    name = Column(String)
    user_id = Column(Integer, index=True)
    text = Column(Text)
    completion_status = Column(Boolean, default=False, index=True)
    date_time = Column(DateTime, default=datetime.now(
        timezone.utc).astimezone())

    file_data = Column(LargeBinary, nullable=True, default=None)
    file_name = Column(String, nullable=True, default=None)


class SharedAccessEnum(enum.Enum):
    VIEW = "view"
    EDIT = "edit"


class TaskShare(Base):

    __repr_attrs__ = ['task_id', 'date_time']

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey(ToDo.id), index=True)
    owner_id = Column(Integer, ForeignKey(ToDoUser.id), index=True)
    shared_with_id = Column(Integer, ForeignKey(ToDoUser.id), index=True)
    permission_level = Column(Enum(SharedAccessEnum),
                              default=SharedAccessEnum.VIEW)
    date_time = Column(DateTime, default=datetime.now(
        timezone.utc).astimezone())

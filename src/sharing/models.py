import enum
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer

from src.auth.models import ToDoUser
from src.common.models import Task
from src.core.database import Base


class SharedAccessEnum(enum.Enum):
    view = "view"
    edit = "edit"


class Share(Base):

    __repr_attrs__ = ['task_id', 'date_time']

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey(Task.id), index=True)
    owner_id = Column(Integer, ForeignKey(ToDoUser.id), index=True)
    target_user_id = Column(Integer, ForeignKey(ToDoUser.id), index=True)
    permission_level = Column(Enum(SharedAccessEnum),
                              default=SharedAccessEnum.view)
    date_time = Column(DateTime, default=datetime.now(
        timezone.utc).astimezone())

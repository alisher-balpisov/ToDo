import enum
from datetime import datetime, timezone

from sqlalchemy import (Column, DateTime, Enum, ForeignKey, Integer,
                        UniqueConstraint)

from src.auth.models import User
from src.common.models import Task
from src.core.database import Base


class SharedAccessEnum(enum.Enum):
    view = "view"
    edit = "edit"


class Share(Base):

    __repr_attrs__ = ['task_id', 'date_time']

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer,
                     ForeignKey(Task.id), index=True, nullable=False)

    owner_id = Column(Integer,
                      ForeignKey(User.id), index=True, nullable=False)

    target_user_id = Column(Integer,
                            ForeignKey(User.id), index=True, nullable=False)

    permission_level = Column(Enum(SharedAccessEnum),
                              default=SharedAccessEnum.view)

    date_time = Column(DateTime,
                       default=lambda: datetime.now(timezone.utc))

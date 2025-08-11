from datetime import datetime, timezone

from sqlalchemy import (Boolean, Column, DateTime, Integer, LargeBinary,
                        String, Text)

from src.core.database import Base


class Task(Base):

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

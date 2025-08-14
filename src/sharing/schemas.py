import enum

from fastapi import Query
from pydantic import BaseModel, Field

from src.common.schemas import BaseSortValidator, ConflictsType
from src.sharing.helpers import SortSharedTasksRule
from src.tasks.schemas import SortTasksValidator

from .models import SharedAccessEnum


class TaskShareSchema(BaseModel):
    target_username: str
    permission_level: SharedAccessEnum = Field(default=SharedAccessEnum.view)


class SortSharedTasksValidator(BaseSortValidator):
    sort: list[SortSharedTasksRule]
    _sort_field: str = 'sort'

    CONFLICTS: ConflictsType = SortTasksValidator.CONFLICTS + [
        ("permission_view_first", "permission_edit_first"),
    ]


class SortOrder(enum.Enum):
    asc = "asc"
    desc = "desc"


class SortOrder(enum.Enum):
    asc = "asc"
    desc = "desc"


class Sort(BaseModel):
    date: SortOrder = SortOrder.desc
    name: str
    status: SortOrder = SortOrder.desc
    permission: SortOrder = SortOrder.desc


async def get_params(
    date: SortOrder = Query(None),
    name: str = Query(None),
    status: SortOrder = Query(None),
    permission: SortOrder = Query(None),
) -> Sort:
    return Sort(date=date, name=name, status=status, permission=permission)

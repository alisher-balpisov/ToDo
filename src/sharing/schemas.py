from typing import ClassVar

from pydantic import BaseModel, Field

from src.common.schemas import BaseSortValidator
from src.sharing.helpers import SortSharedTasksRule
from src.tasks.schemas import SortTasksValidator

from .models import SharedAccessEnum


class TaskShareSchema(BaseModel):
    target_username: str
    permission_level: SharedAccessEnum = Field(default=SharedAccessEnum.view)


class SortSharedTasksValidator(BaseSortValidator):
    sort: list[SortSharedTasksRule]
    _sort_field = 'sort'  # указывает из какого поля брать список сортировок

    CONFLICTS: ClassVar = SortTasksValidator.CONFLICTS + [
        ("permission_view_first", "permission_edit_first"),
    ]

from pydantic import BaseModel, Field

from src.common.schemas import BaseSortValidator, ConflictsType
from src.sharing.helpers import SortSharedTasksRule
from src.tasks.schemas import SortTasksValidator

from .models import SharedAccessEnum


class TaskShareSchema(BaseModel):
    target_username: str
    permission_level: SharedAccessEnum = Field(default=SharedAccessEnum.view)


class SortSharedTasksValidator(BaseSortValidator):
    sort_shared_tasks: list[SortSharedTasksRule]
    _sort_field: str = 'sort_shared_tasks'

    CONFLICTS: ConflictsType = SortTasksValidator.CONFLICTS + [
        ("permission_view_first", "permission_edit_first"),
    ]

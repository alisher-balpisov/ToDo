from src.common.schemas import BaseSortValidator, ConflictsType

from .helpers import SortTasksRule


class SortTasksValidator(BaseSortValidator):
    sort_tasks: list[SortTasksRule]
    _sort_field: str = 'sort_tasks'

    CONFLICTS: ConflictsType = [
        ("date_desc", "date_asc"),
        ("status_false_first", "status_true_first"),
    ]

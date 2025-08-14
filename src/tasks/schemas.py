from fastapi import Query

from src.common.schemas import BaseSortValidator, ConflictsType

from .helpers import SortTasksRule


class SortTasksValidator(BaseSortValidator):
    sort: list[SortTasksRule] 
    _sort_field: str = 'sort'

    CONFLICTS: ConflictsType = [
        ("date_desc", "date_asc"),
        ("status_false_first", "status_true_first"),
    ]

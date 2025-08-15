from typing import ClassVar

from fastapi import Query

from src.common.schemas import BaseSortValidator

from .helpers import SortTasksRule


class SortTasksValidator(BaseSortValidator):
    sort: list[SortTasksRule]
    _sort_field: str = 'sort'  # указывает из какого поля брать список сортировок

    CONFLICTS: ClassVar = [
        ("date_desc", "date_asc"),
        ("status_false_first", "status_true_first"),
    ]

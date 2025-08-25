from typing import ClassVar

from src.common.schemas import BaseSortValidator

from .helpers import SortTasksRule


class SortTasksValidator(BaseSortValidator):
    sort: list[SortTasksRule]
    _sort_field: str = 'sort'  # указывает из какого поля брать список сортировок

    CONFLICTS: ClassVar = [
        ("date_asc", "date_desc"),
        ("status_asc", "status_desc"),
    ]

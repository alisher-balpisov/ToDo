from typing import List, Literal

from fastapi import Query

from app.db.models import ToDo

SortRule = Literal[
    "date_desc", "date_asc", "name", "status_false_first", "status_true_first"
]

todo_sort_mapping = {
    "date_desc": ToDo.date_time.desc(),
    "date_asc": ToDo.date_time.asc(),
    "name": ToDo.name.asc(),
    "status_false_first": ToDo.completion_status.asc(),
    "status_true_first": ToDo.completion_status.desc(),
}


def validate_sort(
    sort: List[SortRule] = Query(default=["date_desc"]),
) -> List[SortRule]:
    if "date_desc" in sort and "date_asc" in sort:
        raise ValueError(
            "Нельзя использовать одновременно 'date_desc' и 'date_asc'")
    if "status_false_first" in sort and "status_true_first" in sort:
        raise ValueError(
            "Нельзя использовать одновременно 'status_false_first' и 'status_true_first'"
        )
    return sort

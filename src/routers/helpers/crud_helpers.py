from typing import List, Literal

from fastapi import Query

from src.db.models import ToDo

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








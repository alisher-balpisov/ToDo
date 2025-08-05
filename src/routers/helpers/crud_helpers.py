from typing import List, Literal

from fastapi import Query

from src.db.models import Task

SortRule = Literal[
    "date_desc", "date_asc", "name", "status_false_first", "status_true_first"
]

todo_sort_mapping = {
    "date_desc": Task.date_time.desc(),
    "date_asc": Task.date_time.asc(),
    "name": Task.name.asc(),
    "status_false_first": Task.completion_status.asc(),
    "status_true_first": Task.completion_status.desc(),
}

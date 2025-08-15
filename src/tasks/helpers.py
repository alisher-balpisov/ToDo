from typing import Literal

from src.common.models import Task

SortTasksRule = Literal[
    "date_desc",
    "date_asc",
    "name",
    "status_asc",
    "status_desc"
]

tasks_sort_mapping = {
    "date_asc": Task.date_time.asc(),
    "date_desc": Task.date_time.desc(),
    "name": Task.name.asc(),
    "status_asc": Task.completion_status.asc(),
    "status_desc": Task.completion_status.desc(),
}

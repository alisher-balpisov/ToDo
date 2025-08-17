from typing import Literal

from .models import Share, Task

SortSharedTasksRule = Literal[
    "date_desc",
    "date_asc",
    "name",
    "status_asc",
    "status_desc",
    "permission_asc",
    "permission_desc",
]

shared_tasks_sort_mapping = {
    "date_desc": Task.date_time.desc(),
    "date_asc": Task.date_time.asc(),
    "name": Task.name.asc(),
    "status_asc": Task.completion_status.asc(),
    "status_desc": Task.completion_status.desc(),
    "permission_asc": Share.permission_level.asc(),
    "permission_desc": Share.permission_level.desc(),
}

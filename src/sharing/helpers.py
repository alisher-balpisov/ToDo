from typing import Literal

from .models import Share, Task

SortSharedTasksRule = Literal[
    "date_desc",
    "date_asc",
    "name",
    "status_false_first",
    "status_true_first",
    "permission_view_first",
    "permission_edit_first",
]

shared_tasks_sort_mapping = {
    "date_desc": Task.date_time.desc(),
    "date_asc": Task.date_time.asc(),
    "name": Task.name.asc(),
    "status_false_first": Task.completion_status.asc(),
    "status_true_first": Task.completion_status.desc(),
    "permission_view_first": Share.permission_level.asc(),
    "permission_edit_first": Share.permission_level.desc(),
}

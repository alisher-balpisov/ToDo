from typing import ClassVar, Optional, Tuple, Type

from fastapi import Query
from pydantic import BaseModel, Field, field_validator, model_validator

from src.db.models import SharedAccessEnum
from src.tasks.helpers.crud_helpers import SortTasksRule
from src.tasks.helpers.shared_tasks_helpers import SortSharedTasksRule


class TaskSchema(BaseModel):
    name: str | None = Field(default=None, max_length=30)
    text: str | None = Field(default=None, max_length=4096)


class TaskShareSchema(BaseModel):
    target_username: str
    permission_level: SharedAccessEnum = Field(default=SharedAccessEnum.view)


def check_conflicting_rules(
    sort: list[str], conflicts: list[Tuple[str, str]]
) -> None:
    """
    Проверяет список сортировок на наличие конфликтующих правил.
    """
    for a, b in conflicts:
        if a in sort and b in sort:
            raise ValueError(f"Нельзя использовать одновременно '{a}' и '{b}'")


ConflictsType = ClassVar[list[Tuple[str, str]]]


class BaseSortValidator(BaseModel):
    """
    Базовый класс валидатора, инкапсулирующий общую логику проверки конфликтов.
    """
    _sort_field: str

    @model_validator(mode='after')
    def check_conflicts(self) -> 'BaseSortValidator':
        """
        Запускает проверку конфликтующих правил для указанного поля.
        """
        # Динамически получаем значение поля для валидации
        sort_params = getattr(self, self._sort_field)
        # Получаем список конфликтов из атрибута класса
        conflicts = getattr(self, 'CONFLICTS', ConflictsType)

        if sort_params:
            check_conflicting_rules(sort_params, conflicts)
        return self


class SortTasksValidator(BaseSortValidator):
    sort_tasks: list[SortTasksRule]
    _sort_field: str = 'sort_tasks'

    CONFLICTS: ConflictsType = [
        ("date_desc", "date_asc"),
        ("status_false_first", "status_true_first"),
    ]


class SortSharedTasksValidator(BaseSortValidator):
    sort_shared_tasks: list[SortSharedTasksRule]
    _sort_field: str = 'sort_shared_tasks'

    CONFLICTS: ConflictsType = SortTasksValidator.CONFLICTS + [
        ("permission_view_first", "permission_edit_first"),
    ]

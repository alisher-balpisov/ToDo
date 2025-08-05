from typing import ClassVar, List, Tuple, Type

from pydantic import BaseModel, Field, field_validator, model_validator

from src.db.models import SharedAccessEnum
from src.routers.helpers.crud_helpers import SortRule as SortTasksRule
from src.routers.helpers.shared_tasks_helpers import \
    SortRule as SortSharedTasksRule


class ToDoSchema(BaseModel):
    name: str | None = Field(default=None, max_length=30)
    text: str | None = Field(default=None, max_length=4096)
    completion_status: bool | None = Field(default=None)


class TaskShareSchema(BaseModel):
    target_username: str
    permission_level: SharedAccessEnum = Field(default=SharedAccessEnum.VIEW)


def check_conflicting_rules(
    sort: List[str], conflicts: List[Tuple[str, str]]
) -> None:
    """
    Проверяет список сортировок на наличие конфликтующих правил.
    """
    for a, b in conflicts:
        if a in sort and b in sort:
            raise ValueError(f"Нельзя использовать одновременно '{a}' и '{b}'")


ConflictsType = ClassVar[List[Tuple[str, str]]]


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
    sort_tasks: List[SortTasksRule]
    _sort_field: str = 'sort_tasks'

    CONFLICTS: ConflictsType = [
        ("date_desc", "date_asc"),
        ("status_false_first", "status_true_first"),
    ]


class SortSharedTasksValidator(BaseSortValidator):
    sort_shared_tasks: List[SortSharedTasksRule]
    _sort_field: str = 'sort_shared_tasks'

    CONFLICTS: ConflictsType = SortTasksValidator.CONFLICTS + [
        ("permission_view_first", "permission_edit_first"),
    ]

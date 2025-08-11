from typing import ClassVar, Tuple

from pydantic import BaseModel, Field, model_validator


class TaskSchema(BaseModel):
    name: str | None = Field(default=None, max_length=30)
    text: str | None = Field(default=None, max_length=4096)


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

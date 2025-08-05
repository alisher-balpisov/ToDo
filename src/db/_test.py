
import pytest

from .schemas import SortSharedTasksValidator, SortTasksValidator


def test_sort_tasks_validator_valid():
    validator = SortTasksValidator()
    validator.sort_tasks = ["date_desc", "status_false_first"]
    assert validator.model_validate(validator)


def test_sort_tasks_validator_conflict():
    validator = SortTasksValidator()
    validator.sort_tasks = ["date_desc", "date_asc"]
    with pytest.raises(ValueError, match="Нельзя использовать одновременно 'date_desc' и 'date_asc'"):
        validator.model_validate(validator)


def test_sort_shared_tasks_validator_valid():
    validator = SortSharedTasksValidator(sort_tasks=[], sort_shared_tasks=[
                                         "permission_view_first", "permission_edit_first"])
    assert validator.model_validate(validator)


def test_sort_shared_tasks_validator_conflict():
    validator = SortSharedTasksValidator()
    validator.sort_shared_tasks = [
        "permission_view_first", "permission_edit_first"]
    with pytest.raises(ValueError, match="Нельзя использовать одновременно 'permission_view_first' и 'permission_edit_first'"):
        validator.model_validate(validator)

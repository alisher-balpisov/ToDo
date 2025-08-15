import pytest


def test_code_coverage_example():
    """Пример теста для увеличения покрытия кода."""
    # Этот тест можно использовать для покрытия редко используемых веток кода

    def rarely_used_function(value):
        if value == "special_case":
            return "special_result"
        elif value == "another_case":
            return "another_result"
        else:
            return "default_result"

    # Тестируем все ветки
    assert rarely_used_function("special_case") == "special_result"
    assert rarely_used_function("another_case") == "another_result"
    assert rarely_used_function("normal") == "default_result"


if __name__ == "__main__":
    # Запуск специфических тестов
    pytest.main([
        "-v",
        "--cov=.",
        "--cov-report=html",
        "--cov-report=term-missing",
        "-m", "not slow"  # Исключаем медленные тесты при обычном запуске
    ])

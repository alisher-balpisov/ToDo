echo "=== Task Manager API Test Runner ==="

# Основные команды для запуска тестов

# 1. Запуск всех тестов
run_all_tests() {
    echo "Запуск всех тестов..."
    pytest -v --tb=short
}

# 2. Запуск тестов с покрытием кода
run_tests_with_coverage() {
    echo "Запуск тестов с анализом покрытия..."
    pytest --cov=. --cov-report=html --cov-report=term-missing --cov-fail-under=80
}

# 3. Запуск быстрых тестов (исключая медленные)
run_fast_tests() {
    echo "Запуск быстрых тестов..."
    pytest -v -m "not slow"
}

# 4. Запуск только тестов аутентификации
run_auth_tests() {
    echo "Запуск тестов аутентификации..."
    pytest -v -m "auth"
}

# 5. Запуск тестов для задач
run_task_tests() {
    echo "Запуск тестов управления задачами..."
    pytest -v -m "tasks"
}

# 6. Запуск тестов совместного доступа
run_sharing_tests() {
    echo "Запуск тестов совместного доступа..."
    pytest -v -m "sharing"
}

# 7. Запуск интеграционных тестов
run_integration_tests() {
    echo "Запуск интеграционных тестов..."
    pytest -v -m "integration"
}

# 8. Запуск тестов безопасности
run_security_tests() {
    echo "Запуск тестов безопасности..."
    pytest -v test_security.py
}

# 9. Запуск тестов производительности
run_performance_tests() {
    echo "Запуск тестов производительности..."
    pytest -v -m "slow" test_performance.py
}

# 10. Генерация отчета в формате JUnit XML
generate_junit_report() {
    echo "Генерация JUnit отчета..."
    pytest --junitxml=test-results.xml
}

# 11. Запуск в verbose режиме с детальным выводом
run_verbose_tests() {
    echo "Запуск с детальным выводом..."
    pytest -vvv --tb=long
}

# 12. Параллельный запуск тестов (требует pytest-xdist)
run_parallel_tests() {
    echo "Параллельный запуск тестов..."
    pytest -n auto
}

# Обработка аргументов командной строки
case "$1" in
    "all")
        run_all_tests
        ;;
    "coverage")
        run_tests_with_coverage
        ;;
    "fast")
        run_fast_tests
        ;;
    "auth")
        run_auth_tests
        ;;
    "tasks")
        run_task_tests
        ;;
    "sharing")
        run_sharing_tests
        ;;
    "integration")
        run_integration_tests
        ;;
    "security")
        run_security_tests
        ;;
    "performance")
        run_performance_tests
        ;;
    "junit")
        generate_junit_report
        ;;
    "verbose")
        run_verbose_tests
        ;;
    "parallel")
        run_parallel_tests
        ;;
    *)
        echo "Использование: $0 {all|coverage|fast|auth|tasks|sharing|integration|security|performance|junit|verbose|parallel}"
        echo ""
        echo "Доступные команды:"
        echo "  all         - Запустить все тесты"
        echo "  coverage    - Запустить тесты с анализом покрытия"
        echo "  fast        - Запустить только быстрые тесты"
        echo "  auth        - Запустить тесты аутентификации"
        echo "  tasks       - Запустить тесты управления задачами"
        echo "  sharing     - Запустить тесты совместного доступа"
        echo "  integration - Запустить интеграционные тесты"
        echo "  security    - Запустить тесты безопасности"
        echo "  performance - Запустить тесты производительности"
        echo "  junit       - Сгенерировать JUnit отчет"
        echo "  verbose     - Запустить с детальным выводом"
        echo "  parallel    - Запустить тесты параллельно"
        exit 1
        ;;
esac

# Makefile для удобного запуска тестов
# Makefile
.PHONY: test test-coverage test-fast test-auth test-tasks test-sharing test-integration test-security test-performance clean install

# Установка зависимостей
install:
	pip install -r requirements-test.txt

# Запуск всех тестов
test:
	pytest -v

# Тесты с покрытием
test-coverage:
	pytest --cov=. --cov-report=html --cov-report=term-missing

# Быстрые тесты
test-fast:
	pytest -v -m "not slow"

# Тесты по категориям
test-auth:
	pytest -v -m "auth"

test-tasks:
	pytest -v -m "tasks"

test-sharing:
	pytest -v -m "sharing"

test-integration:
	pytest -v -m "integration"

test-security:
	pytest -v test_security.py

test-performance:
	pytest -v -m "slow"

# Очистка временных файлов
clean:
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -f test-results.xml
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# CI/CD pipeline конфигурация для GitHub Actions
# .github/workflows/tests.yml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-test.txt
    
    - name: Run tests with coverage
      run: |
        pytest --cov=. --cov-report=xml --cov-report=term-missing
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
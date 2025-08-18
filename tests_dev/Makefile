.PHONY: test test-unit test-integration test-e2e test-coverage test-fast test-slow clean install

# Установка зависимостей
install:
	pip install -r tests/requirements-test.txt

# Запуск всех тестов
test:
	pytest -v

# Запуск unit тестов
test-unit:
	pytest -v tests/unit/ -m "unit"

# Запуск интеграционных тестов
test-integration:
	pytest -v tests/integration/ -m "integration"

# Запуск e2e тестов
test-e2e:
	pytest -v tests/e2e/ -m "e2e"

# Тесты с покрытием кода
test-coverage:
	pytest --cov=src --cov-report=html --cov-report=term-missing --cov-fail-under=80

# Быстрые тесты (без медленных)
test-fast:
	pytest -v -m "not slow"

# Только медленные тесты
test-slow:
	pytest -v -m "slow"

# Тесты по модулям
test-auth:
	pytest -v -m "auth"

test-tasks:
	pytest -v -m "tasks"

test-sharing:
	pytest -v -m "sharing"

test-files:
	pytest -v -m "files"

test-security:
	pytest -v -m "security"

test-performance:
	pytest -v -m "performance"

# Параллельный запуск тестов
test-parallel:
	pytest -n auto -v

# Генерация отчетов
test-junit:
	pytest --junitxml=test-results.xml

test-html:
	pytest --html=test-report.html --self-contained-html

# Очистка временных файлов
clean:
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -f test-results.xml
	rm -f test-report.html
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Проверка качества тестов
test-quality:
	pytest --dead-fixtures --dup-fixtures

# Профилирование тестов
test-profile:
	pytest --profile --profile-svg

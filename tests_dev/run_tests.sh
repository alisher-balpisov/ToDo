echo "=== Task Manager API Test Suite ==="
echo "Choose test category:"
echo "1) All tests"
echo "2) Unit tests only"
echo "3) Integration tests only"
echo "4) E2E tests only"
echo "5) Fast tests (no slow)"
echo "6) Tests with coverage"
echo "7) Security tests"
echo "8) Performance tests"
echo "9) Parallel execution"

read -p "Enter your choice (1-9): " choice

case $choice in
    1)
        echo "Running all tests..."
        pytest -v
        ;;
    2)
        echo "Running unit tests..."
        pytest -v tests/unit/ -m "unit"
        ;;
    3)
        echo "Running integration tests..."
        pytest -v tests/integration/ -m "integration"
        ;;
    4)
        echo "Running E2E tests..."
        pytest -v tests/e2e/ -m "e2e"
        ;;
    5)
        echo "Running fast tests..."
        pytest -v -m "not slow"
        ;;
    6)
        echo "Running tests with coverage..."
        pytest --cov=src --cov-report=html --cov-report=term-missing
        ;;
    7)
        echo "Running security tests..."
        pytest -v -m "security"
        ;;
    8)
        echo "Running performance tests..."
        pytest -v -m "performance"
        ;;
    9)
        echo "Running tests in parallel..."
        pytest -n auto -v
        ;;
    *)
        echo "Invalid choice. Running all tests..."
        pytest -v
        ;;
esac

echo "Test execution completed!"

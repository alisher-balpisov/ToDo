# Единые правила стиля для тестов

## 1. Структура тестового метода (AAA паттерн)
```python
def test_action_condition_expected_result(self, fixtures):
    """Краткое описание того, что тестирует метод."""
    # Arrange - подготовка данных
    data = {...}
    
    # Act - выполнение действия
    result = some_action(data)
    
    # Assert - проверки
    assert result.field == expected_value
```

## 2. Обработка исключений
**Правило**: Всегда использовать `pytest.raises()` для ожидаемых исключений

```python
# ✅ Правильно
def test_create_task_empty_name_raises_error(self, db_session, test_user):
    with pytest.raises(MissingRequiredFieldException) as exc_info:
        create_task_service(db_session, test_user.id, "", "text")
    
    assert exc_info.value.error_code == "MISSING_REQUIRED_FIELD"
    assert "имя задачи" in exc_info.value.missing_fields

# ❌ Неправильно
def test_create_task_empty_name(self, client, auth_headers):
    response = client.post("/tasks/", json={"text": "desc"}, headers=auth_headers)
    assert response.status_code == 422
```

## 3. Именование тестов
**Шаблон**: `test_[действие]_[условие]_[результат]`

```python
# ✅ Правильно
test_register_user_valid_data_success
test_login_user_wrong_password_raises_invalid_credentials
test_get_task_nonexistent_id_raises_not_found

# ❌ Неправильно  
test_register_success
test_login_wrong_password
test_get_task_not_found
```

## 4. API тесты vs Service тесты

### API тесты (integration)
- Проверяют HTTP статус коды
- Используют TestClient
- Проверяют JSON ответы

```python
def test_create_task_valid_data_returns_201(self, client, auth_headers):
    # Arrange
    task_data = {"name": "Test", "text": "Description"}
    
    # Act
    response = client.post("/tasks/", json=task_data, headers=auth_headers)
    
    # Assert
    assert response.status_code == 201
    assert response.json()["task_name"] == "Test"
```

### Service тесты (unit)
- Тестируют бизнес-логику
- Используют `pytest.raises()` для исключений
- Работают с объектами напрямую

```python
def test_create_task_empty_name_raises_missing_field(self, db_session, test_user):
    # Arrange
    empty_name = ""
    
    # Act & Assert
    with pytest.raises(MissingRequiredFieldException) as exc_info:
        create_task_service(db_session, test_user.id, empty_name, "text")
    
    assert exc_info.value.error_code == "MISSING_REQUIRED_FIELD"
```

## 5. Параметризация для схожих тестов
```python
@pytest.mark.parametrize("password, expected_error", [
    ("123", "минимум 8 символов"),
    ("password123", "заглавными буквами"),
    ("PASSWORD123", "строчными буквами"),
])
def test_register_invalid_password_raises_validation_error(self, password, expected_error):
    with pytest.raises(InvalidInputException) as exc_info:
        UserRegisterSchema(username="user", password=password)
    
    assert expected_error in exc_info.value.expected_format
```

## 6. Фикстуры и утилиты
- Выносить повторяющуюся логику в фикстуры
- Использовать утилитарные функции из `utils.py`
- Группировать связанные фикстуры

## 7. Docstrings
```python
def test_share_task_nonexistent_user_raises_not_found(self, db_session, test_user, test_task):
    """Тест предоставления доступа несуществующему пользователю."""
```

## 8. Организация классов
```python
class TestTaskService:
    """Тесты сервиса управления задачами."""
    
    def test_create_task_valid_data_success(self):
        """Позитивный сценарий создания."""
        
    def test_create_task_empty_name_raises_missing_field(self):
        """Негативный сценарий - пустое имя."""
```

## 9. Проверка исключений - детально
```python
# Полная проверка исключения
with pytest.raises(ResourceNotFoundException) as exc_info:
    get_task_service(db_session, user_id, 999)

assert exc_info.value.error_code == "RESOURCE_NOT_FOUND"
assert exc_info.value.resource_type == "Задача"
assert exc_info.value.resource_id == "999"
```

## 10. Маркировка тестов
```python
@pytest.mark.slow
class TestPerformance:
    """Медленные тесты производительности."""

@pytest.mark.integration  
class TestAPIEndpoints:
    """Интеграционные тесты API."""
```

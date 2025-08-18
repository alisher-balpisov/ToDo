import pytest
from unittest.mock import Mock
from jose import jwt
from src.auth.service import (
    get_user_by_username,
    get_user_by_id,
    create,
    get_current_user,
    credentials_exception
)
from src.auth.schemas import UserRegisterSchema
from src.auth.models import ToDoUser
from src.core.config import TODO_JWT_SECRET, TODO_JWT_ALG


class TestAuthService:
    """Тесты сервиса аутентификации."""

    def test_get_user_by_username_found(self, db_session, test_user):
        """Тест поиска пользователя по имени - найден."""
        user = get_user_by_username(db_session, test_user.username)
        
        assert user is not None
        assert user.username == test_user.username
        assert user.id == test_user.id

    def test_get_user_by_username_not_found(self, db_session):
        """Тест поиска пользователя по имени - не найден."""
        user = get_user_by_username(db_session, "nonexistent")
        
        assert user is None

    def test_get_user_by_id_found(self, db_session, test_user):
        """Тест поиска пользователя по ID - найден."""
        user = get_user_by_id(db_session, test_user.id)
        
        assert user is not None
        assert user.id == test_user.id
        assert user.username == test_user.username

    def test_get_user_by_id_not_found(self, db_session):
        """Тест поиска пользователя по ID - не найден."""
        user = get_user_by_id(db_session, 999)
        
        assert user is None

    def test_create_user_success(self, db_session):
        """Тест успешного создания пользователя."""
        user_data = UserRegisterSchema(
            username="newuser",
            password="Password123"
        )
        
        user = create(session=db_session, user_in=user_data)
        
        assert user.username == "newuser"
        assert user.verify_password("Password123")
        assert user.id is not None

    def test_get_current_user_valid_token(self, db_session, test_user):
        """Тест получения текущего пользователя с валидным токеном."""
        token = test_user.get_token
        
        current_user = get_current_user(db_session, token)
        
        assert current_user.id == test_user.id
        assert current_user.username == test_user.username

    def test_get_current_user_invalid_token(self, db_session):
        """Тест получения текущего пользователя с невалидным токеном."""
        with pytest.raises(Exception):  # credentials_exception
            get_current_user(db_session, "invalid_token")

    def test_get_current_user_expired_token(self, db_session, test_user):
        """Тест получения пользователя с истекшим токеном."""
        # Создаем токен с прошедшим временем
        from datetime import datetime, timedelta, timezone
        
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        payload = {"exp": past_time, "sub": test_user.username}
        expired_token = jwt.encode(payload, TODO_JWT_SECRET, algorithm=TODO_JWT_ALG)
        
        with pytest.raises(Exception):  # credentials_exception
            get_current_user(db_session, expired_token)

    def test_credentials_exception(self):
        """Тест исключения для неавторизованных пользователей."""
        with pytest.raises(Exception) as exc_info:
            credentials_exception()
        
        # Проверяем, что это HTTPException с кодом 401
        assert exc_info.value.status_code == 401

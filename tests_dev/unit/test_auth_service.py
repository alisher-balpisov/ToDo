import pytest
from fastapi import HTTPException
from jose import jwt

from src.auth.schemas import UserRegisterSchema
from src.auth.service import (get_current_user, get_user_by_id,
                              get_user_by_username, register_service)
from src.core.config import settings


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
        register_service(
            session=db_session, username=user_data.username, password=user_data.password)
        user = get_user_by_username(
            session=db_session, username=user_data.username)

        assert user.username == "newuser"
        assert user.verify_password("Password123")
        assert user.id is not None

    def test_get_current_user_valid_token(self, db_session, test_user):
        """Тест получения текущего пользователя с валидным токеном."""
        token = test_user.token()

        current_user = get_current_user(db_session, token)

        assert current_user.id == test_user.id
        assert current_user.username == test_user.username

    def test_get_current_user_invalid_token(self, db_session):
        """Тест получения текущего пользователя с невалидным токеном."""
        with pytest.raises(HTTPException):
            get_current_user(db_session, "invalid_token")

    def test_get_current_user_expired_token(self, db_session, test_user):
        """Тест получения пользователя с истекшим токеном."""
        # Создаем токен с прошедшим временем
        from datetime import datetime, timedelta, timezone

        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        payload = {"exp": past_time, "sub": test_user.username}
        expired_token = jwt.encode(
            payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

        with pytest.raises(HTTPException):  # credentials_exception
            get_current_user(db_session, expired_token)

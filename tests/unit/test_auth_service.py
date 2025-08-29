from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from src.auth.schemas import UserRegisterSchema
from src.auth.service import (get_current_user, get_user_by_id,
                              get_user_by_username, register_service)
from src.core.config import settings
from src.core.exception import (InvalidCredentialsException,
                                TokenExpiredException)


@pytest.mark.unit
class TestAuthService:
    """Юнит-тесты для сервисного слоя аутентификации."""

    def test_get_user_by_username_for_existing_user_returns_user(self, db_session, test_user):
        """Тест поиска существующего пользователя по имени должен вернуть объект пользователя."""
        # Arrange
        username = test_user.username

        # Act
        user = await get_user_by_username(db_session, username)

        # Assert
        assert user is not None
        assert user.username == username
        assert user.id == test_user.id

    def test_get_user_by_username_for_nonexistent_user_returns_none(self, db_session):
        """Тест поиска несуществующего пользователя по имени должен вернуть None."""
        # Arrange
        username = "nonexistent"

        # Act
        user = await get_user_by_username(db_session, username)

        # Assert
        assert user is None

    async def test_get_user_by_id_for_existing_user_returns_user(self, db_session, test_user):
        """Тест поиска существующего пользователя по ID должен вернуть объект пользователя."""
        # Arrange
        user_id = test_user.id

        # Act
        user = await get_user_by_id(db_session, user_id)

        # Assert
        assert user is not None
        assert user.id == user_id
        assert user.username == test_user.username

    async def test_get_user_by_id_for_nonexistent_user_returns_none(self, db_session):
        """Тест поиска несуществующего пользователя по ID должен вернуть None."""
        # Arrange
        user_id = 9999

        # Act
        user = await get_user_by_id(db_session, user_id)

        # Assert
        assert user is None

    def test_register_service_with_valid_data_creates_user(self, db_session):
        """Тест успешного создания пользователя через сервис регистрации."""
        # Arrange
        username = "newuser"
        password = "Password123"

        # Act
        # register_service does not return the user object
        register_service(
            session=db_session,
            username=username,
            password=password
        )
        # Fetch the user from DB to verify creation
        created_user = await get_user_by_username(db_session, username)

        # Assert
        assert created_user is not None
        assert created_user.username == username
        assert created_user.verify_password(password)
        assert created_user.id is not None

    def test_get_current_user_with_valid_token_returns_user(self, db_session, test_user):
        """Тест получения текущего пользователя с валидным токеном."""
        # Arrange
        token = test_user.token()

        # Act
        current_user = get_current_user(db_session, token)

        # Assert
        assert current_user.id == test_user.id
        assert current_user.username == test_user.username

    def test_get_current_user_with_invalid_token_raises_invalid_credentials(self, db_session):
        """Тест получения текущего пользователя с невалидным токеном должен вызвать исключение."""
        # Arrange
        invalid_token = "this.is.an.invalid.token"

        # Act & Assert
        with pytest.raises(InvalidCredentialsException) as exc_info:
            get_current_user(db_session, invalid_token)

        assert exc_info.value.error_code == "INVALID_CREDENTIALS"

    def test_get_current_user_with_expired_token_raises_token_expired(self, db_session, test_user):
        """Тест получения пользователя с истекшим токеном должен вызвать исключение."""
        # Arrange
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        payload = {"exp": past_time, "sub": test_user.username}
        expired_token = jwt.encode(
            payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

        # Act & Assert
        with pytest.raises(TokenExpiredException) as exc_info:
            get_current_user(db_session, expired_token)

        assert exc_info.value.error_code == "TOKEN_EXPIRED"
        assert exc_info.value.token_type == "access"

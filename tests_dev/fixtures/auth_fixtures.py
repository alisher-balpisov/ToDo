from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from src.core.config import TODO_JWT_ALG, TODO_JWT_SECRET


@pytest.fixture
def expired_token(test_user):
    """Создает истекший JWT токен."""
    past_time = datetime.now(timezone.utc) - timedelta(hours=1)
    payload = {"exp": past_time, "sub": test_user.username}
    return jwt.encode(payload, TODO_JWT_SECRET, algorithm=TODO_JWT_ALG)


@pytest.fixture
def invalid_token():
    """Возвращает невалидный токен."""
    return "invalid.jwt.token"


@pytest.fixture
def admin_user(db_session):
    """Создает пользователя-администратора."""
    from src.auth.schemas import UserRegisterSchema
    from src.auth.service import create

    user_data = UserRegisterSchema(username="admin", password="AdminPass123")
    admin = create(session=db_session, user_in=user_data)
    admin.is_admin = True  # Если у вас есть поле is_admin
    db_session.commit()
    return admin


@pytest.fixture
def admin_headers(admin_user):
    """Заголовки авторизации для администратора."""
    token = admin_user.get_token
    return {"Authorization": f"Bearer {token}"}

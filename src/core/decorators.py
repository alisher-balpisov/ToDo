import inspect
import logging
from functools import wraps
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exception import (InvalidInputException,
                                MissingRequiredFieldException)

logger = logging.getLogger(__name__)


def _get_and_validate_session(
    func_name: str,
    args: Tuple,
    kwargs: Dict[str, Any],
    commit: bool
) -> Optional[AsyncSession]:
    """Извлекает и валидирует сессию из аргументов функции."""
    if not commit:
        return None

    session = kwargs.get("session")
    if session is None and args:
        possible_session = args[0]
        if isinstance(possible_session, AsyncSession):
            session = possible_session

    if session is None:
        raise MissingRequiredFieldException(
            f"аргумент 'session' обязателен в функции '{func_name}'"
        )

    if not isinstance(session, AsyncSession):
        raise InvalidInputException(
            "session",
            type(session).__name__,
            "объект класса 'AsyncSession'"
        )

    return session


def _log_exception(func_name: str) -> None:
    """Логирует исключение с контекстом функции."""
    logger.exception("[service] Ошибка в '%s'", func_name)


async def _execute_async(func, commit, *args, **kwargs):
    """Выполняет асинхронную функцию с управлением транзакциями."""
    session = kwargs.get("session")
    try:
        result = await func(*args, **kwargs)
        if commit and session is not None:
            await session.commit()
        return result
    except Exception:
        if session is not None:
            await session.rollback()
        _log_exception(func.__name__)
        raise


def service_method(commit: bool = True):
    """
    Декоратор для методов сервиса с автоматическим управлением транзакциями.

    Args:
        commit: Если True, автоматически коммитит транзакцию при успехе
                и делает rollback при ошибке.
    """
    def decorator(func):
        if not inspect.iscoroutinefunction(func):
            raise TypeError(
                f"Функция '{func.__name__}' должна быть async для "
                f"использования с @service_method"
            )

        @wraps(func)
        async def wrapper(*args, **kwargs):
            session = _get_and_validate_session(
                func.__name__, args, kwargs, commit)
            if 'session' not in kwargs:
                kwargs['session'] = session
            return await _execute_async(func, commit, *args, **kwargs)

        return wrapper
    return decorator

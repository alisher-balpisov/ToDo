import inspect
import logging
from functools import wraps
from typing import Any, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exception import (InvalidInputException,
                                MissingRequiredFieldException)

logger = logging.getLogger(__name__)


def _get_and_validate_session(
    func: Callable,
    args: tuple,
    kwargs: dict[str, Any],
    commit: bool
) -> AsyncSession | None:
    """Извлекает и валидирует сессию из аргументов функции."""
    if not commit:
        return None
    session = None
    
    try:
        sig = inspect.signature(func)
        bound_args = sig.bind_partial(*args, **kwargs)
        session = bound_args.arguments.get('session')
    except TypeError:
        pass

    if session is None:
        raise MissingRequiredFieldException(
            f"аргумент 'session' обязателен в функции '{func.__name__}'"
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


async def _execute_async(func, db_session, commit, *args, **kwargs):
    """Выполняет асинхронную функцию с управлением транзакциями."""
    try:
        result = await func(*args, **kwargs)
        if commit and db_session is not None:
            await db_session.commit()
        return result
    except Exception:
        if db_session is not None:
            await db_session.rollback()
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
            session = _get_and_validate_session(func, args, kwargs, commit)
            return await _execute_async(func, session, commit, *args, **kwargs)

        return wrapper
    return decorator

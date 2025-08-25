import logging
from functools import wraps

from sqlalchemy.orm import Session

from src.core.exception import InvalidInputException, MissingRequiredFieldException


logger = logging.getLogger(__name__)


def handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Логируем с полным стеком
            logger.exception("[handler] Ошибка в '%s': %s",
                             func.__name__, str(e), exc_info=True)
            raise
    return wrapper


def transactional(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        session = kwargs.get("session")
        if session is None and args:
            session = args[0]

        if session is None:
            raise MissingRequiredFieldException(
                f"аргумент 'session' в функции '{func.__name__}'")

        if not isinstance(session, Session):
            raise InvalidInputException(
                "session", type(session).__name__, "объект класса 'Session'")

        try:
            result = func(*args, **kwargs)
            session.commit()
            return result
        except Exception:
            session.rollback()
            raise
    return wrapper

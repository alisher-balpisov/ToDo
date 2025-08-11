from logging import getLogger
from typing import NoReturn

from fastapi import HTTPException, status

logger = getLogger()


def handle_server_exception(e: Exception, message: str = "Ошибка сервера") -> NoReturn:
    logger.exception(message)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=[{"msg": f"{message}: {str(e)}"}]
    )

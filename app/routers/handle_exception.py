from logging import getLogger

from fastapi import HTTPException

logger = getLogger()


def check_handle_exception(e: Exception, message: str = "Ошибка сервера"):
    logger.exception(message)
    raise HTTPException(status_code=500, detail=f"{message}: {str(e)}")

# src/core/exception_handlers.py
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette import status

from .exception import (ApiRateLimitException, AuthenticationException,
                        BaseProjectException, BusinessLogicException,
                        BusinessRuleViolationException, ConfigurationException,
                        DataFormatException, ExternalServiceException,
                        InsufficientPermissionsException,
                        InvalidConfigurationException,
                        InvalidCredentialsException, InvalidInputException,
                        InvalidOperationException,
                        MissingConfigurationException,
                        MissingRequiredFieldException,
                        ResourceAlreadyExistsException, ResourceException,
                        ResourceNotFoundException,
                        ResourceUnavailableException,
                        ServiceUnavailableException, TokenExpiredException,
                        ValidationException)

EXCEPTION_STATUS_MAP = {
    # Validation
    ValidationException: status.HTTP_400_BAD_REQUEST,
    InvalidInputException: status.HTTP_400_BAD_REQUEST,
    MissingRequiredFieldException: status.HTTP_400_BAD_REQUEST,
    DataFormatException: status.HTTP_422_UNPROCESSABLE_ENTITY,

    # Auth
    AuthenticationException: status.HTTP_401_UNAUTHORIZED,
    InvalidCredentialsException: status.HTTP_401_UNAUTHORIZED,
    TokenExpiredException: status.HTTP_401_UNAUTHORIZED,
    InsufficientPermissionsException: status.HTTP_403_FORBIDDEN,

    # Resources
    ResourceException: status.HTTP_404_NOT_FOUND,
    ResourceNotFoundException: status.HTTP_404_NOT_FOUND,
    ResourceAlreadyExistsException: status.HTTP_409_CONFLICT,
    ResourceUnavailableException: status.HTTP_503_SERVICE_UNAVAILABLE,

    # Business logic
    BusinessLogicException: status.HTTP_400_BAD_REQUEST,
    InvalidOperationException: status.HTTP_400_BAD_REQUEST,
    BusinessRuleViolationException: status.HTTP_422_UNPROCESSABLE_ENTITY,

    # External services
    ExternalServiceException: status.HTTP_502_BAD_GATEWAY,
    ServiceUnavailableException: status.HTTP_503_SERVICE_UNAVAILABLE,
    ApiRateLimitException: status.HTTP_429_TOO_MANY_REQUESTS,

    # Configuration
    ConfigurationException: status.HTTP_500_INTERNAL_SERVER_ERROR,
    MissingConfigurationException: status.HTTP_500_INTERNAL_SERVER_ERROR,
    InvalidConfigurationException: status.HTTP_500_INTERNAL_SERVER_ERROR,

    # Base fallback
    BaseProjectException: status.HTTP_500_INTERNAL_SERVER_ERROR,
}


async def generic_exception_handler(request: Request, exc: BaseProjectException) -> JSONResponse:
    """Универсальный обработчик для всех исключений проекта."""
    status_code = EXCEPTION_STATUS_MAP.get(
        type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    return JSONResponse(
        status_code=status_code,
        content=exc.to_dict()
    )


def register_exception_handlers(app):
    """Регистрирует обработчики для всех исключений проекта."""
    for exc_cls in EXCEPTION_STATUS_MAP.keys():
        app.add_exception_handler(exc_cls, generic_exception_handler)

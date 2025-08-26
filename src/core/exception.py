import logging
from typing import Any

logger = logging.getLogger(__name__)


# БАЗОВЫЕ ИСКЛЮЧЕНИЯ
# =============================================================================
class BaseProjectException(Exception):
    """
    Базовый класс исключений для всех исключений, специфичных для проекта.

    Предоставляет общую функциональность для отслеживания ошибок, логирования и отладки.
    """

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
        original_exception: Exception | None = None
    ):
        """
        Инициализация базового исключения.

        Args:
            message: Человекочитаемое описание ошибки
            error_code: Уникальный идентификатор типа ошибки
            details: Дополнительная контекстная информация
            original_exception: Обернутое исключение, если применимо
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.original_exception = original_exception

        # Логируем создание исключения для отладки
        logger.debug(f"Создано исключение: {self.error_code} - {message}")

    def to_dict(self) -> dict[str, Any]:
        """Преобразование исключения в словарь для сериализации."""
        return {
            'error_type': self.__class__.__name__,
            'error_code': self.error_code,
            'message': self.message,
            'details': self.details
        }

    def __str__(self) -> str:
        """Строковое представление с кодом ошибки."""
        if self.error_code != self.__class__.__name__:
            return f"[{self.error_code}] {self.message}"
        return self.message

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BaseProjectException):
            return False
        return (
            self.message == other.message
            and self.error_code == other.error_code
            and self.details == other.details
        )

# ИСКЛЮЧЕНИЯ ВАЛИДАЦИИ
# =============================================================================


class ValidationException(BaseProjectException):
    """Базовый класс для всех исключений, связанных с валидацией."""
    pass


class InvalidInputException(ValidationException):
    """Возникает когда входные данные не проходят проверки валидации."""

    def __init__(
        self,
        field_name: str,
        provided_value: Any,
        expected_format: str,
        message: str | None = None
    ):
        self.field_name = field_name
        self.provided_value = provided_value
        self.expected_format = expected_format

        if message is None:
            message = (
                f"Некорректные входные данные для поля '{field_name}': "
                f"получено '{provided_value}', ожидалось {expected_format}"
            )

        details = {
            'field_name': field_name,
            'provided_value': str(provided_value),
            'expected_format': expected_format
        }

        super().__init__(message, 'INVALID_INPUT', details)


class MissingRequiredFieldException(ValidationException):
    """Возникает когда обязательные поля отсутствуют во входных данных."""

    def __init__(self, field_names: str | list):
        if isinstance(field_names, str):
            field_names = [field_names]

        self.missing_fields = field_names

        if len(field_names) == 1:
            message = f"Отсутствует обязательное поле '{field_names[0]}'"
        else:
            fields_str = "', '".join(field_names)
            message = f"Отсутствуют обязательные поля: '{fields_str}'"

        details = {'missing_fields': field_names}
        super().__init__(message, 'MISSING_REQUIRED_FIELD', details)


class DataFormatException(ValidationException):
    """Возникает когда формат данных не соответствует ожидаемой структуре."""

    def __init__(self, expected_format: str, actual_format: str, data_sample: str = ""):
        self.expected_format = expected_format
        self.actual_format = actual_format
        self.data_sample = data_sample

        message = f"Несоответствие формата данных: ожидается {expected_format}, получен {actual_format}"
        if data_sample:
            message += f". Пример данных: {data_sample}"

        details = {
            'expected_format': expected_format,
            'actual_format': actual_format,
            'data_sample': data_sample
        }

        super().__init__(message, 'DATA_FORMAT_ERROR', details)


# ИСКЛЮЧЕНИЯ АУТЕНТИФИКАЦИИ И АВТОРИЗАЦИИ
# =============================================================================
class AuthenticationException(BaseProjectException):
    """Базовый класс для исключений, связанных с аутентификацией."""
    pass


class InvalidCredentialsException(AuthenticationException):
    """Возникает когда предоставленные учетные данные некорректны."""

    def __init__(self, username: str | None = None):
        self.username = username

        if username:
            message = f"Некорректные учетные данные для пользователя '{username}'"
            details = {'username': username}
        else:
            message = "Предоставлены некорректные учетные данные"
            details = {}

        super().__init__(message, 'INVALID_CREDENTIALS', details)


class TokenExpiredException(AuthenticationException):
    """Возникает когда срок действия токена аутентификации истек."""

    def __init__(self, token_type: str = "access", expired_at: str | None = None):
        self.token_type = token_type
        self.expired_at = expired_at

        message = f"Срок действия токена аутентификации ({token_type}) истек"
        if expired_at:
            message += f" в {expired_at}"

        details = {
            'token_type': token_type,
            'expired_at': expired_at
        }

        super().__init__(message, 'TOKEN_EXPIRED', details)


class InsufficientPermissionsException(AuthenticationException):
    """Возникает когда у пользователя недостаточно прав для выполнения операции."""

    def __init__(self, required_permission: str, user_role: str | None = None):
        self.required_permission = required_permission
        self.user_role = user_role

        message = f"Недостаточно прав: требуется '{required_permission}'"
        if user_role:
            message += f" (текущая роль: {user_role})"

        details = {
            'required_permission': required_permission,
            'user_role': user_role
        }

        super().__init__(message, 'INSUFFICIENT_PERMISSIONS', details)


# ИСКЛЮЧЕНИЯ РЕСУРСОВ
# =============================================================================
class ResourceException(BaseProjectException):
    """Базовый класс для исключений, связанных с ресурсами."""
    pass


class ResourceNotFoundException(ResourceException):
    """Возникает когда запрашиваемый ресурс не может быть найден."""

    def __init__(self, resource_type: str, resource_id: str | int):
        self.resource_type = resource_type
        self.resource_id = str(resource_id)

        message = f"{resource_type} с ID '{resource_id}' не найденa"
        details = {
            'resource_type': resource_type,
            'resource_id': self.resource_id
        }

        super().__init__(message, 'RESOURCE_NOT_FOUND', details)


class ResourceAlreadyExistsException(ResourceException):
    """Возникает при попытке создать ресурс, который уже существует."""

    def __init__(self, resource_type: str, identifier: str):
        self.resource_type = resource_type
        self.identifier = identifier

        message = f"{resource_type} с идентификатором '{identifier}' уже существует"
        details = {
            'resource_type': resource_type,
            'identifier': identifier
        }

        super().__init__(message, 'RESOURCE_ALREADY_EXISTS', details)


class ResourceUnavailableException(ResourceException):
    """Возникает когда ресурс существует, но временно недоступен."""

    def __init__(self, resource_type: str, resource_id: str, reason: str = ""):
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.reason = reason

        message = f"{resource_type} '{resource_id}' временно недоступен"
        if reason:
            message += f": {reason}"

        details = {
            'resource_type': resource_type,
            'resource_id': resource_id,
            'reason': reason
        }

        super().__init__(message, 'RESOURCE_UNAVAILABLE', details)


# ИСКЛЮЧЕНИЯ БИЗНЕС-ЛОГИКИ
# =============================================================================
class BusinessLogicException(BaseProjectException):
    """Базовый класс для нарушений бизнес-правил."""
    pass


class InvalidOperationException(BusinessLogicException):
    """Возникает когда операция не разрешена в текущем состоянии."""

    def __init__(self, operation: str, current_state: str, reason: str = ""):
        self.operation = operation
        self.current_state = current_state
        self.reason = reason

        message = f"Операция '{operation}' не разрешена в состоянии '{current_state}'"
        if reason:
            message += f": {reason}"

        details = {
            'operation': operation,
            'current_state': current_state,
            'reason': reason
        }

        super().__init__(message, 'INVALID_OPERATION', details)


class BusinessRuleViolationException(BusinessLogicException):
    """Возникает при нарушении бизнес-правил."""

    def __init__(self, rule_name: str, violation_details: str):
        self.rule_name = rule_name
        self.violation_details = violation_details

        message = f"Нарушение бизнес-правила: {rule_name} - {violation_details}"
        details = {
            'rule_name': rule_name,
            'violation_details': violation_details
        }

        super().__init__(message, 'BUSINESS_RULE_VIOLATION', details)


# ИСКЛЮЧЕНИЯ ВНЕШНИХ СЕРВИСОВ
# =============================================================================
class ExternalServiceException(BaseProjectException):
    """Базовый класс для ошибок связи с внешними сервисами."""
    pass


class ServiceUnavailableException(ExternalServiceException):
    """Возникает когда внешний сервис недоступен."""

    def __init__(self, service_name: str, status_code: int | None = None):
        self.service_name = service_name
        self.status_code = status_code

        message = f"Сервис '{service_name}' недоступен"
        if status_code:
            message += f" (HTTP {status_code})"

        details = {
            'service_name': service_name,
            'status_code': status_code
        }

        super().__init__(message, 'SERVICE_UNAVAILABLE', details)


class ApiRateLimitException(ExternalServiceException):
    """Возникает при превышении лимита запросов к API."""

    def __init__(self, service_name: str, reset_time: str | None = None):
        self.service_name = service_name
        self.reset_time = reset_time

        message = f"Превышен лимит запросов к сервису '{service_name}'"
        if reset_time:
            message += f". Сброс лимита в: {reset_time}"

        details = {
            'service_name': service_name,
            'reset_time': reset_time
        }

        super().__init__(message, 'API_RATE_LIMIT_EXCEEDED', details)


# ИСКЛЮЧЕНИЯ КОНФИГУРАЦИИ
# =============================================================================
class ConfigurationException(BaseProjectException):
    """Базовый класс для исключений, связанных с конфигурацией."""
    pass


class MissingConfigurationException(ConfigurationException):
    """Возникает когда отсутствует обязательная конфигурация."""

    def __init__(self, config_key: str, config_source: str = "переменные окружения"):
        self.config_key = config_key
        self.config_source = config_source

        message = f"Отсутствует обязательная конфигурация: '{config_key}' в {config_source}"
        details = {
            'config_key': config_key,
            'config_source': config_source
        }

        super().__init__(message, 'MISSING_CONFIGURATION', details)


class InvalidConfigurationException(ConfigurationException):
    """Возникает когда значения конфигурации некорректны."""

    def __init__(self, config_key: str, config_value: str, expected_format: str):
        self.config_key = config_key
        self.config_value = config_value
        self.expected_format = expected_format

        message = (
            f"Некорректная конфигурация для '{config_key}': "
            f"'{config_value}' не соответствует ожидаемому формату: {expected_format}"
        )

        details = {
            'config_key': config_key,
            'config_value': config_value,
            'expected_format': expected_format
        }

        super().__init__(message, 'INVALID_CONFIGURATION', details)


# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =============================================================================
def handle_exception(exception: Exception, context: str = "") -> BaseProjectException:
    """
    Преобразование обычных исключений в исключения, специфичные для проекта.

    Args:
        exception: Исходное исключение для обертывания
        context: Дополнительный контекст о том, где произошло исключение

    Returns:
        Экземпляр исключения, специфичного для проекта
    """
    if isinstance(exception, BaseProjectException):
        return exception

    message = f"Произошла неожиданная ошибка"
    if context:
        message += f" в {context}"
    message += f": {str(exception)}"

    details = {
        'original_exception_type': type(exception).__name__,
        'context': context
    }

    return BaseProjectException(
        message=message,
        error_code='UNEXPECTED_ERROR',
        details=details,
        original_exception=exception
    )


def get_exception_hierarchy() -> dict[str, list]:
    """
    Получение полной иерархии исключений для целей документирования.

    Returns:
        Словарь, сопоставляющий базовые классы с их производными исключениями
    """
    return {
        'BaseProjectException': [
            'ValidationException',
            'AuthenticationException',
            'ResourceException',
            'BusinessLogicException',
            'ExternalServiceException',
            'ConfigurationException'
        ],
        'ValidationException': [
            'InvalidInputException',
            'MissingRequiredFieldException',
            'DataFormatException'
        ],
        'AuthenticationException': [
            'InvalidCredentialsException',
            'TokenExpiredException',
            'InsufficientPermissionsException'
        ],
        'ResourceException': [
            'ResourceNotFoundException',
            'ResourceAlreadyExistsException',
            'ResourceUnavailableException'
        ],
        'BusinessLogicException': [
            'InvalidOperationException',
            'BusinessRuleViolationException'
        ],
        'ExternalServiceException': [
            'ServiceUnavailableException',
            'ApiRateLimitException'
        ],
        'ConfigurationException': [
            'MissingConfigurationException',
            'InvalidConfigurationException'
        ]
    }

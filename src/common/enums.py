from enum import Enum


class SharedAccessEnum(str, Enum):
    view = "view"
    edit = "edit"


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"

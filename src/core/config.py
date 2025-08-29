# src/core/config.py
import secrets
from typing import ClassVar, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MIN_LEN_JWT_SECRET = 32


class Settings(BaseSettings):
    """Безопасная конфигурация приложения."""

    # JWT Configuration
    JWT_SECRET: str = Field(
        # генерируем случайный ключ если не задан
        default_factory=lambda: secrets.token_urlsafe(32),
        description="JWT secret key (minimum 32 characters)"
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60
    JWT_REFRESH_EXPIRATION_MINUTES: int = 10080   # default: 7 дней
    DEFAULT_ENCODING: str = "utf-8"
    MIN_LEN_JWT_SECRET: ClassVar[int] = 32
    # Database
    DATABASE_URL: str | None = None

    DATABASE_DRIVER: str = "postgresql+asyncpg"
    DATABASE_HOSTNAME: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_USER: str = "postgres"
    DATABASE_PASSWORD: str | None = None
    DATABASE_NAME: str = "base_db"
    DATABASE_ECHO: bool = False

    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"{self.DATABASE_DRIVER}://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOSTNAME}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )

    # Security
    BCRYPT_ROUNDS: int = 12   # количество раундов хэширования паролей
    PASSWORD_MIN_LENGTH: int = 8
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_TIME_MINUTES: int = 5

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # File Upload
    MAX_FILE_SIZE_MB: int = 20
    MAX_FILE_SIZE: int = MAX_FILE_SIZE_MB * 1024 * 1024
    ALLOWED_EXTENSIONS: tuple[str, ...] = Field(
        default_factory=lambda: (".txt", ".pdf", ".png", ".jpg", ".jpeg")
    )
    ALLOWED_TYPES: tuple[str, ...] = Field(
        default_factory=lambda: (
            "image/png", "image/jpeg", "application/pdf", "text/plain")
    )

    # CORS
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000", "http://localhost:8080"]
    )

    # Environment (режим работы приложения)
    ENVIRONMENT: Literal[
        "development", "production", "testing"] = "development"

    @field_validator("JWT_SECRET")
    def validate_jwt_secret(cls, v):
        """Проверка, что ключ достаточно длинный для безопасности."""
        if len(v) < cls.MIN_LEN_JWT_SECRET:
            raise ValueError(
                f"JWT_SECRET должен содержать не менее {cls.MIN_LEN_JWT_SECRET} символов")
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,   # имена переменных чувствительны к регистру
        extra="ignore"    # игнорировать лишние переменные в .env
    )


settings = Settings()

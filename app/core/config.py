from typing import Optional
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or .env file."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application Settings
    PROJECT_NAME: str = "Enterprise SaaS Auth API"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"

    # AI Configuration
    OPENAI_API_KEY: Optional[str] = None

    # Security & Authentication
    SECRET_KEY: str = "super-secret-key-change-this-in-production-for-jwt-signing"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    EMAIL_RESET_TOKEN_EXPIRE_MINUTES: int = 30
    EMAIL_VERIFY_TOKEN_EXPIRE_HOURS: int = 24

    # Database (PostgreSQL)
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "saas_auth_db"
    DATABASE_URI_OVERRIDE: Optional[str] = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URI(self) -> str:
        """Construct PostgreSQL async URI."""
        if self.DATABASE_URI_OVERRIDE:
            return self.DATABASE_URI_OVERRIDE
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def TORTOISE_URI(self) -> str:
        """Construct Tortoise ORM compatible URI."""
        if self.DATABASE_URI_OVERRIDE:
            uri = self.DATABASE_URI_OVERRIDE
        else:
            uri = (
                f"postgres://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        if uri.startswith("postgresql+asyncpg://"):
            uri = uri.replace("postgresql+asyncpg://", "postgres://", 1)
        elif uri.startswith("postgresql://"):
            uri = uri.replace("postgresql://", "postgres://", 1)
        if "?ssl=" in uri:
            uri = uri.split("?ssl=")[0]
        return uri

    @computed_field  # type: ignore[prop-decorator]
    @property
    def TORTOISE_ORM(self) -> dict:
        """Tortoise ORM configuration dictionary for Aerich and runtime initialization."""
        return {
            "connections": {"default": self.TORTOISE_URI},
            "apps": {
                "models": {
                    "models": [
                        "app.models.user", 
                        "app.models.organization",
                        "app.models.workspace",
                        "app.models.document",
                        "aerich.models"
                    ],
                    "default_connection": "default",
                },
            },
        }

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = ""
    REDIS_DB: int = 0
    REDIS_URI_OVERRIDE: Optional[str] = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def REDIS_URI(self) -> str:
        """Construct Redis URI."""
        if self.REDIS_URI_OVERRIDE:
            return self.REDIS_URI_OVERRIDE
        auth_part = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Email Delivery (SMTP)
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: Optional[str] = ""
    SMTP_PASSWORD: Optional[str] = ""
    SMTP_TLS: bool = False
    SMTP_SSL: bool = False
    EMAILS_FROM_EMAIL: str = "noreply@enterprisesaas.com"
    EMAILS_FROM_NAME: str = "Enterprise SaaS Security"


settings = Settings()
TORTOISE_ORM_CONFIG = settings.TORTOISE_ORM

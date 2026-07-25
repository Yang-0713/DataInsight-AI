from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration loaded from environment variables or backend/.env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="DATAINSIGHT_",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "DataInsight AI"
    environment: str = "development"
    debug: bool = False
    api_prefix: str = "/api"
    auto_create_tables: bool = True

    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "datainsight_ai"

    jwt_secret_key: SecretStr = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=60, ge=5, le=1440)

    cors_origins: list[str] = [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ]

    @property
    def database_url(self) -> str:
        username = quote_plus(self.mysql_user)
        password = quote_plus(self.mysql_password)
        return (
            f"mysql+pymysql://{username}:{password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            "?charset=utf8mb4"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()

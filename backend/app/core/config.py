from functools import lru_cache
from pathlib import Path
from typing import Literal
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

    dataset_storage_dir: Path = Path("../datasets")
    report_storage_dir: Path = Path("../reports")
    max_upload_size_mb: int = Field(default=50, ge=1, le=500)
    max_ml_rows: int = Field(default=5000, ge=100, le=50000)

    openai_api_key: SecretStr | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-5.6-terra"
    openai_api_mode: Literal["responses", "chat_completions"] = "responses"
    openai_reasoning_effort: Literal["none", "low", "medium", "high", "xhigh"] = (
        "medium"
    )
    openai_max_output_tokens: int = Field(default=1200, ge=200, le=16000)
    openai_timeout_seconds: float = Field(default=60, ge=5, le=300)
    ai_max_history_messages: int = Field(default=12, ge=0, le=30)

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

    @property
    def dataset_storage_path(self) -> Path:
        return self.dataset_storage_dir.expanduser().resolve()

    @property
    def report_storage_path(self) -> Path:
        return self.report_storage_dir.expanduser().resolve()

    @property
    def ai_configured(self) -> bool:
        return bool(
            self.openai_api_key
            and self.openai_api_key.get_secret_value().strip()
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()

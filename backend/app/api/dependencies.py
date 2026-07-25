from pathlib import Path
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.ai.provider import AIProvider, OpenAICompatibleProvider
from app.core.security import decode_access_token
from app.core.config import get_settings
from app.database.session import get_db
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)

DatabaseSession = Annotated[Session, Depends(get_db)]
BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(bearer_scheme),
]


def get_current_user(
    credentials: BearerCredentials, database: DatabaseSession
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="登录状态无效或已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise credentials_error

    try:
        payload = decode_access_token(credentials.credentials)
        if payload.get("type") != "access":
            raise credentials_error
        user_id = int(payload.get("sub", ""))
    except (jwt.InvalidTokenError, TypeError, ValueError):
        raise credentials_error from None

    user = database.get(User, user_id)
    if user is None:
        raise credentials_error
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_dataset_storage() -> Path:
    return get_settings().dataset_storage_path


DatasetStorage = Annotated[Path, Depends(get_dataset_storage)]


def get_report_storage() -> Path:
    return get_settings().report_storage_path


ReportStorage = Annotated[Path, Depends(get_report_storage)]


def get_ai_provider() -> AIProvider:
    settings = get_settings()
    if not settings.ai_configured or settings.openai_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "AI 服务尚未配置，请在 backend/.env 中设置 "
                "DATAINSIGHT_OPENAI_API_KEY"
            ),
        )
    return OpenAICompatibleProvider(
        api_key=settings.openai_api_key.get_secret_value(),
        base_url=settings.openai_base_url,
        model=settings.openai_model,
        api_mode=settings.openai_api_mode,
        reasoning_effort=settings.openai_reasoning_effort,
        max_output_tokens=settings.openai_max_output_tokens,
        timeout_seconds=settings.openai_timeout_seconds,
    )


AIProviderDependency = Annotated[AIProvider, Depends(get_ai_provider)]

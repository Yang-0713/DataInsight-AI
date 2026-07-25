from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
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

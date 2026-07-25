from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User, UserRole
from app.schemas.auth import RegisterRequest


def get_user_by_identity(database: Session, identity: str) -> User | None:
    normalized_email = identity.lower()
    statement = select(User).where(
        or_(User.username == identity, User.email == normalized_email)
    )
    return database.scalar(statement)


def get_user_by_username(database: Session, username: str) -> User | None:
    return database.scalar(select(User).where(User.username == username))


def get_user_by_email(database: Session, email: str) -> User | None:
    return database.scalar(select(User).where(User.email == email.lower()))


def create_user(database: Session, payload: RegisterRequest) -> User:
    user = User(
        username=payload.username,
        email=str(payload.email).lower(),
        password_hash=hash_password(payload.password),
        role=UserRole.USER,
    )
    database.add(user)
    database.commit()
    database.refresh(user)
    return user


def authenticate_user(
    database: Session, identity: str, password: str
) -> User | None:
    user = get_user_by_identity(database, identity)
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user

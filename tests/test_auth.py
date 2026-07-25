from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.session import get_db
from app.main import app

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


def override_get_db() -> Generator[Session, None, None]:
    database = TestingSessionLocal()
    try:
        yield database
    finally:
        database.close()


@pytest.fixture(autouse=True)
def database_schema() -> Generator[None, None, None]:
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    test_client = TestClient(app)
    yield test_client
    test_client.close()


def register_user() -> dict[str, str]:
    return {
        "username": "analyst",
        "email": "analyst@example.com",
        "password": "DataInsight123!",
    }


def test_register_login_and_get_current_user(client: TestClient) -> None:
    payload = register_user()

    register_response = client.post("/api/auth/register", json=payload)
    assert register_response.status_code == 201
    assert register_response.json()["role"] == "USER"
    assert "password_hash" not in register_response.json()

    login_response = client.post(
        "/api/auth/login",
        json={"identity": payload["email"], "password": payload["password"]},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["username"] == payload["username"]


def test_register_rejects_duplicate_identity(client: TestClient) -> None:
    payload = register_user()
    assert client.post("/api/auth/register", json=payload).status_code == 201

    duplicate_response = client.post("/api/auth/register", json=payload)
    assert duplicate_response.status_code == 409


def test_login_rejects_wrong_password(client: TestClient) -> None:
    payload = register_user()
    client.post("/api/auth/register", json=payload)

    response = client.post(
        "/api/auth/login",
        json={"identity": payload["username"], "password": "WrongPassword123!"},
    )
    assert response.status_code == 401


def test_protected_route_requires_token(client: TestClient) -> None:
    response = client.get("/api/auth/me")
    assert response.status_code == 401

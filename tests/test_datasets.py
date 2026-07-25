from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_dataset_storage
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
def database_schema(tmp_path: Path) -> Generator[None, None, None]:
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_dataset_storage] = lambda: tmp_path
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    test_client = TestClient(app)
    yield test_client
    test_client.close()


def create_account_and_token(
    client: TestClient,
    *,
    username: str = "analyst",
    email: str = "analyst@example.com",
) -> str:
    password = "DataInsight123!"
    register_response = client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={"identity": email, "password": password},
    )
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_upload_list_detail_and_delete_dataset(
    client: TestClient, tmp_path: Path
) -> None:
    token = create_account_and_token(client)
    headers = auth_headers(token)
    csv_content = b"month,sales,region\nJan,10,East\nFeb,12,West\n"

    upload_response = client.post(
        "/api/datasets/upload",
        headers=headers,
        files={"file": ("sales.csv", csv_content, "text/csv")},
    )
    assert upload_response.status_code == 201
    dataset = upload_response.json()
    assert dataset["filename"] == "sales.csv"
    assert dataset["rows"] == 2
    assert dataset["columns"] == 3
    assert list(tmp_path.rglob("*.csv"))

    list_response = client.get("/api/datasets", headers=headers)
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [dataset["id"]]

    detail_response = client.get(
        f"/api/datasets/{dataset['id']}",
        headers=headers,
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["filename"] == "sales.csv"

    delete_response = client.delete(
        f"/api/datasets/{dataset['id']}",
        headers=headers,
    )
    assert delete_response.status_code == 204
    assert not list(tmp_path.rglob("*.csv"))
    assert client.get(
        f"/api/datasets/{dataset['id']}",
        headers=headers,
    ).status_code == 404


def test_dataset_is_private_to_its_owner(client: TestClient) -> None:
    owner_token = create_account_and_token(client)
    other_token = create_account_and_token(
        client,
        username="reviewer",
        email="reviewer@example.com",
    )
    upload_response = client.post(
        "/api/datasets/upload",
        headers=auth_headers(owner_token),
        files={"file": ("private.csv", b"id,value\n1,42\n", "text/csv")},
    )
    dataset_id = upload_response.json()["id"]

    assert client.get(
        f"/api/datasets/{dataset_id}",
        headers=auth_headers(other_token),
    ).status_code == 404
    assert client.delete(
        f"/api/datasets/{dataset_id}",
        headers=auth_headers(other_token),
    ).status_code == 404


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("notes.txt", b"a,b\n1,2\n"),
        ("broken.csv", b""),
    ],
)
def test_upload_rejects_unsupported_or_empty_files(
    client: TestClient,
    filename: str,
    content: bytes,
) -> None:
    token = create_account_and_token(client)
    response = client.post(
        "/api/datasets/upload",
        headers=auth_headers(token),
        files={"file": (filename, content, "text/plain")},
    )
    assert response.status_code == 422


def test_dataset_routes_require_authentication(client: TestClient) -> None:
    assert client.get("/api/datasets").status_code == 401

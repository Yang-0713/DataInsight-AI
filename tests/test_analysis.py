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
    with TestClient(app) as test_client:
        yield test_client


def create_account_and_token(
    client: TestClient,
    *,
    username: str = "analyst",
    email: str = "analyst@example.com",
) -> str:
    password = "DataInsight123!"
    assert client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": password},
    ).status_code == 201
    response = client.post(
        "/api/auth/login",
        json={"identity": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def upload_analysis_dataset(client: TestClient, token: str) -> int:
    csv_content = (
        "date,sales,cost,region\n"
        "2026-01-01,100,60,East\n"
        "2026-01-02,120,70,West\n"
        "2026-01-02,120,70,West\n"
        "2026-01-03,,80,East\n"
    ).encode()
    response = client.post(
        "/api/datasets/upload",
        headers=auth_headers(token),
        files={"file": ("sales.csv", csv_content, "text/csv")},
    )
    assert response.status_code == 201
    return int(response.json()["id"])


def test_run_eda_and_read_persisted_result(client: TestClient) -> None:
    token = create_account_and_token(client)
    dataset_id = upload_analysis_dataset(client, token)

    response = client.post(
        f"/api/analysis/{dataset_id}",
        headers=auth_headers(token),
    )
    assert response.status_code == 201
    payload = response.json()
    result = payload["result_json"]

    assert payload["analysis_type"] == "EDA"
    assert result["profile"]["rows"] == 4
    assert result["profile"]["columns"] == 4
    assert result["profile"]["duplicate_rows"] == 1
    assert result["profile"]["missing_cells"] == 1

    sales = next(
        item
        for item in result["statistics"]["numerical"]
        if item["column"] == "sales"
    )
    assert sales["mean"] == pytest.approx(113.333333)
    assert sales["median"] == 120

    chart_types = {chart["type"] for chart in result["visualizations"]}
    assert {"histogram", "boxplot", "bar", "heatmap", "line"} <= chart_types
    assert all("option" in chart for chart in result["visualizations"])

    stored = client.get(
        f"/api/results/{payload['id']}",
        headers=auth_headers(token),
    )
    assert stored.status_code == 200
    assert stored.json()["result_json"] == result


def test_analysis_is_private_to_dataset_owner(client: TestClient) -> None:
    owner_token = create_account_and_token(client)
    other_token = create_account_and_token(
        client,
        username="reviewer",
        email="reviewer@example.com",
    )
    dataset_id = upload_analysis_dataset(client, owner_token)
    result = client.post(
        f"/api/analysis/{dataset_id}",
        headers=auth_headers(owner_token),
    )
    assert result.status_code == 201

    assert client.post(
        f"/api/analysis/{dataset_id}",
        headers=auth_headers(other_token),
    ).status_code == 404
    assert client.get(
        f"/api/results/{result.json()['id']}",
        headers=auth_headers(other_token),
    ).status_code == 404


def test_analysis_routes_require_authentication(client: TestClient) -> None:
    assert client.post("/api/analysis/1").status_code == 401
    assert client.get("/api/results/1").status_code == 401

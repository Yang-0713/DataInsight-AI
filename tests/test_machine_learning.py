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


def upload_csv(
    client: TestClient,
    token: str,
    content: str,
    filename: str = "samples.csv",
) -> int:
    response = client.post(
        "/api/datasets/upload",
        headers=auth_headers(token),
        files={"file": (filename, content.encode(), "text/csv")},
    )
    assert response.status_code == 201
    return int(response.json()["id"])


def machine_learning_csv() -> str:
    rows = ["id,x,y,z,group"]
    for index in range(1, 20):
        x = (index % 5) * 0.1
        y = (index % 3) * 0.15
        z = "" if index == 5 else (index % 4) * 0.2
        rows.append(f"S{index:02d},{x},{y},{z},normal")
    rows.append("S20,9.0,8.5,9.5,outlier")
    return "\n".join(rows) + "\n"


def test_run_machine_learning_and_persist_result(client: TestClient) -> None:
    token = create_account_and_token(client)
    dataset_id = upload_csv(client, token, machine_learning_csv())

    features_response = client.get(
        f"/api/ml/{dataset_id}/features",
        headers=auth_headers(token),
    )
    assert features_response.status_code == 200
    assert features_response.json()["recommended_features"] == ["x", "y", "z"]

    response = client.post(
        f"/api/ml/{dataset_id}",
        headers=auth_headers(token),
        json={"contamination": 0.1, "lof_neighbors": 5},
    )
    assert response.status_code == 201
    payload = response.json()
    result = payload["result_json"]

    assert payload["analysis_type"] == "ML"
    assert result["preprocessing"]["features"] == ["x", "y", "z"]
    assert result["preprocessing"]["sample_count"] == 20
    assert result["preprocessing"]["missing_values_imputed"] == 1
    assert len(result["pca"]["visualization"]) == 20
    assert len(result["pca"]["explained_variance_ratio"]) == 2
    assert result["isolation_forest"]["anomaly_count"] == 2
    assert result["lof"]["anomaly_count"] == 2

    isolation_samples = result["isolation_forest"]["samples"]
    outlier = next(item for item in isolation_samples if item["sample_id"] == "S20")
    assert outlier["label"] == "anomaly"
    assert outlier["anomaly_score"] == pytest.approx(1.0)

    stored = client.get(
        f"/api/results/{payload['id']}",
        headers=auth_headers(token),
    )
    assert stored.status_code == 200
    assert stored.json()["result_json"] == result


def test_machine_learning_accepts_explicit_features(client: TestClient) -> None:
    token = create_account_and_token(client)
    dataset_id = upload_csv(client, token, machine_learning_csv())

    response = client.post(
        f"/api/ml/{dataset_id}",
        headers=auth_headers(token),
        json={"features": ["x", "z"], "contamination": 0.1},
    )
    assert response.status_code == 201
    assert response.json()["result_json"]["preprocessing"]["features"] == ["x", "z"]


def test_machine_learning_is_private_to_owner(client: TestClient) -> None:
    owner_token = create_account_and_token(client)
    other_token = create_account_and_token(
        client,
        username="reviewer",
        email="reviewer@example.com",
    )
    dataset_id = upload_csv(client, owner_token, machine_learning_csv())

    response = client.post(
        f"/api/ml/{dataset_id}",
        headers=auth_headers(other_token),
        json={},
    )
    assert response.status_code == 404


def test_machine_learning_rejects_unsuitable_data(client: TestClient) -> None:
    token = create_account_and_token(client)
    dataset_id = upload_csv(
        client,
        token,
        "city,category\nShanghai,A\nBeijing,B\nShenzhen,A\n",
        "categories.csv",
    )

    response = client.post(
        f"/api/ml/{dataset_id}",
        headers=auth_headers(token),
        json={},
    )
    assert response.status_code == 422
    assert "数值字段" in response.json()["detail"]


def test_machine_learning_requires_authentication(client: TestClient) -> None:
    assert client.post("/api/ml/1", json={}).status_code == 401
    assert client.get("/api/ml/1/features").status_code == 401

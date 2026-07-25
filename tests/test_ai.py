import json
from collections.abc import Generator
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.ai.provider import AICompletion, OpenAICompatibleProvider
from app.api.dependencies import (
    get_ai_provider,
    get_dataset_storage,
    get_report_storage,
)
from app.database.base import Base
from app.database.session import get_db
from app.main import app
from app.models.analysis_result import AnalysisResult

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


class FakeAIProvider:
    provider_name = "fake"
    model_name = "fake-analyst"

    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def complete(
        self,
        *,
        instructions: str,
        input_text: str,
        safety_identifier: str,
    ) -> AICompletion:
        self.calls.append(
            {
                "instructions": instructions,
                "input_text": input_text,
                "safety_identifier": safety_identifier,
            }
        )
        if "合法 JSON 对象" in instructions:
            text = json.dumps(
                {
                    "dataset_summary": "<script>alert('x')</script> 数据概述",
                    "important_findings": ["销售均值约为 113.33"],
                    "possible_problems": ["存在 1 个缺失单元格"],
                    "recommendations": ["复核缺失值对应记录"],
                },
                ensure_ascii=False,
            )
        else:
            text = "结论：数据中存在重复记录和缺失值，建议先完成数据清洗。"
        return AICompletion(
            text=text,
            provider=self.provider_name,
            model=self.model_name,
        )


def override_get_db() -> Generator[Session, None, None]:
    database = TestingSessionLocal()
    try:
        yield database
    finally:
        database.close()


@pytest.fixture(autouse=True)
def database_schema(tmp_path: Path) -> Generator[FakeAIProvider, None, None]:
    provider = FakeAIProvider()
    dataset_root = tmp_path / "datasets"
    report_root = tmp_path / "reports"
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_dataset_storage] = lambda: dataset_root
    app.dependency_overrides[get_report_storage] = lambda: report_root
    app.dependency_overrides[get_ai_provider] = lambda: provider
    yield provider
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


def upload_dataset(client: TestClient, token: str) -> int:
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
        files={"file": ("sales<unsafe>.csv", csv_content, "text/csv")},
    )
    assert response.status_code == 201
    return int(response.json()["id"])


def test_openai_provider_uses_responses_api_and_parses_output() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["authorization"] = request.headers["authorization"]
        captured["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "output": [
                    {
                        "content": [
                            {"type": "output_text", "text": "第一段"},
                            {"type": "output_text", "text": "第二段"},
                        ]
                    }
                ]
            },
        )

    provider = OpenAICompatibleProvider(
        api_key="test-secret",
        base_url="https://api.example.test/v1",
        model="test-model",
        transport=httpx.MockTransport(handler),
    )
    result = provider.complete(
        instructions="system",
        input_text="question",
        safety_identifier="di_test",
    )

    assert result.text == "第一段\n第二段"
    assert captured["path"] == "/v1/responses"
    assert captured["authorization"] == "Bearer test-secret"
    payload = captured["payload"]
    assert isinstance(payload, dict)
    assert payload["model"] == "test-model"
    assert payload["safety_identifier"] == "di_test"


def test_openai_provider_supports_chat_completions_mode() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "兼容回答"}}]},
        )

    provider = OpenAICompatibleProvider(
        api_key="test-secret",
        base_url="https://local.example/v1/",
        model="local-model",
        api_mode="chat_completions",
        transport=httpx.MockTransport(handler),
    )
    result = provider.complete(
        instructions="system",
        input_text="question",
        safety_identifier="di_test",
    )
    assert result.text == "兼容回答"


def test_ai_chat_builds_aggregate_context_and_persists(
    client: TestClient,
    database_schema: FakeAIProvider,
) -> None:
    token = create_account_and_token(client)
    dataset_id = upload_dataset(client, token)

    response = client.post(
        "/api/ai/chat",
        headers=auth_headers(token),
        json={
            "dataset_id": dataset_id,
            "message": "有哪些数据质量问题？",
            "history": [],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["model"] == "fake-analyst"
    assert payload["answer"].startswith("结论")
    assert len(database_schema.calls) == 1
    prompt = database_schema.calls[0]["input_text"]
    assert '"missing_cells":1' in prompt
    assert "2026-01-01,100,60,East" not in prompt
    assert ".csv</filepath>" not in prompt

    stored = client.get(
        f"/api/results/{payload['result_id']}",
        headers=auth_headers(token),
    )
    assert stored.status_code == 200
    assert stored.json()["analysis_type"] == "AI_CHAT"
    with TestingSessionLocal() as database:
        count = database.scalar(select(func.count(AnalysisResult.id)))
    assert count == 2


def test_ai_status_never_exposes_credentials(client: TestClient) -> None:
    token = create_account_and_token(client)
    response = client.get("/api/ai/status", headers=auth_headers(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "openai-compatible"
    assert "api_key" not in payload


def test_generate_download_and_delete_escaped_report(
    client: TestClient,
    tmp_path: Path,
) -> None:
    token = create_account_and_token(client)
    dataset_id = upload_dataset(client, token)

    response = client.post(
        f"/api/reports/{dataset_id}",
        headers=auth_headers(token),
    )
    assert response.status_code == 201
    report = response.json()
    assert report["findings"] == ["销售均值约为 113.33"]

    files = list((tmp_path / "reports").rglob("*.html"))
    assert len(files) == 1
    content = files[0].read_text(encoding="utf-8")
    assert "&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;" in content
    assert "<script>alert('x')</script>" not in content
    assert "sales&lt;unsafe&gt;.csv" in content

    download = client.get(
        f"/api/reports/{report['id']}/download",
        headers=auth_headers(token),
    )
    assert download.status_code == 200
    assert "text/html" in download.headers["content-type"]

    listed = client.get("/api/reports", headers=auth_headers(token))
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [report["id"]]

    deleted = client.delete(
        f"/api/datasets/{dataset_id}",
        headers=auth_headers(token),
    )
    assert deleted.status_code == 204
    assert not files[0].exists()


def test_ai_reports_are_private_to_owner(client: TestClient) -> None:
    owner_token = create_account_and_token(client)
    other_token = create_account_and_token(
        client,
        username="reviewer",
        email="reviewer@example.com",
    )
    dataset_id = upload_dataset(client, owner_token)
    report = client.post(
        f"/api/reports/{dataset_id}",
        headers=auth_headers(owner_token),
    ).json()

    assert client.get(
        f"/api/reports/{report['id']}/download",
        headers=auth_headers(other_token),
    ).status_code == 404
    assert client.post(
        "/api/ai/chat",
        headers=auth_headers(other_token),
        json={"dataset_id": dataset_id, "message": "分析", "history": []},
    ).status_code == 404

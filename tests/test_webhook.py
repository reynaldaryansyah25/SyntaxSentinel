from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api.endpoints import webhook
from app.main import app


client = TestClient(app)


def pipeline_payload(status: str = "failed") -> dict[str, object]:
    return {
        "object_kind": "pipeline",
        "project": {
            "id": 123,
            "web_url": "https://gitlab.com/example/syntaxsentinel-demo",
        },
        "object_attributes": {
            "id": 456,
            "status": status,
            "ref": "main",
            "sha": "abc123",
            "source": "push",
        },
    }


@pytest.fixture(autouse=True)
def webhook_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        webhook,
        "get_settings",
        lambda: SimpleNamespace(gitlab_webhook_secret="expected-secret"),
    )


def test_gitlab_webhook_rejects_invalid_token() -> None:
    response = client.post(
        "/api/v1/webhook/gitlab",
        json=pipeline_payload(),
        headers={"X-Gitlab-Token": "wrong-secret"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid GitLab webhook token"


def test_gitlab_webhook_ignores_non_failed_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []

    async def fake_run_healing_process(**kwargs: object) -> dict[str, object]:
        calls.append(kwargs)
        return {"status": "called"}

    monkeypatch.setattr(webhook, "run_healing_process", fake_run_healing_process)

    response = client.post(
        "/api/v1/webhook/gitlab",
        json=pipeline_payload(status="success"),
        headers={"X-Gitlab-Token": "expected-secret"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Ignored: Pipeline not failed"}
    assert calls == []


def test_gitlab_webhook_accepts_failed_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []

    async def fake_run_healing_process(**kwargs: object) -> dict[str, object]:
        calls.append(kwargs)
        return {"status": "called"}

    monkeypatch.setattr(webhook, "run_healing_process", fake_run_healing_process)

    response = client.post(
        "/api/v1/webhook/gitlab",
        json=pipeline_payload(status="failed"),
        headers={"X-Gitlab-Token": "expected-secret"},
    )

    assert response.status_code == 202
    assert response.json() == {
        "message": "Pipeline failure detected",
        "pipeline_id": 456,
        "project_id": 123,
    }
    assert calls == [{"project_id": 123, "pipeline_id": 456, "ref": "main"}]

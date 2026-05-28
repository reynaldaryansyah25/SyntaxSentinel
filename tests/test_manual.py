from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api.endpoints import manual
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def manual_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        manual,
        "get_settings",
        lambda: SimpleNamespace(demo_token="expected-demo-token"),
    )


def test_manual_heal_pipeline_rejects_invalid_token() -> None:
    response = client.post(
        "/api/v1/manual/heal-pipeline",
        json={"project_id": 123, "pipeline_id": 456, "ref": "main"},
        headers={"X-Demo-Token": "wrong-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid demo token"


def test_manual_heal_pipeline_accepts_valid_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    async def fake_run_healing_process(**kwargs: object) -> dict[str, object]:
        calls.append(kwargs)
        return {"status": "called"}

    monkeypatch.setattr(manual, "run_healing_process", fake_run_healing_process)

    response = client.post(
        "/api/v1/manual/heal-pipeline",
        json={"project_id": 123, "pipeline_id": 456, "ref": "main"},
        headers={"X-Demo-Token": "expected-demo-token"},
    )

    assert response.status_code == 202
    assert response.json() == {
        "message": "Manual healing process accepted",
        "project_id": 123,
        "pipeline_id": 456,
        "ref": "main",
    }
    assert calls == [{"project_id": 123, "pipeline_id": 456, "ref": "main"}]
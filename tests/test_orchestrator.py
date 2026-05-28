from types import SimpleNamespace
from typing import Any

import pytest

from app.models.agent import FixPlan
from app.services import orchestrator


class FakeGitLabClient:
    def __init__(
        self,
        *,
        failed_jobs: list[dict[str, Any]] | None = None,
        trace: str = "",
        files: dict[str, str] | None = None,
    ) -> None:
        self.failed_jobs = failed_jobs if failed_jobs is not None else [{"id": 99, "name": "pytest", "stage": "test"}]
        self.trace = trace
        self.files = files or {}
        self.branches: list[dict[str, Any]] = []
        self.commits: list[dict[str, Any]] = []
        self.merge_requests: list[dict[str, Any]] = []

    async def __aenter__(self) -> "FakeGitLabClient":
        return self

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    async def get_failed_jobs(self, project_id: int, pipeline_id: int) -> list[dict[str, Any]]:
        return self.failed_jobs

    async def read_job_trace(self, project_id: int, job_id: int) -> str:
        return self.trace

    async def get_file_content(self, project_id: int, file_path: str, ref: str) -> str:
        return self.files[file_path]

    async def create_branch(self, project_id: int, branch_name: str, ref: str) -> dict[str, Any]:
        payload = {"name": branch_name, "ref": ref, "dry_run": True}
        self.branches.append(payload)
        return payload

    async def commit_file_changes(
        self,
        project_id: int,
        branch: str,
        commit_message: str,
        actions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        payload = {
            "id": "commit-1",
            "branch": branch,
            "message": commit_message,
            "actions": actions,
            "dry_run": True,
        }
        self.commits.append(payload)
        return payload

    async def create_merge_request(
        self,
        project_id: int,
        source_branch: str,
        target_branch: str,
        title: str,
        description: str,
        labels: list[str] | None = None,
    ) -> dict[str, Any]:
        payload = {
            "iid": 1,
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
            "description": description,
            "labels": labels or [],
            "dry_run": True,
        }
        self.merge_requests.append(payload)
        return payload


@pytest.fixture(autouse=True)
def orchestrator_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        orchestrator,
        "get_settings",
        lambda: SimpleNamespace(
            max_trace_chars=4000,
            agent_min_confidence=0.75,
            gitlab_default_branch="main",
            dry_run=True,
        ),
    )


def make_fix_plan(
    *,
    confidence_score: float = 0.91,
    should_create_merge_request: bool = True,
    file_to_modify: str = "app.py",
    original_snippet: str = "def add(a: int, b: int) -> int\n    return a + b",
    fixed_snippet: str = "def add(a: int, b: int) -> int:\n    return a + b",
    risk_level: str = "low",
) -> FixPlan:
    return FixPlan(
        root_cause="The function definition is missing a colon.",
        error_type="SyntaxError",
        file_to_modify=file_to_modify,
        original_snippet=original_snippet,
        fixed_snippet=fixed_snippet,
        full_fixed_file_content=None,
        confidence_score=confidence_score,
        explanation="Add the missing colon to make the Python function definition valid.",
        risk_level=risk_level,
        should_create_merge_request=should_create_merge_request,
    )


@pytest.mark.asyncio
async def test_run_healing_process_creates_merge_request(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_gitlab = FakeGitLabClient(
        trace='''
Traceback (most recent call last):
  File "/builds/user/project/app.py", line 1
    def add(a: int, b: int) -> int
SyntaxError: expected ':'
''',
        files={"app.py": "def add(a: int, b: int) -> int\n    return a + b\n"},
    )
    monkeypatch.setattr(orchestrator, "GitLabMCPClient", lambda settings: fake_gitlab)

    async def fake_analyze_and_plan_fix(
        job_trace_log: str,
        source_file_path: str,
        source_code: str,
    ) -> FixPlan:
        return make_fix_plan(file_to_modify=source_file_path)

    monkeypatch.setattr(orchestrator, "analyze_and_plan_fix", fake_analyze_and_plan_fix)

    result = await orchestrator.run_healing_process(123, 456, "main")

    assert result["status"] == "merge_request_created"
    assert result["source_file_path"] == "app.py"
    assert fake_gitlab.branches[0]["name"] == "syntaxsentinel/fix-pipeline-456"
    assert fake_gitlab.commits[0]["actions"] == [
        {
            "action": "update",
            "file_path": "app.py",
            "content": "def add(a: int, b: int) -> int:\n    return a + b\n",
        }
    ]
    assert fake_gitlab.merge_requests[0]["labels"] == ["ai-auto-fix"]
    assert "requires human review" in fake_gitlab.merge_requests[0]["description"]


@pytest.mark.asyncio
async def test_run_healing_process_stops_when_no_failed_jobs(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_gitlab = FakeGitLabClient(failed_jobs=[])
    monkeypatch.setattr(orchestrator, "GitLabMCPClient", lambda settings: fake_gitlab)

    result = await orchestrator.run_healing_process(123, 456, "main")

    assert result["status"] == "no_failed_jobs"
    assert fake_gitlab.commits == []
    assert fake_gitlab.merge_requests == []


@pytest.mark.asyncio
async def test_run_healing_process_blocks_low_confidence(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_gitlab = FakeGitLabClient(
        trace='''
Traceback (most recent call last):
  File "/builds/user/project/app.py", line 1
SyntaxError: expected ':'
''',
        files={"app.py": "def add(a: int, b: int) -> int\n    return a + b\n"},
    )
    monkeypatch.setattr(orchestrator, "GitLabMCPClient", lambda settings: fake_gitlab)

    async def fake_analyze_and_plan_fix(
        job_trace_log: str,
        source_file_path: str,
        source_code: str,
    ) -> FixPlan:
        return make_fix_plan(file_to_modify=source_file_path, confidence_score=0.2)

    monkeypatch.setattr(orchestrator, "analyze_and_plan_fix", fake_analyze_and_plan_fix)

    result = await orchestrator.run_healing_process(123, 456, "main")

    assert result["status"] == "safety_blocked"
    assert "confidence" in result["reason"]
    assert fake_gitlab.commits == []


@pytest.mark.asyncio
async def test_run_healing_process_blocks_when_trace_has_no_file(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_gitlab = FakeGitLabClient(trace="pipeline failed without a Python traceback")
    monkeypatch.setattr(orchestrator, "GitLabMCPClient", lambda settings: fake_gitlab)

    result = await orchestrator.run_healing_process(123, 456, "main")

    assert result["status"] == "safety_blocked"
    assert "No safe repository file path" in result["reason"]
    assert fake_gitlab.commits == []


@pytest.mark.asyncio
async def test_run_healing_process_blocks_invalid_patch(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_gitlab = FakeGitLabClient(
        trace='''
Traceback (most recent call last):
  File "/builds/user/project/app.py", line 1
SyntaxError: expected ':'
''',
        files={"app.py": "print('snippet does not match')\n"},
    )
    monkeypatch.setattr(orchestrator, "GitLabMCPClient", lambda settings: fake_gitlab)

    async def fake_analyze_and_plan_fix(
        job_trace_log: str,
        source_file_path: str,
        source_code: str,
    ) -> FixPlan:
        return make_fix_plan(file_to_modify=source_file_path)

    monkeypatch.setattr(orchestrator, "analyze_and_plan_fix", fake_analyze_and_plan_fix)

    result = await orchestrator.run_healing_process(123, 456, "main")

    assert result["status"] == "safety_blocked"
    assert "not found" in result["reason"]
    assert fake_gitlab.commits == []

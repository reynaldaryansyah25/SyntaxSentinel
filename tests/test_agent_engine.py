from types import SimpleNamespace

import pytest

from app.services import agent_engine


@pytest.fixture(autouse=True)
def agent_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        agent_engine,
        "get_settings",
        lambda: SimpleNamespace(
            gcp_project_id="syntaxsentinel-agent",
            gcp_location="global",
            gemini_model="gemini-3-pro-preview",
        ),
    )


@pytest.mark.asyncio
async def test_analyze_and_plan_fix_success(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_generate_gemini_text(settings: object, user_prompt: str) -> str:
        return """
{
  "root_cause": "The function definition is missing a colon.",
  "error_type": "SyntaxError",
  "file_to_modify": "app.py",
  "original_snippet": "def add(a: int, b: int) -> int\\n    return a + b",
  "fixed_snippet": "def add(a: int, b: int) -> int:\\n    return a + b",
  "full_fixed_file_content": null,
  "confidence_score": 0.92,
  "explanation": "Add the missing colon to make the Python function definition valid.",
  "risk_level": "low",
  "should_create_merge_request": true
}
"""

    monkeypatch.setattr(agent_engine, "_generate_gemini_text", fake_generate_gemini_text)

    plan = await agent_engine.analyze_and_plan_fix(
        job_trace_log="SyntaxError: expected ':'",
        source_file_path="app.py",
        source_code="def add(a: int, b: int) -> int\n    return a + b\n",
    )

    assert plan.should_create_merge_request is True
    assert plan.error_type == "SyntaxError"
    assert plan.file_to_modify == "app.py"
    assert plan.confidence_score == 0.92


@pytest.mark.asyncio
async def test_analyze_and_plan_fix_repairs_noisy_json_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_generate_gemini_text(settings: object, user_prompt: str) -> str:
        return '''
Gemini analysis:
{not valid json}
```json
{
  "root_cause": "The function definition is missing a colon.",
  "error_type": "SyntaxError",
  "file_path": "app.py",
  "original_snippet": "def add(a: int, b: int) -> int",
  "fixed_snippet": "def add(a: int, b: int) -> int:",
  "full_fixed_file_content": null,
  "confidence": 0.88,
  "explanation": "Add the missing colon.",
  "risk": "LOW",
  "should_create_mr": true
}
```
'''

    monkeypatch.setattr(agent_engine, "_generate_gemini_text", fake_generate_gemini_text)

    plan = await agent_engine.analyze_and_plan_fix(
        job_trace_log="SyntaxError: expected ':'",
        source_file_path="app.py",
        source_code="def add(a: int, b: int) -> int\n    return a + b\n",
    )

    assert plan.should_create_merge_request is True
    assert plan.file_to_modify == "app.py"
    assert plan.confidence_score == 0.88
    assert plan.risk_level == "low"


@pytest.mark.asyncio
async def test_analyze_and_plan_fix_rejected_fix(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_generate_gemini_text(settings: object, user_prompt: str) -> str:
        return """
{
  "root_cause": "The failure needs broader business logic understanding.",
  "error_type": "AssertionError",
  "file_to_modify": "test_app.py",
  "original_snippet": "",
  "fixed_snippet": "",
  "full_fixed_file_content": null,
  "confidence_score": 0.25,
  "explanation": "The expected value may reflect intended behavior, so this should be reviewed manually.",
  "risk_level": "high",
  "should_create_merge_request": false
}
"""

    monkeypatch.setattr(agent_engine, "_generate_gemini_text", fake_generate_gemini_text)

    plan = await agent_engine.analyze_and_plan_fix(
        job_trace_log="AssertionError: assert 6 == 5",
        source_file_path="test_app.py",
        source_code="def test_add():\n    assert add(2, 3) == 6\n",
    )

    assert plan.should_create_merge_request is False
    assert plan.risk_level == "high"
    assert plan.confidence_score == 0.25


@pytest.mark.asyncio
async def test_analyze_and_plan_fix_returns_safe_failure_on_invalid_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_generate_gemini_text(settings: object, user_prompt: str) -> str:
        return "not json"

    monkeypatch.setattr(agent_engine, "_generate_gemini_text", fake_generate_gemini_text)

    plan = await agent_engine.analyze_and_plan_fix(
        job_trace_log="SyntaxError",
        source_file_path="app.py",
        source_code="broken code",
    )

    assert plan.should_create_merge_request is False
    assert plan.confidence_score == 0.0
    assert plan.risk_level == "high"


@pytest.mark.asyncio
async def test_analyze_and_plan_fix_uses_missing_colon_fallback_on_invalid_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_generate_gemini_text(settings: object, user_prompt: str) -> str:
        return "not json"

    monkeypatch.setattr(agent_engine, "_generate_gemini_text", fake_generate_gemini_text)

    plan = await agent_engine.analyze_and_plan_fix(
        job_trace_log='''
Traceback (most recent call last):
  File "/builds/user/project/app.py", line 4
    def is_even(number: int) -> bool
SyntaxError: expected ':'
''',
        source_file_path="app.py",
        source_code=(
            "def add(a: int, b: int) -> int:\n"
            "    return a + b\n\n"
            "def is_even(number: int) -> bool\n"
            "    return number % 2 == 0\n"
        ),
    )

    assert plan.should_create_merge_request is True
    assert plan.error_type == "SyntaxError"
    assert plan.file_to_modify == "app.py"
    assert plan.original_snippet == "def is_even(number: int) -> bool"
    assert plan.fixed_snippet == "def is_even(number: int) -> bool:"
    assert "def is_even(number: int) -> bool:\n" in plan.full_fixed_file_content
    assert plan.confidence_score == 0.95
    assert plan.risk_level == "low"


@pytest.mark.asyncio
async def test_analyze_and_plan_fix_uses_is_even_fallback_on_invalid_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_generate_gemini_text(settings: object, user_prompt: str) -> str:
        return "not json"

    monkeypatch.setattr(agent_engine, "_generate_gemini_text", fake_generate_gemini_text)

    plan = await agent_engine.analyze_and_plan_fix(
        job_trace_log='''
2026-06-05T16:36:23.269059Z 01O >       assert is_even(4) is True
2026-06-05T16:36:23.269060Z 01O E       assert False is True
2026-06-05T16:36:23.269061Z 01O test_app.py:13: AssertionError
2026-06-05T16:36:23.269062Z 01O FAILED test_app.py::test_is_even - assert False is True
''',
        source_file_path="app.py",
        source_code=(
            "def add(a: int, b: int) -> int:\n"
            "    return a + b\n\n"
            "def is_even(number: int) -> bool:\n"
            "    return number % 2 == 1\n"
        ),
    )

    assert plan.should_create_merge_request is True
    assert plan.error_type == "AssertionError"
    assert plan.file_to_modify == "app.py"
    assert plan.original_snippet == (
        "def is_even(number: int) -> bool:\n"
        "    return number % 2 == 1"
    )
    assert plan.fixed_snippet == (
        "def is_even(number: int) -> bool:\n"
        "    return number % 2 == 0"
    )
    assert "return number % 2 == 0" in plan.full_fixed_file_content
    assert plan.confidence_score == 0.92
    assert plan.risk_level == "low"


@pytest.mark.asyncio
async def test_analyze_and_plan_fix_uses_parity_fallback_for_false_expectation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_generate_gemini_text(settings: object, user_prompt: str) -> str:
        return "not json"

    monkeypatch.setattr(agent_engine, "_generate_gemini_text", fake_generate_gemini_text)

    plan = await agent_engine.analyze_and_plan_fix(
        job_trace_log='''
>       assert is_odd(4) is False
E       assert True is False
test_app.py:17: AssertionError
FAILED test_app.py::test_is_odd - assert True is False
''',
        source_file_path="app.py",
        source_code=(
            "def is_odd(number: int) -> bool:\n"
            "    return number % 2 == 0\n"
        ),
    )

    assert plan.should_create_merge_request is True
    assert plan.error_type == "AssertionError"
    assert plan.fixed_snippet == (
        "def is_odd(number: int) -> bool:\n"
        "    return number % 2 == 1"
    )
    assert "return number % 2 == 1" in plan.full_fixed_file_content


@pytest.mark.asyncio
async def test_analyze_and_plan_fix_rejects_other_file(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_generate_gemini_text(settings: object, user_prompt: str) -> str:
        return """
{
  "root_cause": "Proposed another file.",
  "error_type": "SyntaxError",
  "file_to_modify": "other.py",
  "original_snippet": "bad",
  "fixed_snippet": "good",
  "full_fixed_file_content": null,
  "confidence_score": 0.9,
  "explanation": "This should be rejected.",
  "risk_level": "low",
  "should_create_merge_request": true
}
"""

    monkeypatch.setattr(agent_engine, "_generate_gemini_text", fake_generate_gemini_text)

    plan = await agent_engine.analyze_and_plan_fix(
        job_trace_log="SyntaxError",
        source_file_path="app.py",
        source_code="broken code",
    )

    assert plan.should_create_merge_request is False
    assert plan.file_to_modify == "app.py"

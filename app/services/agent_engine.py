"""Gemini reasoning module for safe CI failure repair plans."""

import asyncio
import json
import logging
import re
from typing import Any

from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.models.agent import FixPlan
from app.utils.traceback_parser import extract_python_error_summary

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """You are SyntaxSentinel, an autonomous AI DevOps Engineer.
Your task is to safely repair failed CI/CD pipelines.

Rules:
1. Only fix small Python syntax errors, missing dependencies, simple import typos, or simple test assertion mismatches.
2. Do not refactor business logic.
3. Do not rewrite the whole project.
4. Do not create new files.
5. Only modify the file provided by the user.
6. The patch must be minimal.
7. If you are uncertain, set should_create_merge_request to false.
8. If the fix requires broad business logic understanding, reject it.
9. Explain the root cause briefly.
10. Return only valid JSON matching the requested schema.
"""


class GeminiGenerationError(RuntimeError):
    """Raised when Gemini cannot generate a usable response."""


async def analyze_and_plan_fix(
    job_trace_log: str,
    source_file_path: str,
    source_code: str,
) -> FixPlan:
    settings = get_settings()

    if not settings.gcp_project_id or not settings.gcp_location or not settings.gemini_model:
        return _safe_failure(
            source_file_path,
            "Google Cloud Gemini settings are not fully configured.",
        )

    prompt = _build_user_prompt(job_trace_log, source_file_path, source_code)

    try:
        raw_text = await _generate_gemini_text(settings, prompt)
        payload = _extract_json_object(raw_text)
        plan = FixPlan.model_validate(_normalize_fix_plan_payload(payload))
    except (GeminiGenerationError, ValidationError, ValueError, json.JSONDecodeError) as exc:
        logger.warning(
            "Gemini fix plan parsing failed",
            extra={"source_file_path": source_file_path, "error_type": exc.__class__.__name__},
        )
        fallback_plan = _build_deterministic_fallback_fix(
            job_trace_log,
            source_file_path,
            source_code,
        )
        if fallback_plan is not None:
            logger.info(
                "Deterministic fallback fix plan generated",
                extra={
                    "source_file_path": source_file_path,
                    "error_type": fallback_plan.error_type,
                    "confidence_score": fallback_plan.confidence_score,
                    "risk_level": fallback_plan.risk_level,
                },
            )
            return fallback_plan
        return _safe_failure(source_file_path, "Gemini response could not be parsed safely.")

    if plan.file_to_modify != source_file_path:
        return _safe_failure(
            source_file_path,
            "Gemini proposed modifying a file outside the provided source file.",
        )

    logger.info(
        "Gemini fix plan generated",
        extra={
            "source_file_path": source_file_path,
            "error_type": plan.error_type,
            "confidence_score": plan.confidence_score,
            "risk_level": plan.risk_level,
            "should_create_merge_request": plan.should_create_merge_request,
        },
    )
    return plan


async def _generate_gemini_text(settings: Settings, user_prompt: str) -> str:
    return await asyncio.to_thread(_generate_gemini_text_sync, settings, user_prompt)


def _generate_gemini_text_sync(settings: Settings, user_prompt: str) -> str:
    try:
        import vertexai
        from vertexai.generative_models import GenerationConfig, GenerativeModel
    except ImportError as exc:
        raise GeminiGenerationError("Vertex AI SDK is not installed.") from exc

    vertexai.init(project=settings.gcp_project_id, location=settings.gcp_location)
    model = GenerativeModel(
        settings.gemini_model,
        system_instruction=[SYSTEM_INSTRUCTION],
    )

    try:
        generation_config = GenerationConfig(
            temperature=0.1,
            response_mime_type="application/json",
        )
    except TypeError:
        generation_config = GenerationConfig(temperature=0.1)

    response = model.generate_content(
        [user_prompt],
        generation_config=generation_config,
    )

    text = getattr(response, "text", None)
    if not text:
        raise GeminiGenerationError("Gemini returned an empty response.")

    return text


def _build_user_prompt(job_trace_log: str, source_file_path: str, source_code: str) -> str:
    schema = FixPlan.model_json_schema()

    return f"""Analyze this failed CI job and propose a safe minimal fix.

Allowed fix types:
- Python syntax error
- Missing dependency
- Simple import typo
- Simple pytest assertion mismatch

Candidate file path:
{source_file_path}

Job trace:
```text
{job_trace_log}
```

Source code:
```text
{source_code}
```

Output JSON schema:
```json
{json.dumps(schema, indent=2)}
```

Return only JSON. Do not include markdown.
"""


def _extract_json_object(raw_text: str) -> dict[str, Any]:
    text = raw_text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    parsed = _loads_first_json_object(text)

    if not isinstance(parsed, dict):
        raise ValueError("Gemini response must be a JSON object.")

    return parsed


def _loads_first_json_object(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as original_error:
        last_error: json.JSONDecodeError | None = None
        for candidate in _iter_balanced_json_objects(text):
            try:
                return json.loads(candidate)
            except json.JSONDecodeError as exc:
                last_error = exc
        raise last_error or original_error


def _iter_balanced_json_objects(text: str) -> list[str]:
    candidates: list[str] = []
    start_indexes = [index for index, char in enumerate(text) if char == "{"]

    for start in start_indexes:
        depth = 0
        in_string = False
        escaped = False

        for index in range(start, len(text)):
            char = text[index]

            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    candidates.append(text[start : index + 1])
                    break

    return candidates


def _normalize_fix_plan_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    aliases = {
        "file": "file_to_modify",
        "file_path": "file_to_modify",
        "confidence": "confidence_score",
        "risk": "risk_level",
        "create_merge_request": "should_create_merge_request",
        "should_create_mr": "should_create_merge_request",
    }

    for source_key, target_key in aliases.items():
        if target_key not in normalized and source_key in normalized:
            normalized[target_key] = normalized[source_key]

    return normalized


def _build_deterministic_fallback_fix(
    job_trace_log: str,
    source_file_path: str,
    source_code: str,
) -> FixPlan | None:
    return _build_missing_colon_fallback_fix(
        job_trace_log,
        source_file_path,
        source_code,
    ) or _build_parity_assertion_fallback_fix(
        job_trace_log,
        source_file_path,
        source_code,
    )


def _build_missing_colon_fallback_fix(
    job_trace_log: str,
    source_file_path: str,
    source_code: str,
) -> FixPlan | None:
    error_summary = extract_python_error_summary(job_trace_log)
    if not _is_missing_colon_syntax_error(error_summary):
        return None

    summary_path = error_summary.get("file_path")
    if isinstance(summary_path, str) and summary_path != source_file_path:
        return None

    line_number = error_summary.get("line_number")
    if not isinstance(line_number, int):
        return None

    lines = source_code.splitlines()
    line_index = line_number - 1
    if line_index < 0 or line_index >= len(lines):
        return None

    original_line = lines[line_index]
    fixed_line = _add_missing_colon(original_line)
    if fixed_line is None:
        return None

    lines[line_index] = fixed_line
    fixed_content = "\n".join(lines)
    if source_code.endswith("\n"):
        fixed_content += "\n"

    return FixPlan(
        root_cause=(
            f"`{source_file_path}` line {line_number} starts a Python block but "
            "is missing the required trailing colon."
        ),
        error_type="SyntaxError",
        file_to_modify=source_file_path,
        original_snippet=original_line,
        fixed_snippet=fixed_line,
        full_fixed_file_content=fixed_content,
        confidence_score=0.95,
        explanation=(
            "The Python interpreter reported `SyntaxError: expected ':'`. "
            "The deterministic fallback added the missing colon to the block header only."
        ),
        risk_level="low",
        should_create_merge_request=True,
    )


def _build_parity_assertion_fallback_fix(
    job_trace_log: str,
    source_file_path: str,
    source_code: str,
) -> FixPlan | None:
    error_summary = extract_python_error_summary(job_trace_log)
    if error_summary.get("error_type") != "AssertionError":
        return None

    assertion = _extract_boolean_function_assertion(job_trace_log)
    if assertion is None:
        return None

    function_name, argument_value, expected_result = assertion
    if not function_name.startswith("is_"):
        return None

    pattern = re.compile(
        rf"(?ms)^def[ \t]+{re.escape(function_name)}\([^)]*\)(?:[ \t]*->[^\n:]+)?:\n"
        r"(?P<indent>[ \t]+)return[ \t]+(?P<name>[A-Za-z_][A-Za-z0-9_]*)"
        r"[ \t]*%[ \t]*2[ \t]*==[ \t]*(?P<remainder>[01])[ \t]*$"
    )
    match = pattern.search(source_code)
    if not match:
        return None

    current_remainder = int(match.group("remainder"))
    expected_remainder = argument_value % 2 if expected_result else 1 - (argument_value % 2)
    if current_remainder == expected_remainder:
        return None

    original_snippet = match.group(0)
    fixed_snippet = original_snippet.rsplit("\n", maxsplit=1)[0] + (
        f"\n{match.group('indent')}return {match.group('name')} % 2 == {expected_remainder}"
    )
    fixed_content = (
        source_code[: match.start()]
        + fixed_snippet
        + source_code[match.end() :]
    )

    return FixPlan(
        root_cause=(
            f"`{function_name}` returns the wrong boolean value for the tested "
            "parity case because the modulo comparison uses the opposite remainder."
        ),
        error_type="AssertionError",
        file_to_modify=source_file_path,
        original_snippet=original_snippet,
        fixed_snippet=fixed_snippet,
        full_fixed_file_content=fixed_content,
        confidence_score=0.92,
        explanation=(
            f"The failing test expected `{function_name}({argument_value})` "
            f"to be `{expected_result}`. "
            "The deterministic fallback changed the parity comparison from "
            f"`% 2 == {current_remainder}` to `% 2 == {expected_remainder}`."
        ),
        risk_level="low",
        should_create_merge_request=True,
    )


def _extract_boolean_function_assertion(job_trace_log: str) -> tuple[str, int, bool] | None:
    assertion_match = re.search(
        r"assert\s+(?P<function>[A-Za-z_][A-Za-z0-9_]*)\((?P<argument>-?\d+)\)\s+is\s+"
        r"(?P<expected>True|False)",
        job_trace_log,
    )
    if not assertion_match:
        return None

    expected_text = assertion_match.group("expected")
    expected_result = expected_text == "True"
    mismatch_text = f"assert {not expected_result} is {expected_result}"
    if mismatch_text not in job_trace_log:
        return None

    return (
        assertion_match.group("function"),
        int(assertion_match.group("argument")),
        expected_result,
    )


def _is_missing_colon_syntax_error(error_summary: dict[str, object | None]) -> bool:
    message = str(error_summary.get("message") or "").lower()
    return error_summary.get("error_type") == "SyntaxError" and "expected ':'" in message


def _add_missing_colon(line: str) -> str | None:
    stripped_line = line.rstrip()
    if stripped_line.endswith(":"):
        return None

    if not re.match(
        r"^\s*(async\s+def|def|class|if|elif|else|for|while|try|except|finally|with|match|case)\b",
        stripped_line,
    ):
        return None

    return f"{stripped_line}:"


def _safe_failure(source_file_path: str, reason: str) -> FixPlan:
    return FixPlan(
        root_cause=reason,
        error_type="UnknownError",
        file_to_modify=source_file_path,
        original_snippet="",
        fixed_snippet="",
        full_fixed_file_content=None,
        confidence_score=0.0,
        explanation=reason,
        risk_level="high",
        should_create_merge_request=False,
    )

"""Gemini reasoning module for safe CI failure repair plans."""

import asyncio
import json
import logging
import re
from typing import Any

from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.models.agent import FixPlan

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
        plan = FixPlan.model_validate(payload)
    except (GeminiGenerationError, ValidationError, ValueError, json.JSONDecodeError) as exc:
        logger.warning(
            "Gemini fix plan parsing failed",
            extra={"source_file_path": source_file_path, "error_type": exc.__class__.__name__},
        )
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

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise
        parsed = json.loads(match.group(0))

    if not isinstance(parsed, dict):
        raise ValueError("Gemini response must be a JSON object.")

    return parsed


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

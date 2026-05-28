"""Self-healing orchestration entrypoint."""

import logging
from typing import Any

from app.core.config import get_settings
from app.models.agent import FixPlan
from app.services.agent_engine import analyze_and_plan_fix
from app.services.gitlab_mcp_client import GitLabAPIError, GitLabMCPClient
from app.services.patcher import (
    PatchValidationError,
    build_gitlab_update_action,
    replace_exact_snippet,
    validate_file_scope,
    validate_patch_size,
)
from app.utils.traceback_parser import (
    extract_candidate_file_paths,
    extract_python_error_summary,
    trim_trace,
)

logger = logging.getLogger(__name__)


async def run_healing_process(project_id: int, pipeline_id: int, ref: str) -> dict[str, Any]:
    settings = get_settings()
    logger.info(
        "Healing process started",
        extra={"project_id": project_id, "pipeline_id": pipeline_id, "ref": ref},
    )

    try:
        async with GitLabMCPClient(settings=settings) as gitlab:
            failed_jobs = await gitlab.get_failed_jobs(project_id, pipeline_id)
            if not failed_jobs:
                return _stopped("no_failed_jobs", project_id, pipeline_id, "No failed jobs found.")

            failed_job = _select_failed_job(failed_jobs)
            job_id = _extract_job_id(failed_job)
            if job_id is None:
                return _stopped("invalid_failed_job", project_id, pipeline_id, "Failed job has no id.")

            raw_trace = await gitlab.read_job_trace(project_id, job_id)
            job_trace = trim_trace(raw_trace, settings.max_trace_chars)
            candidate_paths = extract_candidate_file_paths(job_trace)
            error_summary = extract_python_error_summary(job_trace)
            source_file_path = _select_source_file(candidate_paths, error_summary)
            if source_file_path is None:
                return _safety_blocked(
                    project_id,
                    pipeline_id,
                    "No safe repository file path could be extracted from the failed job trace.",
                    {"candidate_paths": candidate_paths, "error_summary": error_summary},
                )

            source_code = await gitlab.get_file_content(project_id, source_file_path, ref)
            fix_plan = await analyze_and_plan_fix(job_trace, source_file_path, source_code)
            validation_error = _validate_fix_plan(fix_plan, source_file_path, settings.agent_min_confidence)
            if validation_error:
                return _safety_blocked(
                    project_id,
                    pipeline_id,
                    validation_error,
                    {"fix_plan": fix_plan.model_dump()},
                )

            fixed_content = _build_fixed_content(source_code, fix_plan)
            validate_patch_size(source_code, fixed_content)
            action = build_gitlab_update_action(source_file_path, fixed_content)

            branch_name = f"syntaxsentinel/fix-pipeline-{pipeline_id}"
            target_branch = ref or settings.gitlab_default_branch
            commit_message = f"Fix pipeline failure {pipeline_id}"
            mr_title = f"SyntaxSentinel fix for pipeline {pipeline_id}"
            mr_description = _build_merge_request_description(
                fix_plan=fix_plan,
                pipeline_id=pipeline_id,
                source_file_path=source_file_path,
                job_id=job_id,
            )

            branch = await gitlab.create_branch(project_id, branch_name, target_branch)
            commit = await gitlab.commit_file_changes(
                project_id,
                branch_name,
                commit_message,
                [action],
            )
            merge_request = await gitlab.create_merge_request(
                project_id,
                branch_name,
                target_branch,
                mr_title,
                mr_description,
                labels=["ai-auto-fix"],
            )

            result = {
                "status": "merge_request_created",
                "project_id": project_id,
                "pipeline_id": pipeline_id,
                "job_id": job_id,
                "ref": ref,
                "source_file_path": source_file_path,
                "branch": branch,
                "commit": commit,
                "merge_request": merge_request,
                "dry_run": bool(settings.dry_run),
                "fix_plan": fix_plan.model_dump(),
            }
            logger.info(
                "Healing process completed",
                extra={
                    "project_id": project_id,
                    "pipeline_id": pipeline_id,
                    "job_id": job_id,
                    "source_file_path": source_file_path,
                    "dry_run": settings.dry_run,
                },
            )
            return result
    except PatchValidationError as exc:
        logger.warning(
            "Healing process blocked by patch safety validation",
            extra={"project_id": project_id, "pipeline_id": pipeline_id, "reason": str(exc)},
        )
        return _safety_blocked(project_id, pipeline_id, str(exc))
    except GitLabAPIError as exc:
        logger.exception(
            "Healing process failed because GitLab API returned an error",
            extra={"project_id": project_id, "pipeline_id": pipeline_id, "status_code": exc.status_code},
        )
        return {
            "status": "gitlab_error",
            "project_id": project_id,
            "pipeline_id": pipeline_id,
            "reason": str(exc),
            "status_code": exc.status_code,
        }
    except Exception as exc:
        logger.exception(
            "Healing process failed unexpectedly",
            extra={"project_id": project_id, "pipeline_id": pipeline_id},
        )
        return {
            "status": "error",
            "project_id": project_id,
            "pipeline_id": pipeline_id,
            "reason": exc.__class__.__name__,
        }


def _select_failed_job(failed_jobs: list[dict[str, Any]]) -> dict[str, Any]:
    preferred_keywords = ("test", "pytest", "lint", "build")
    for job in failed_jobs:
        name = str(job.get("name", "")).lower()
        stage = str(job.get("stage", "")).lower()
        if any(keyword in name or keyword in stage for keyword in preferred_keywords):
            return job
    return failed_jobs[0]


def _extract_job_id(job: dict[str, Any]) -> int | None:
    job_id = job.get("id")
    if isinstance(job_id, int):
        return job_id
    if isinstance(job_id, str) and job_id.isdigit():
        return int(job_id)
    return None


def _select_source_file(
    candidate_paths: list[str],
    error_summary: dict[str, object | None],
) -> str | None:
    summary_path = error_summary.get("file_path")
    if isinstance(summary_path, str) and validate_file_scope(summary_path):
        return summary_path

    for path in candidate_paths:
        if validate_file_scope(path):
            return path
    return None


def _validate_fix_plan(
    fix_plan: FixPlan,
    source_file_path: str,
    min_confidence: float,
) -> str | None:
    if not fix_plan.should_create_merge_request:
        return "Gemini declined to create a merge request for this failure."
    if fix_plan.confidence_score < min_confidence:
        return "Gemini confidence score is below the configured safety threshold."
    if fix_plan.file_to_modify != source_file_path:
        return "Gemini proposed modifying a different file than the selected source file."
    if fix_plan.risk_level == "high":
        return "Gemini marked the fix as high risk."
    if not validate_file_scope(fix_plan.file_to_modify):
        return "Gemini proposed a file outside the allowed patch scope."
    if fix_plan.full_fixed_file_content is None and (
        not fix_plan.original_snippet or not fix_plan.fixed_snippet
    ):
        return "Gemini did not provide enough patch content to apply a safe fix."
    return None


def _build_fixed_content(source_code: str, fix_plan: FixPlan) -> str:
    if fix_plan.full_fixed_file_content is not None:
        return fix_plan.full_fixed_file_content
    return replace_exact_snippet(
        source_code,
        fix_plan.original_snippet,
        fix_plan.fixed_snippet,
    )


def _build_merge_request_description(
    *,
    fix_plan: FixPlan,
    pipeline_id: int,
    source_file_path: str,
    job_id: int,
) -> str:
    return f"""## SyntaxSentinel Automated Fix

Root cause:
{fix_plan.root_cause}

Fix explanation:
{fix_plan.explanation}

Safety summary:
- Confidence score: {fix_plan.confidence_score:.2f}
- Risk level: {fix_plan.risk_level}
- Modified file: `{source_file_path}`
- Original pipeline ID: `{pipeline_id}`
- Failed job ID: `{job_id}`

This Merge Request was generated by SyntaxSentinel and requires human review before merge.
SyntaxSentinel never auto-merges changes.
"""


def _stopped(
    status: str,
    project_id: int,
    pipeline_id: int,
    reason: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    logger.info(
        "Healing process stopped",
        extra={"project_id": project_id, "pipeline_id": pipeline_id, "status": status, "reason": reason},
    )
    return {
        "status": status,
        "project_id": project_id,
        "pipeline_id": pipeline_id,
        "reason": reason,
        "details": details or {},
    }


def _safety_blocked(
    project_id: int,
    pipeline_id: int,
    reason: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    logger.warning(
        "Healing process blocked by safety policy",
        extra={"project_id": project_id, "pipeline_id": pipeline_id, "reason": reason},
    )
    return {
        "status": "safety_blocked",
        "project_id": project_id,
        "pipeline_id": pipeline_id,
        "reason": reason,
        "details": details or {},
    }

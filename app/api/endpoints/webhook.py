import logging

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, status
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.security import verify_shared_secret
from app.models.gitlab import GitLabPipelineWebhookPayload
from app.services.orchestrator import run_healing_process

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/webhook", tags=["webhook"])


@router.post("/gitlab")
async def handle_gitlab_webhook(
    payload: GitLabPipelineWebhookPayload,
    background_tasks: BackgroundTasks,
    x_gitlab_token: str | None = Header(default=None, alias="X-Gitlab-Token"),
) -> dict[str, object]:
    settings = get_settings()
    if not verify_shared_secret(x_gitlab_token, settings.gitlab_webhook_secret):
        logger.warning("GitLab webhook rejected: invalid secret")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid GitLab webhook token",
        )

    attributes = payload.object_attributes
    project_id = payload.project.id
    pipeline_id = attributes.pipeline_id

    logger.info(
        "GitLab pipeline webhook received",
        extra={
            "object_kind": payload.object_kind,
            "project_id": project_id,
            "pipeline_id": pipeline_id,
            "ref": attributes.ref,
            "status": attributes.status,
            "source": attributes.source,
        },
    )

    if attributes.status != "failed":
        logger.info(
            "GitLab pipeline webhook ignored: pipeline not failed",
            extra={
                "project_id": project_id,
                "pipeline_id": pipeline_id,
                "ref": attributes.ref,
                "status": attributes.status,
            },
        )
        return {"message": "Ignored: Pipeline not failed"}

    background_tasks.add_task(
        run_healing_process,
        project_id=project_id,
        pipeline_id=pipeline_id,
        ref=attributes.ref,
    )

    logger.info(
        "GitLab pipeline failure accepted for healing",
        extra={
            "project_id": project_id,
            "pipeline_id": pipeline_id,
            "ref": attributes.ref,
            "status": attributes.status,
        },
    )

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "message": "Pipeline failure detected",
            "pipeline_id": pipeline_id,
            "project_id": project_id,
        },
    )

import logging

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, status
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.security import verify_shared_secret
from app.models.gitlab import PipelineReference
from app.services.orchestrator import run_healing_process

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/manual", tags=["manual"])


@router.post("/heal-pipeline")
async def heal_pipeline_manually(
    payload: PipelineReference,
    background_tasks: BackgroundTasks,
    x_demo_token: str | None = Header(default=None, alias="X-Demo-Token"),
) -> JSONResponse:
    settings = get_settings()
    if not verify_shared_secret(x_demo_token, settings.demo_token):
        logger.warning("Manual healing request rejected: invalid demo token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid demo token",
        )

    logger.info(
        "Manual healing fallback accepted",
        extra={
            "project_id": payload.project_id,
            "pipeline_id": payload.pipeline_id,
            "ref": payload.ref,
        },
    )

    background_tasks.add_task(
        run_healing_process,
        project_id=payload.project_id,
        pipeline_id=payload.pipeline_id,
        ref=payload.ref,
    )

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "message": "Manual healing process accepted",
            "project_id": payload.project_id,
            "pipeline_id": payload.pipeline_id,
            "ref": payload.ref,
        },
    )
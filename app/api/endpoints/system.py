from fastapi import APIRouter

from app.core.config import get_settings
from app.models.response import HealthResponse, RootResponse

router = APIRouter(tags=["system"])


@router.get("/", response_model=RootResponse)
async def root() -> RootResponse:
    return RootResponse(
        name="SyntaxSentinel",
        message="Autonomous first responder for broken CI/CD pipelines.",
    )


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", app_env=settings.app_env)

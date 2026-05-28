from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="SyntaxSentinel",
        description="Autonomous CI/CD pipeline healing agent for GitLab.",
        version="0.1.0",
    )
    app.include_router(api_router)
    return app


app = create_app()

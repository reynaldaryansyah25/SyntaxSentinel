from fastapi import APIRouter

from app.api.endpoints import system, webhook, manual

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(webhook.router)
api_router.include_router(manual.router)

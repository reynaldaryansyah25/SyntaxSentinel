from fastapi import APIRouter

from app.api.endpoints import system

api_router = APIRouter()
api_router.include_router(system.router)

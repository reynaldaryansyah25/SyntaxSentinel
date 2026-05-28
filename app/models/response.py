from pydantic import BaseModel


class RootResponse(BaseModel):
    name: str
    message: str


class HealthResponse(BaseModel):
    status: str
    app_env: str

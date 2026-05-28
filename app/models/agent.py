from pydantic import BaseModel, Field


class AgentDecision(BaseModel):
    status: str = Field(..., description="High-level agent decision status.")
    reason: str = Field(..., description="Short human-readable reason.")

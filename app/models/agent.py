from pydantic import BaseModel, Field, field_validator


class AgentDecision(BaseModel):
    status: str = Field(..., description="High-level agent decision status.")
    reason: str = Field(..., description="Short human-readable reason.")


class FixPlan(BaseModel):
    root_cause: str
    error_type: str
    file_to_modify: str
    original_snippet: str
    fixed_snippet: str
    full_fixed_file_content: str | None = None
    confidence_score: float = Field(ge=0.0, le=1.0)
    explanation: str
    risk_level: str
    should_create_merge_request: bool

    @field_validator("risk_level")
    @classmethod
    def validate_risk_level(cls, value: str) -> str:
        allowed = {"low", "medium", "high"}
        normalized = value.strip().lower()
        if normalized not in allowed:
            raise ValueError("risk_level must be one of: low, medium, high")
        return normalized
from pydantic import BaseModel, ConfigDict, Field, field_validator


class PipelineReference(BaseModel):
    project_id: int = Field(gt=0)
    pipeline_id: int = Field(gt=0)
    ref: str = Field(min_length=1)

    @field_validator("ref", mode="before")
    @classmethod
    def strip_ref(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class GitLabProject(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    web_url: str | None = None


class GitLabPipelineAttributes(BaseModel):
    model_config = ConfigDict(extra="ignore")

    pipeline_id: int = Field(alias="id", gt=0)
    status: str
    ref: str = Field(min_length=1)
    sha: str | None = None
    source: str | None = None

    @field_validator("ref", "status", mode="before")
    @classmethod
    def strip_text_fields(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class GitLabPipelineWebhookPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    object_kind: str
    project: GitLabProject
    object_attributes: GitLabPipelineAttributes

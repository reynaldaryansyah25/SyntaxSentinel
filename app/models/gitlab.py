from pydantic import BaseModel, ConfigDict, Field


class PipelineReference(BaseModel):
    project_id: int
    pipeline_id: int
    ref: str


class GitLabProject(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    web_url: str | None = None


class GitLabPipelineAttributes(BaseModel):
    model_config = ConfigDict(extra="ignore")

    pipeline_id: int = Field(alias="id")
    status: str
    ref: str
    sha: str | None = None
    source: str | None = None


class GitLabPipelineWebhookPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    object_kind: str
    project: GitLabProject
    object_attributes: GitLabPipelineAttributes

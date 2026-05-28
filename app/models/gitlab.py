from pydantic import BaseModel


class PipelineReference(BaseModel):
    project_id: int
    pipeline_id: int
    ref: str

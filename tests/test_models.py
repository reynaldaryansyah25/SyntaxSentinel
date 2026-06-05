import pytest
from pydantic import ValidationError

from app.models.agent import FixPlan
from app.models.gitlab import PipelineReference


def test_pipeline_reference_strips_ref() -> None:
    payload = PipelineReference(project_id=123, pipeline_id=456, ref="  feature/demo  ")

    assert payload.ref == "feature/demo"


@pytest.mark.parametrize(
    "payload",
    [
        {"project_id": 0, "pipeline_id": 456, "ref": "main"},
        {"project_id": 123, "pipeline_id": 0, "ref": "main"},
        {"project_id": 123, "pipeline_id": 456, "ref": "   "},
    ],
)
def test_pipeline_reference_rejects_invalid_values(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        PipelineReference(**payload)


def test_fix_plan_normalizes_file_path() -> None:
    plan = FixPlan(
        root_cause="Syntax error.",
        error_type="SyntaxError",
        file_to_modify=r"src\app.py",
        original_snippet="bad",
        fixed_snippet="good",
        confidence_score=0.9,
        explanation="Fix syntax.",
        risk_level=" LOW ",
        should_create_merge_request=True,
    )

    assert plan.file_to_modify == "src/app.py"
    assert plan.risk_level == "low"

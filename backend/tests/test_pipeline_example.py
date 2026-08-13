from app.core.models import (
    _PIPELINE_EXAMPLE_PATH,
    _PIPELINE_EXAMPLE_RESUME_PATH,
    _load_pipeline_request_example,
)


def test_pipeline_example_resume_matches_civic_climate_sample() -> None:
    example = _load_pipeline_request_example()
    sample = _PIPELINE_EXAMPLE_RESUME_PATH.read_text(encoding="utf-8")
    json_resume = str(_PIPELINE_EXAMPLE_PATH.read_text(encoding="utf-8"))
    assert example["resume"] == sample
    assert "Jordan Hale" in json_resume
    assert "VOLUNTEER" in sample
    assert "SIDE PROJECTS" in sample
    assert "climate" in sample.lower()
    assert "nonprofit" in sample.lower()

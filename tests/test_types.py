import pytest

from runner.types import job_from_dict, transition_status


def test_valid_status_transitions() -> None:
    assert transition_status("picked_up", "running") == "running"
    assert transition_status("running", "succeeded") == "succeeded"
    assert transition_status("running", "failed") == "failed"


def test_invalid_transition_raises() -> None:
    with pytest.raises(ValueError, match="Invalid status transition"):
        transition_status("picked_up", "succeeded")


def test_job_from_dict_parses_compile_captureone() -> None:
    job = job_from_dict(
        {
            "job_id": "job_1",
            "job_type": "compile_captureone",
            "payload": {"style_id": "style_1", "version": "v2"},
            "status": "picked_up",
        }
    )
    assert job.job_id == "job_1"
    assert job.job_type == "compile_captureone"
    assert job.payload.style_id == "style_1"
    assert job.payload.version == "v2"
    assert job.status == "picked_up"


def test_job_from_dict_unsupported_type_raises() -> None:
    with pytest.raises(ValueError, match="Unsupported job type"):
        job_from_dict(
            {
                "job_id": "job_1",
                "job_type": "unknown",
                "payload": {"style_id": "style_1", "version": "v2"},
            }
        )

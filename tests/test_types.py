import pytest

from runner.types import transition_status


def test_valid_status_transitions() -> None:
    assert transition_status("picked_up", "running") == "running"
    assert transition_status("running", "succeeded") == "succeeded"
    assert transition_status("running", "failed") == "failed"


def test_invalid_transition_raises() -> None:
    with pytest.raises(ValueError, match="Invalid status transition"):
        transition_status("picked_up", "succeeded")


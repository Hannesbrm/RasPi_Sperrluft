"""Tests for SystemState helper methods."""

from datetime import datetime, timedelta

from models.system_state import SystemState


def test_as_dict_includes_postrun_remaining():
    state = SystemState()
    data = state.as_dict()
    assert data["postrun_remaining"] == 0

    state.postrun_until = datetime.now() + timedelta(seconds=5)
    data = state.as_dict()
    assert 0 < data["postrun_remaining"] <= 5

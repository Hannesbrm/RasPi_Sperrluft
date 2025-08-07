"""Tests for configuration management."""

import json
from pathlib import Path

from config import config_manager
from models.system_state import SystemState


def test_load_and_save_config(tmp_config):
    data = config_manager.load_config()
    assert Path(config_manager.CONFIG_PATH).exists()
    assert data == config_manager.DEFAULT_CONFIG

    state = SystemState(setpoint=42.0, alarm_threshold=55.0, manual_pwm=10.0)
    config_manager.save_config(state)

    loaded = json.loads(Path(config_manager.CONFIG_PATH).read_text())
    assert loaded["setpoint"] == 42.0
    assert loaded["alarm_threshold"] == 55.0
    assert loaded["manual_pwm"] == 10.0

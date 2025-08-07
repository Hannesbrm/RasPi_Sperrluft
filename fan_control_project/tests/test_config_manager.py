"""Tests for configuration management."""

import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import config_manager
from models.system_state import SystemState


def test_load_and_save_config(tmp_path):
    cfg_file = tmp_path / "settings.json"
    # Patch CONFIG_PATH to use temporary file
    config_manager.CONFIG_PATH = str(cfg_file)

    data = config_manager.load_config()
    assert cfg_file.exists()
    assert data == config_manager.DEFAULT_CONFIG

    state = SystemState(setpoint=42.0, alarm_threshold=55.0, manual_pwm=10.0)
    config_manager.save_config(state)

    loaded = json.loads(cfg_file.read_text())
    assert loaded["setpoint"] == 42.0
    assert loaded["alarm_threshold"] == 55.0
    assert loaded["manual_pwm"] == 10.0

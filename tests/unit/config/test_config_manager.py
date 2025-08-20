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


def test_load_config_with_invalid_json(tmp_config):
    Path(config_manager.CONFIG_PATH).write_text("{ invalid")
    data = config_manager.load_config()
    assert data == config_manager.DEFAULT_CONFIG


def test_load_config_adds_missing_keys(tmp_config):
    Path(config_manager.CONFIG_PATH).write_text(json.dumps({"setpoint": 1.0}))
    data = config_manager.load_config()
    assert all(k in data for k in config_manager.DEFAULT_CONFIG)
    loaded = json.loads(Path(config_manager.CONFIG_PATH).read_text())
    assert all(k in loaded for k in config_manager.DEFAULT_CONFIG)


def test_mcp_block_migration(tmp_config):
    Path(config_manager.CONFIG_PATH).write_text(json.dumps({"mcp9600": {"retries": 3}}))
    data = config_manager.load_config()
    mcp = data["mcp9600"]
    assert mcp["type"] == "K"
    assert mcp["retries"] == 3
    assert "backoff_ms" in mcp

import sys
from pathlib import Path

# Ensure project package is importable
PROJECT_ROOT = Path(__file__).resolve().parents[1] / "fan_control_project"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest

from config import config_manager
from models.system_state import SystemState
from web import server as webserver


@pytest.fixture
def state(monkeypatch):
    """Return a fresh SystemState and patch the web server to use it."""
    state = SystemState()
    monkeypatch.setattr(webserver, "state", state)
    return state


@pytest.fixture
def tmp_config(tmp_path, monkeypatch):
    """Use a temporary config file for tests."""
    cfg_file = tmp_path / "settings.json"
    monkeypatch.setattr(config_manager, "CONFIG_PATH", str(cfg_file))
    return cfg_file


@pytest.fixture
def no_save_config(monkeypatch):
    """Disable persisting configuration during tests."""
    monkeypatch.setattr(config_manager, "save_config", lambda s: None)
    monkeypatch.setattr(webserver, "save_config", lambda s: None)


@pytest.fixture
def dummy_actuator():
    class DummyActuator:
        def __init__(self):
            self.last_value: float | None = None

        def set_output(self, value: float) -> None:
            self.last_value = value

        def stop(self) -> None:  # pragma: no cover - nothing to clean up
            pass

    return DummyActuator


@pytest.fixture
def dummy_pid():
    class DummyPID:
        def __init__(self, value: float = 10.0):
            self.value = value
            self.last_setpoint: float | None = None
            self.last_input: float | None = None

        def update_setpoint(self, sp: float) -> None:
            self.last_setpoint = sp

        def compute(self, current_value: float) -> float:
            self.last_input = current_value
            return self.value

    return DummyPID


@pytest.fixture
def dummy_sensor_reader():
    class DummySensorReader:
        def __init__(self, data: dict[str, dict[str, float | str]] | None = None):
            self.data = data or {}

        def read_all(self) -> dict[str, dict[str, float | str]]:
            return self.data

        def read_temperature(self, idx: int) -> float | None:
            key = list(self.data.keys())[idx]
            entry = self.data.get(key, {})
            return entry.get("temperature")

    return DummySensorReader


@pytest.fixture
def app_client():
    """Flask test client for the web server."""
    return webserver.app.test_client()


@pytest.fixture
def socketio_client():
    """Socket.IO test client connected to the server."""
    client = webserver.socketio.test_client(webserver.app)
    try:
        yield client
    finally:
        client.disconnect()

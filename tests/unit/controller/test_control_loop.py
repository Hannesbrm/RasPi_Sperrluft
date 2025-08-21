import datetime
import types

import pytest

import controller.control_loop as control_loop
from controller.control_loop import ControlLoop
from models import SystemState, Mode
from models.sensor_info import SensorInfo


@pytest.fixture
def loop_factory(dummy_sensor_reader, dummy_pid, dummy_actuator):
    def _create_loop(state=None, sensor_data=None, pid=None, actuator=None, sensors=None):
        state = state or SystemState()
        pid = pid or dummy_pid()
        actuator = actuator or dummy_actuator()
        sensors = sensors or [SensorInfo("id1", "pin1"), SensorInfo("id2", "pin2")]
        reader = dummy_sensor_reader(sensor_data or {})
        return ControlLoop(state, reader, pid, actuator, sensors)

    return _create_loop


def test_read_temperatures_updates_state(loop_factory):
    sensor_data = {
        "id1": {"temperature": 21.0, "status": "ok"},
        "id2": {"temperature": 22.0, "status": "ok"},
    }
    loop = loop_factory(sensor_data=sensor_data)

    t1, t2 = loop._read_temperatures()

    assert t1 == 21.0 and t2 == 22.0
    assert loop.state.temperature1 == 21.0
    assert loop.state.status2 == "ok"
    assert loop.state.temp1_pin == "pin1"


def test_handle_alarm_state_sets_flags_and_postrun(loop_factory):
    state = SystemState(alarm_threshold=50.0, postrun_seconds=10.0)
    loop = loop_factory(state=state)
    now = datetime.datetime.now()

    alarm, postrun = loop._handle_alarm_state(60.0, now)
    assert alarm is True
    assert postrun is False
    assert state.alarm_active is True
    assert state.postrun_until is None

    alarm, postrun = loop._handle_alarm_state(40.0, now)
    assert alarm is False
    assert postrun is True
    assert state.postrun_until == now + datetime.timedelta(seconds=10.0)


def test_compute_output_manual_and_auto(loop_factory, dummy_actuator):
    state = SystemState(mode=Mode.MANUAL, manual_percent=30.0)
    act = dummy_actuator()
    loop = loop_factory(state=state, actuator=act)
    result = loop._compute_output(None, False, False)
    assert result == 30.0
    assert act.last_value == 30.0

    state.mode = Mode.AUTO
    state.alarm_percent = 80.0
    result = loop._compute_output(25.0, True, False)
    assert result == 80.0
    assert act.last_value == 80.0


def test_start_and_stop_runs_thread(loop_factory, monkeypatch):
    loop = loop_factory()

    def run_once():
        loop._running = False

    monkeypatch.setattr(loop, "_run_loop", run_once)
    loop.start()
    loop.stop()
    assert loop._thread is None


def test_start_ignores_if_running(loop_factory):
    loop = loop_factory()
    loop._running = True
    loop.start()
    assert loop._thread is None


def test_read_temperatures_swapped(loop_factory):
    data = {
        "id1": {"temperature": 10.0, "status": "ok"},
        "id2": {"temperature": 20.0, "status": "ok"},
    }
    state = SystemState(swap_sensors=True)
    loop = loop_factory(state=state, sensor_data=data)
    t1, t2 = loop._read_temperatures()
    assert t1 == 20.0 and t2 == 10.0
    assert state.temp1_pin == "pin2"


def test_handle_alarm_state_postrun_expiry(loop_factory):
    now = datetime.datetime.now()
    state = SystemState(alarm_threshold=50.0, postrun_seconds=1.0, alarm_active=True)
    loop = loop_factory(state=state)
    alarm, postrun = loop._handle_alarm_state(40.0, now)
    assert postrun is True
    later = now + datetime.timedelta(seconds=2)
    alarm, postrun = loop._handle_alarm_state(40.0, later)
    assert alarm is False and postrun is False
    assert state.postrun_until is None


def test_compute_output_temp_none_and_invalid_mode(loop_factory, dummy_actuator):
    state = SystemState(mode=Mode.AUTO, output_pct=55.0)
    act = dummy_actuator()
    loop = loop_factory(state=state, actuator=act)
    result = loop._compute_output(None, False, False)
    assert result == 55.0
    state.mode = "other"
    state.output_pct = 5.0
    result = loop._compute_output(30.0, False, False)
    assert result == 5.0


def test_run_loop_calls_update_once(loop_factory, monkeypatch):
    loop = loop_factory()
    calls = []

    def fake_update():
        calls.append(1)
        loop._running = False

    monkeypatch.setattr(loop, "update_once", fake_update)
    monkeypatch.setattr(control_loop, "time", types.SimpleNamespace(sleep=lambda s: None))
    loop._running = True
    loop._run_loop()
    assert calls == [1]

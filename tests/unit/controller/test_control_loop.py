import datetime

import pytest

from controller.control_loop import ControlLoop
from models import SystemState, Mode
from models.sensor_info import SensorInfo


@pytest.fixture
def loop_factory(dummy_sensor_reader, dummy_pid, dummy_pwm):
    def _create_loop(state=None, sensor_data=None, pid=None, pwm=None, sensors=None):
        state = state or SystemState()
        pid = pid or dummy_pid()
        pwm = pwm or dummy_pwm()
        sensors = sensors or [SensorInfo("id1", "pin1"), SensorInfo("id2", "pin2")]
        reader = dummy_sensor_reader(sensor_data or {})
        return ControlLoop(state, reader, pid, pwm, sensors)

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


def test_compute_pwm_manual_and_auto(loop_factory, dummy_pwm):
    state = SystemState(mode=Mode.MANUAL, manual_pwm=30.0, min_pwm=20.0)
    pwm = dummy_pwm(min_pwm=20.0)
    loop = loop_factory(state=state, pwm=pwm)
    result = loop._compute_pwm(None, False, False)
    assert result == 30.0
    assert pwm.last_value == 30.0

    state.mode = Mode.AUTO
    state.alarm_pwm = 80.0
    result = loop._compute_pwm(25.0, True, False)
    assert result == 80.0
    assert pwm.last_value == 80.0

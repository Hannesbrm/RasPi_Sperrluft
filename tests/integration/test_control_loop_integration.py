"""Integration test for ControlLoop with dummy components."""

from controller.control_loop import ControlLoop
from models import SystemState
from models.sensor_info import SensorInfo


def test_update_once_updates_pwm(dummy_sensor_reader, dummy_pid, dummy_pwm):
    state = SystemState(setpoint=30.0, alarm_threshold=80.0)
    reader = dummy_sensor_reader(
        {
            "id1": {"temperature": 20.0, "status": "ok"},
            "id2": {"temperature": 35.0, "status": "ok"},
        }
    )
    pid = dummy_pid(value=40.0)
    pwm = dummy_pwm()
    loop = ControlLoop(state, reader, pid, pwm, [SensorInfo("id1", "p1"), SensorInfo("id2", "p2")])

    loop.update_once()

    assert state.temperature1 == 20.0
    assert state.temperature2 == 35.0
    assert pwm.last_value == 60.0  # 100 - PID output (40)
    assert state.pwm1 == 60.0

"""Integration test for ControlLoop with dummy components."""

from controller.control_loop import ControlLoop
from models import SystemState
from models.sensor_info import SensorInfo


def test_update_once_updates_output(dummy_sensor_reader, dummy_pid, dummy_actuator):
    state = SystemState(setpoint=30.0, alarm_threshold=80.0)
    reader = dummy_sensor_reader(
        {
            "id1": {"temperature": 20.0, "status": "ok"},
            "id2": {"temperature": 35.0, "status": "ok"},
        }
    )
    pid = dummy_pid(value=40.0)
    act = dummy_actuator()
    loop = ControlLoop(state, reader, pid, act, [SensorInfo("id1", "p1"), SensorInfo("id2", "p2")])

    loop.update_once()

    assert state.temperature1 == 20.0
    assert state.temperature2 == 35.0
    assert act.last_value == 60.0  # 100 - PID output (40)
    assert state.output_pct == 60.0

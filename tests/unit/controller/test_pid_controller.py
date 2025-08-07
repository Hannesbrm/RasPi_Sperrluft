"""Tests for PIDController wrapper."""

from controller.pid_controller import PIDController


def test_pid_compute_and_setpoint():
    pid = PIDController(setpoint=25.0, kp=2.0, ki=0.0, kd=0.0, sample_time=0)
    # With setpoint 25 and current value 20 error is 5 -> output 10
    assert pid.compute(20.0) == 10.0
    pid.update_setpoint(30.0)
    # Now error is 10 -> output 20
    assert pid.compute(20.0) == 20.0

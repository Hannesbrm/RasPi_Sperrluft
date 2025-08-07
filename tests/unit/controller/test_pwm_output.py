"""Tests for FanPWMController in dummy mode."""

from controller.pwm_output import FanPWMController


def test_pwm_respects_minimum():
    pwm = FanPWMController(min_pwm=30.0)
    pwm.set_pwm(10.0)
    assert pwm._value == 30.0
    pwm.set_pwm(50.0)
    assert pwm._value == 50.0


def test_pwm_stop_does_not_fail():
    pwm = FanPWMController()
    pwm.stop()
    assert pwm.pwm is None

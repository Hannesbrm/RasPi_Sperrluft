"""Tests for FanPWMController in dummy mode."""

import pytest

import controller.pwm_output as pwm_module
from controller.pwm_output import FanPWMController


@pytest.fixture(autouse=True)
def mock_gpio(monkeypatch):
    """Force the PWM controller into dummy mode for tests."""
    monkeypatch.setattr(pwm_module, "_HAS_GPIO", False)


def test_pwm_respects_minimum():
    pwm = FanPWMController(min_pwm=30.0)
    pwm.set_pwm(10.0)
    assert pwm.last_value == 30.0
    pwm.set_pwm(50.0)
    assert pwm.last_value == 50.0


def test_pwm_stop_does_not_fail():
    pwm = FanPWMController()
    pwm.stop()
    assert pwm.pwm is None

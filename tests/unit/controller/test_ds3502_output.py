"""Tests for DS3502 output mapping."""

from controller.ds3502_output import FanDS3502Controller, DS3502Config


def test_percent_to_wiper_mapping():
    cfg = DS3502Config(wiper_min=2, wiper_max=125)
    ctrl = FanDS3502Controller(cfg)
    assert ctrl._percent_to_wiper(0) == 2
    assert ctrl._percent_to_wiper(50) == 64
    assert ctrl._percent_to_wiper(100) == 125


def test_percent_to_wiper_inverted():
    cfg = DS3502Config(wiper_min=2, wiper_max=125, invert=True)
    ctrl = FanDS3502Controller(cfg)
    assert ctrl._percent_to_wiper(0) == 125
    assert ctrl._percent_to_wiper(50) == 64
    assert ctrl._percent_to_wiper(100) == 2

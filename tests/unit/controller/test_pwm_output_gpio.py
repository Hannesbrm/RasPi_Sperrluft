"""Hardware-path tests for FanPWMController using a fake GPIO module."""

import types

import importlib
import sys

import controller.pwm_output as pwm_module
from controller.pwm_output import FanPWMController


class FakePWM:
    def __init__(self, pin, freq):
        self.pin = pin
        self.freq = freq
        self.started = False
        self.last = None
        self.stopped = False

    def start(self, val):
        self.started = True

    def ChangeDutyCycle(self, val):
        self.last = val

    def stop(self):
        self.stopped = True


class FakeGPIO:
    BCM = object()
    OUT = object()

    def __init__(self):
        self.mode = None
        self.setup_calls = []
        self.cleanup_calls = []
        self.pwm_instance = None

    def setwarnings(self, flag):
        self.warn = flag

    def setmode(self, mode):
        self.mode = mode

    def setup(self, pin, mode):
        self.setup_calls.append((pin, mode))

    def PWM(self, pin, freq):
        self.pwm_instance = FakePWM(pin, freq)
        return self.pwm_instance

    def cleanup(self, pin):
        self.cleanup_calls.append(pin)


def test_pwm_gpio_interaction(monkeypatch):
    fake_gpio = FakeGPIO()
    monkeypatch.setattr(pwm_module, "GPIO", fake_gpio)
    monkeypatch.setattr(pwm_module, "_HAS_GPIO", True)
    pwm = FanPWMController(pin=17, frequency=50, min_pwm=10.0)
    assert fake_gpio.pwm_instance.started
    pwm.set_pwm(150.0)
    assert pwm.last_value == 100.0
    # 100% logical PWM should result in 0% hardware duty cycle
    assert fake_gpio.pwm_instance.last == 0.0
    pwm.set_pwm(40.0)
    assert pwm.last_value == 40.0
    # Normal values are inverted as well
    assert fake_gpio.pwm_instance.last == 60.0
    pwm.stop()
    assert fake_gpio.cleanup_calls == [17]
    assert fake_gpio.pwm_instance.stopped


def test_module_import_sets_has_gpio(monkeypatch):
    fake_gpio = FakeGPIO()
    monkeypatch.setitem(sys.modules, "RPi.GPIO", fake_gpio)
    importlib.reload(pwm_module)
    assert pwm_module._HAS_GPIO is True
    monkeypatch.delitem(sys.modules, "RPi.GPIO", raising=False)
    importlib.reload(pwm_module)

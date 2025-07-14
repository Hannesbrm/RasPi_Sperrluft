"""Represent the current system state for the fan control application."""

from enum import Enum
from typing import Any, Dict


class Mode(Enum):
    """Possible operating modes for the system."""

    NORMAL = "normal"
    ALARM = "alarm"
    MANUAL = "manual"


class SystemState:
    """Container object for the runtime state of the system."""

    def __init__(
        self,
        temperature1: float = 0.0,
        temperature2: float = 0.0,
        pwm1: float = 0.0,
        pwm2: float = 0.0,
        setpoint: float = 0.0,
        mode: Mode = Mode.NORMAL,
        alarm_threshold: float = 0.0,
        manual_pwm: float = 0.0,
        kp: float = 1.0,
        ki: float = 0.1,
        kd: float = 0.0,
    ) -> None:
        self._temperature1 = temperature1
        self._temperature2 = temperature2
        self._pwm1 = pwm1
        self._pwm2 = pwm2
        self._setpoint = setpoint
        self._mode = mode
        self._alarm_threshold = alarm_threshold
        self._manual_pwm = manual_pwm
        self._kp = kp
        self._ki = ki
        self._kd = kd

    # Temperatur 1
    @property
    def temperature1(self) -> float:
        return self._temperature1

    @temperature1.setter
    def temperature1(self, value: float) -> None:
        self._temperature1 = value

    # Temperatur 2
    @property
    def temperature2(self) -> float:
        return self._temperature2

    @temperature2.setter
    def temperature2(self, value: float) -> None:
        self._temperature2 = value

    # PWM-Wert 1
    @property
    def pwm1(self) -> float:
        return self._pwm1

    @pwm1.setter
    def pwm1(self, value: float) -> None:
        self._pwm1 = value

    # PWM-Wert 2
    @property
    def pwm2(self) -> float:
        return self._pwm2

    @pwm2.setter
    def pwm2(self, value: float) -> None:
        self._pwm2 = value

    # Solltemperatur
    @property
    def setpoint(self) -> float:
        return self._setpoint

    @setpoint.setter
    def setpoint(self, value: float) -> None:
        self._setpoint = value

    # Betriebsmodus
    @property
    def mode(self) -> Mode:
        return self._mode

    @mode.setter
    def mode(self, value: Mode) -> None:
        if isinstance(value, Mode):
            self._mode = value
        else:
            self._mode = Mode(value)

    # Alarmgrenze
    @property
    def alarm_threshold(self) -> float:
        return self._alarm_threshold

    @alarm_threshold.setter
    def alarm_threshold(self, value: float) -> None:
        self._alarm_threshold = value

    # Manueller PWM-Wert
    @property
    def manual_pwm(self) -> float:
        return self._manual_pwm

    @manual_pwm.setter
    def manual_pwm(self, value: float) -> None:
        self._manual_pwm = value

    # PID parameters
    @property
    def kp(self) -> float:
        return self._kp

    @kp.setter
    def kp(self, value: float) -> None:
        self._kp = value

    @property
    def ki(self) -> float:
        return self._ki

    @ki.setter
    def ki(self, value: float) -> None:
        self._ki = value

    @property
    def kd(self) -> float:
        return self._kd

    @kd.setter
    def kd(self, value: float) -> None:
        self._kd = value

    def to_dict(self) -> Dict[str, Any]:
        """Return a dictionary representation of the state."""

        return {
            "temperature1": self._temperature1,
            "temperature2": self._temperature2,
            "pwm1": self._pwm1,
            "pwm2": self._pwm2,
            "setpoint": self._setpoint,
            "mode": self._mode.value,
            "alarm_threshold": self._alarm_threshold,
            "manual_pwm": self._manual_pwm,
            "kp": self._kp,
            "ki": self._ki,
            "kd": self._kd,
        }


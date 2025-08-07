"""Represent the current system state for the fan control application."""

from enum import Enum
from typing import Any, Dict


class Mode(Enum):
    """Possible operating modes for the system."""

    AUTO = "auto"
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
        mode: Mode = Mode.AUTO,
        alarm_threshold: float = 0.0,
        manual_pwm: float = 0.0,
        alarm_pwm: float = 100.0,
        min_pwm: float = 20.0,
        kp: float = 1.0,
        ki: float = 0.1,
        kd: float = 0.0,
        postrun_seconds: float = 30.0,
        status1: str = "ok",
        status2: str = "ok",
        temp1_pin: str = "",
        temp2_pin: str = "",
        swap_sensors: bool = False,
    ) -> None:
        self._temperature1 = temperature1
        self._temperature2 = temperature2
        self._pwm1 = pwm1
        self._pwm2 = pwm2
        self._setpoint = setpoint
        self._mode = mode
        self._alarm_threshold = alarm_threshold
        self._manual_pwm = manual_pwm
        self._alarm_pwm = alarm_pwm
        self._min_pwm = min_pwm
        self._kp = kp
        self._ki = ki
        self._kd = kd
        self._postrun_seconds = postrun_seconds
        self._postrun_until = None
        self._alarm_active = False
        self._status1 = status1
        self._status2 = status2
        self._temp1_pin = temp1_pin
        self._temp2_pin = temp2_pin
        self._swap_sensors = swap_sensors

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

    # PWM-Wert im Alarmmodus
    @property
    def alarm_pwm(self) -> float:
        return self._alarm_pwm

    @alarm_pwm.setter
    def alarm_pwm(self, value: float) -> None:
        self._alarm_pwm = value

    # Minimaler PWM-Wert
    @property
    def min_pwm(self) -> float:
        return self._min_pwm

    @min_pwm.setter
    def min_pwm(self, value: float) -> None:
        self._min_pwm = value

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

    # Nachlaufzeit in Sekunden
    @property
    def postrun_seconds(self) -> float:
        return self._postrun_seconds

    @postrun_seconds.setter
    def postrun_seconds(self, value: float) -> None:
        self._postrun_seconds = value

    # Zeitpunkt bis wann der Nachlauf aktiv bleibt
    @property
    def postrun_until(self):  # type: ignore[override]
        return self._postrun_until

    @postrun_until.setter
    def postrun_until(self, value) -> None:  # type: ignore[override]
        self._postrun_until = value

    # Interner Alarmstatus
    @property
    def alarm_active(self) -> bool:
        return self._alarm_active

    @alarm_active.setter
    def alarm_active(self, value: bool) -> None:
        self._alarm_active = value

    # Status des ersten Sensors
    @property
    def status1(self) -> str:
        return self._status1

    @status1.setter
    def status1(self, value: str) -> None:
        self._status1 = value

    # Status des zweiten Sensors
    @property
    def status2(self) -> str:
        return self._status2

    @status2.setter
    def status2(self, value: str) -> None:
        self._status2 = value

    # GPIO pin of the first temperature channel
    @property
    def temp1_pin(self) -> str:
        return self._temp1_pin

    @temp1_pin.setter
    def temp1_pin(self, value: str) -> None:
        self._temp1_pin = value

    # GPIO pin of the second temperature channel
    @property
    def temp2_pin(self) -> str:
        return self._temp2_pin

    @temp2_pin.setter
    def temp2_pin(self, value: str) -> None:
        self._temp2_pin = value

    # Whether the sensor roles are swapped
    @property
    def swap_sensors(self) -> bool:
        return self._swap_sensors

    @swap_sensors.setter
    def swap_sensors(self, value: bool) -> None:
        self._swap_sensors = value

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
            "alarm_pwm": self._alarm_pwm,
            "min_pwm": self._min_pwm,
            "kp": self._kp,
            "ki": self._ki,
            "kd": self._kd,
            "postrun_seconds": self._postrun_seconds,
            "alarm_active": self._alarm_active,
            "status1": self._status1,
            "status2": self._status2,
            "temp1_pin": self._temp1_pin,
            "temp2_pin": self._temp2_pin,
            "swap_sensors": self._swap_sensors,
        }


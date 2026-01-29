"""Represent the current system state for the fan control application."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class Mode(Enum):
    """Possible operating modes for the system."""

    AUTO = "auto"
    MANUAL = "manual"


@dataclass
class SystemState:
    """Container object for the runtime state of the system."""

    temperature1: float = 0.0
    temperature2: float = 0.0
    ambient1: float = 0.0
    ambient2: float = 0.0
    delta1: float = 0.0
    delta2: float = 0.0
    output_pct: float = 0.0
    setpoint: float = 0.0
    mode: Mode = field(default=Mode.AUTO)
    alarm_threshold: float = 0.0
    manual_percent: float = 0.0
    alarm_percent: float = 100.0
    wiper_min: int = 2
    kp: float = 1.0
    ki: float = 0.1
    kd: float = 0.0
    postrun_seconds: float = 30.0
    status1: str = "ok"
    status2: str = "ok"
    temp1_pin: str = ""
    temp2_pin: str = ""
    swap_sensors: bool = False
    postrun_until: Optional[datetime] = None
    alarm_active: bool = False
    thermocouple_type: str = "K"
    smoothing_enabled: bool = True
    smoothing_alpha: float = 0.3

    def __post_init__(self) -> None:
        if not isinstance(self.mode, Mode):
            self.mode = Mode(self.mode)
        self.thermocouple_type = str(self.thermocouple_type).upper()

    def as_dict(self) -> Dict[str, Any]:
        """Return a dictionary representation of the state."""

        data = asdict(self)
        data["mode"] = self.mode.value
        data["thermocouple_type"] = str(self.thermocouple_type).upper()
        remaining = 0
        if self.postrun_until is not None:
            remaining = int((self.postrun_until - datetime.now()).total_seconds())
            if remaining < 0:
                remaining = 0
        data["postrun_remaining"] = remaining
        data.pop("postrun_until", None)
        return data

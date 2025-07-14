"""Background control loop for regulating the fan speed."""

from __future__ import annotations

import threading
import time
from typing import Optional

from .sensor_reader import SensorReader
from .pid_controller import PIDController
from .pwm_output import FanPWMController
from ..models import SystemState, Mode


class ControlLoop:
    """Continuously update :class:`SystemState` and control the fan."""

    def __init__(
        self,
        state: SystemState,
        sensor_reader: SensorReader,
        pid_controller: PIDController,
        pwm_controller: FanPWMController,
        alarm_pwm: float = 100.0,
        interval: float = 0.5,
    ) -> None:
        self.state = state
        self.sensor_reader = sensor_reader
        self.pid = pid_controller
        self.pwm = pwm_controller
        self.alarm_pwm = alarm_pwm
        self.interval = interval

        self._thread: Optional[threading.Thread] = None
        self._running = False

    def start(self) -> None:
        """Start the control loop in a background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the control loop."""
        self._running = False
        if self._thread is not None:
            self._thread.join()
            self._thread = None
        self.pwm.stop()

    def _run_loop(self) -> None:
        while self._running:
            self._update_once()
            time.sleep(self.interval)

    def _update_once(self) -> None:
        """Read sensors, compute PWM value and update state."""
        temp1 = self.sensor_reader.read_temperature(0)
        temp2 = self.sensor_reader.read_temperature(1)

        if temp1 is not None:
            self.state.temperature1 = temp1
        if temp2 is not None:
            self.state.temperature2 = temp2

        pwm_value = 0.0

        if self.state.mode == Mode.MANUAL:
            pwm_value = self.state.manual_pwm
        elif (
            self.state.mode == Mode.ALARM
            and temp2 is not None
            and temp2 > self.state.alarm_threshold
        ):
            pwm_value = self.alarm_pwm
        else:
            if temp1 is not None:
                self.pid.update_setpoint(self.state.setpoint)
                pwm_value = self.pid.compute(temp1)
            else:
                pwm_value = self.state.pwm1

        self.pwm.set_pwm(pwm_value)
        self.state.pwm1 = pwm_value

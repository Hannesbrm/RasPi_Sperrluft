"""Background control loop for regulating the fan speed."""

from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta
from typing import Optional, List

from .sensor_reader import SensorReader
from .pid_controller import PIDController
from .pwm_output import FanPWMController
from models import SystemState, Mode
from models.sensor_info import SensorInfo
from config.logging_config import logger


class ControlLoop:
    """Continuously update :class:`SystemState` and control the fan."""

    def __init__(
        self,
        state: SystemState,
        sensor_reader: SensorReader,
        pid_controller: PIDController,
        pwm_controller: FanPWMController,
        sensors: List[SensorInfo],
        alarm_pwm: float = 100.0,
        interval: float = 0.5,
    ) -> None:
        self.state = state
        self.sensor_reader = sensor_reader
        self.pid = pid_controller
        self.pwm = pwm_controller
        self.state.alarm_pwm = alarm_pwm
        self.interval = interval
        self.sensors = sensors

        self._thread: Optional[threading.Thread] = None
        self._running = False

    def start(self) -> None:
        """Start the control loop in a background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Control loop gestartet")

    def stop(self) -> None:
        """Stop the control loop."""
        self._running = False
        if self._thread is not None:
            self._thread.join()
            self._thread = None
        self.pwm.stop()
        logger.info("Control loop gestoppt")

    def _run_loop(self) -> None:
        while self._running:
            self.update_once()
            time.sleep(self.interval)

    def _read_temperatures(self) -> tuple[Optional[float], Optional[float]]:
        """Read both sensors and update state values."""
        sensor_data = self.sensor_reader.read_all()

        if self.state.swap_sensors:
            sensor1_info = self.sensors[1]
            sensor2_info = self.sensors[0]
        else:
            sensor1_info = self.sensors[0]
            sensor2_info = self.sensors[1]

        entry1 = sensor_data.get(sensor1_info.rom_id, {})
        entry2 = sensor_data.get(sensor2_info.rom_id, {})

        self.state.temp1_pin = sensor1_info.pin
        self.state.temp2_pin = sensor2_info.pin

        logger.debug("Sensor1=%s Sensor2=%s", entry1, entry2)

        temp1 = entry1.get("temperature")
        temp2 = entry2.get("temperature")
        amb1 = entry1.get("ambient")
        amb2 = entry2.get("ambient")
        delta1 = entry1.get("delta")
        delta2 = entry2.get("delta")
        status1 = entry1.get("status", "error")
        status2 = entry2.get("status", "error")

        self.state.status1 = status1
        self.state.status2 = status2

        if temp1 is not None:
            self.state.temperature1 = temp1
        if temp2 is not None:
            self.state.temperature2 = temp2
        if amb1 is not None:
            self.state.ambient1 = amb1
        if amb2 is not None:
            self.state.ambient2 = amb2
        if delta1 is not None:
            self.state.delta1 = delta1
        if delta2 is not None:
            self.state.delta2 = delta2

        return temp1, temp2

    def _handle_alarm_state(
        self, temp2: Optional[float], now: datetime
    ) -> tuple[bool, bool]:
        """Update alarm and postrun state based on ``temp2``."""
        alarm = temp2 is not None and temp2 > self.state.alarm_threshold

        if alarm:
            self.state.alarm_active = True
            self.state.postrun_until = None
        else:
            if self.state.alarm_active:
                self.state.alarm_active = False
                self.state.postrun_until = now + timedelta(
                    seconds=self.state.postrun_seconds
                )

        postrun_active = False
        if self.state.postrun_until is not None:
            if now < self.state.postrun_until:
                postrun_active = True
            else:
                self.state.postrun_until = None

        return alarm, postrun_active

    def _compute_pwm(
        self, temp1: Optional[float], alarm: bool, postrun_active: bool
    ) -> float:
        """Compute the PWM value and update the controller."""
        if self.state.mode == Mode.MANUAL:
            pwm_value = self.state.manual_pwm

        elif self.state.mode == Mode.AUTO:
            if alarm or postrun_active:
                pwm_value = self.state.alarm_pwm
            elif temp1 is not None:
                self.pid.update_setpoint(self.state.setpoint)
                pwm_value = self.pid.compute(temp1)
                pwm_value = 100.0 - pwm_value
                pwm_value = max(0.0, min(100.0, pwm_value))
            else:
                pwm_value = self.state.pwm1
        else:
            pwm_value = self.state.pwm1

        final_value = max(self.pwm.min_pwm, pwm_value)
        self.pwm.set_pwm(final_value)
        self.state.pwm1 = final_value
        return final_value

    def update_once(self) -> None:
        """Perform a single control-loop iteration."""
        temp1, temp2 = self._read_temperatures()
        now = datetime.now()
        alarm, postrun_active = self._handle_alarm_state(temp2, now)
        final_value = self._compute_pwm(temp1, alarm, postrun_active)
        logger.debug(
            "PWM berechnet: temp1=%s temp2=%s alarm=%s pwm=%.2f",
            temp1,
            temp2,
            alarm or postrun_active,
            final_value,
        )

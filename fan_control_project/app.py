"""Entry point for the fan control application."""

# Use the real sensor reader for the MAX31850K sensors
from controller.sensor_reader import SensorReader
from controller.pid_controller import PIDController
from controller.pwm_output import FanPWMController
from controller.control_loop import ControlLoop
from web import server
from config import load_config
from config.logging_config import logger
from models.sensor_info import SensorInfo

# Description of connected sensors including ROM IDs and GPIO pins
sensors = [
    SensorInfo(rom_id="3b-68000ec3edfc", pin="D24"),
    SensorInfo(rom_id="3b-2e141377f2c2", pin="D26"),
]


def main() -> None:
    """Initialize all components and start the web server."""
    logger.info("Starte Anwendung")

    # Reuse the global state object from the web server so that updates become
    # visible to connected clients.
    state = server.state

    # Load persisted configuration values
    cfg = load_config()
    logger.debug("Konfiguration geladen: %s", cfg)
    state.setpoint = float(cfg.get("setpoint", 0.0))
    state.alarm_threshold = float(cfg.get("alarm_threshold", 0.0))
    state.manual_pwm = float(cfg.get("manual_pwm", 0.0))
    state.alarm_pwm = float(cfg.get("alarm_pwm", 100.0))
    state.min_pwm = float(cfg.get("min_pwm", 20.0))
    pwm_pin = int(cfg.get("pwm_pin", 12))
    state.kp = float(cfg.get("kp", 1.0))
    state.ki = float(cfg.get("ki", 0.1))
    state.kd = float(cfg.get("kd", 0.0))
    state.postrun_seconds = float(cfg.get("postrun_seconds", 30.0))

    # IDs of the connected 1-Wire temperature sensors. Using the order of the
    # ``sensors`` list ensures a stable mapping independent of the startup
    # sequence on the bus.
    state.swap_sensors = bool(cfg.get("swap_sensors", False))
    sensor_ids = [s.rom_id for s in sensors]
    sensor_reader = SensorReader(sensor_ids)

    if state.swap_sensors:
        state.temp1_pin = sensors[1].pin
        state.temp2_pin = sensors[0].pin
    else:
        state.temp1_pin = sensors[0].pin
        state.temp2_pin = sensors[1].pin

    # Basic PID controller using parameters from the configuration.
    pid = PIDController(
        setpoint=state.setpoint,
        kp=state.kp,
        ki=state.ki,
        kd=state.kd,
        sample_time=0.5,
    )

    pwm_controller = FanPWMController(pin=pwm_pin, min_pwm=state.min_pwm)

    control_loop = ControlLoop(
        state,
        sensor_reader,
        pid,
        pwm_controller,
        sensors=sensors,
        alarm_pwm=state.alarm_pwm,
    )
    control_loop.start()
    logger.info("Steuerung gestartet")

    # Expose PID controller to the web server for runtime updates
    server.pid_controller = pid

    server.main()
    logger.info("Anwendung beendet")


if __name__ == "__main__":
    main()


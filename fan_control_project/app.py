"""Entry point for the fan control application."""

# Use the real sensor reader for the MAX31850K sensors
from controller.sensor_reader import SensorReader
from controller.pid_controller import PIDController
from controller.pwm_output import FanPWMController
from controller.control_loop import ControlLoop
from web import server
from config import load_config

# Mapping between semantic temperature labels and the 1-Wire sensor IDs
sensor_mapping = {
    "temperature1": "3b-68000ec3edfc",
    "temperature2": "3b-2e141377f2c2",
}


def main() -> None:
    """Initialize all components and start the web server."""

    # Reuse the global state object from the web server so that updates become
    # visible to connected clients.
    state = server.state

    # Load persisted configuration values
    cfg = load_config()
    state.setpoint = float(cfg.get("setpoint", 0.0))
    state.alarm_threshold = float(cfg.get("alarm_threshold", 0.0))
    state.manual_pwm = float(cfg.get("manual_pwm", 0.0))
    state.alarm_pwm = float(cfg.get("alarm_pwm", 100.0))
    state.min_pwm = float(cfg.get("min_pwm", 20.0))
    pwm_pin = int(cfg.get("pwm_pin", 12))
    state.kp = float(cfg.get("kp", 1.0))
    state.ki = float(cfg.get("ki", 0.1))
    state.kd = float(cfg.get("kd", 0.0))

    # IDs of the connected 1-Wire temperature sensors. Keys in ``sensor_mapping``
    # represent the logical position while the values are the stable IDs of the
    # sensors on the bus. Using ``list(sensor_mapping.values())`` ensures that
    # the reader gets a reproducible ordering independent of the startup
    # sequence of the sensors.
    sensor_ids = list(sensor_mapping.values())
    sensor_reader = SensorReader(sensor_ids)

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
        state.alarm_pwm,
        sensor_mapping=sensor_mapping,
    )
    control_loop.start()

    # Expose PID controller to the web server for runtime updates
    server.pid_controller = pid

    server.main()


if __name__ == "__main__":
    main()


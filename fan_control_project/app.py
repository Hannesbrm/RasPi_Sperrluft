"""Entry point for the fan control application."""

# Use the dummy sensor reader for development without hardware
from controller.sensor_reader_dummy import SensorReader
from controller.pid_controller import PIDController
from controller.pwm_output import FanPWMController
from controller.control_loop import ControlLoop
from web import server
from config import load_config


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
    state.kp = float(cfg.get("kp", 1.0))
    state.ki = float(cfg.get("ki", 0.1))
    state.kd = float(cfg.get("kd", 0.0))

    # IDs of the connected 1-Wire temperature sensors. Adjust these values for
    # a real setup. Two IDs are expected for temperature1 and temperature2.
    sensor_ids = [
        "28-000000000001",
        "28-000000000002",
    ]
    sensor_reader = SensorReader(sensor_ids)

    # Basic PID controller using parameters from the configuration.
    pid = PIDController(
        setpoint=state.setpoint,
        kp=state.kp,
        ki=state.ki,
        kd=state.kd,
        sample_time=0.5,
    )

    pwm_controller = FanPWMController()

    control_loop = ControlLoop(state, sensor_reader, pid, pwm_controller, state.alarm_pwm)
    control_loop.start()

    # Expose PID controller to the web server for runtime updates
    server.pid_controller = pid

    server.main()


if __name__ == "__main__":
    main()


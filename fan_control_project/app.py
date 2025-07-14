"""Entry point for the fan control application."""

from controller.sensor_reader import SensorReader
from controller.pid_controller import PIDController
from controller.pwm_output import FanPWMController
from controller.control_loop import ControlLoop
from web import server


def main() -> None:
    """Initialize all components and start the web server."""

    # Reuse the global state object from the web server so that updates become
    # visible to connected clients.
    state = server.state

    # IDs of the connected 1-Wire temperature sensors. Adjust these values for
    # a real setup. Two IDs are expected for temperature1 and temperature2.
    sensor_ids = [
        "28-000000000001",
        "28-000000000002",
    ]
    sensor_reader = SensorReader(sensor_ids)

    # Basic PID controller with reasonable default parameters. The setpoint in
    # the shared state object may be changed via the web interface.
    pid = PIDController(
        setpoint=state.setpoint,
        kp=1.0,
        ki=0.1,
        kd=0.0,
        sample_time=0.5,
    )

    pwm_controller = FanPWMController()

    control_loop = ControlLoop(state, sensor_reader, pid, pwm_controller)
    control_loop.start()

    server.main()


if __name__ == "__main__":
    main()


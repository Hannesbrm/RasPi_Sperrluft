from simple_pid import PID

from config.logging_config import logger

class PIDController:
    """Wrapper around :class:`simple_pid.PID` for basic fan control."""

    def __init__(self, setpoint: float, kp: float, ki: float, kd: float,
                 output_limits=(0, 100), sample_time=1.0):
        """Initialize PID controller with tuning parameters.

        Parameters
        ----------
        setpoint : float
            Desired target value.
        kp : float
            Proportional gain.
        ki : float
            Integral gain.
        kd : float
            Derivative gain.
        output_limits : tuple, optional
            Minimum and maximum control output. Defaults to (0, 100).
        sample_time : float, optional
            Minimum time between two calculations. Defaults to 1 second.
        """
        self.pid = PID(kp, ki, kd, setpoint=setpoint, output_limits=output_limits)
        self.pid.sample_time = sample_time
        logger.debug(
            "PID initialisiert: setpoint=%s, kp=%s, ki=%s, kd=%s",
            setpoint,
            kp,
            ki,
            kd,
        )

    def compute(self, current_value: float) -> float:
        """Return control output for a measured value."""
        result = self.pid(current_value)
        logger.debug("PID compute: input=%.2f output=%.2f", current_value, result)
        return result

    def update_setpoint(self, new_value: float) -> None:
        """Update the desired target value."""
        logger.debug("PID setpoint update: %s", new_value)
        self.pid.setpoint = new_value

"""PWM controller abstraction used by the control loop."""

try:
    import RPi.GPIO as GPIO
    _HAS_GPIO = True
except Exception:  # pragma: no cover - only triggered off Pi
    GPIO = None  # type: ignore
    _HAS_GPIO = False

from config.logging_config import logger

class FanPWMController:
    """Control a PWM fan using ``RPi.GPIO`` or a dummy fallback."""

    def __init__(self, pin: int = 12, frequency: int = 25, min_pwm: float = 20.0) -> None:
        self.pin = pin
        self.frequency = frequency
        self.min_pwm = min_pwm
        self.pwm = None

        if _HAS_GPIO:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin, GPIO.OUT)
            self.pwm = GPIO.PWM(self.pin, self.frequency)
            self.pwm.start(0)
            logger.info("PWM initialisiert auf Pin %s", self.pin)
        else:
            # Dummy mode when running off the Pi
            self._value = 0.0
            logger.info("PWM Dummy-Modus aktiv")

    def set_pwm(self, value: float) -> None:
        """Set PWM duty cycle (0.0-100.0) respecting ``min_pwm``."""
        value = max(self.min_pwm, min(100.0, value))
        if not _HAS_GPIO:
            self._value = value
            logger.debug("Dummy PWM gesetzt: %.2f", value)
            return

        if self.pwm:
            self.pwm.ChangeDutyCycle(value)
            logger.debug("PWM gesetzt: %.2f", value)

    def stop(self) -> None:
        """Stop PWM and clean up GPIO."""
        if _HAS_GPIO and self.pwm:
            self.pwm.stop()
            GPIO.cleanup(self.pin)
            self.pwm = None
        logger.info("PWM gestoppt")


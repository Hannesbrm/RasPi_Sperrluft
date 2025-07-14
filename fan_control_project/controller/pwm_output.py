import RPi.GPIO as GPIO

class FanPWMController:
    """Simple PWM controller for a fan using RPi.GPIO."""

    def __init__(self, pin: int = 18, frequency: int = 25) -> None:
        """Initialize PWM on the given GPIO pin."""
        self.pin = pin
        self.frequency = frequency
        self.pwm = None

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pin, self.frequency)
        self.pwm.start(0)

    def set_pwm(self, value: float) -> None:
        """Set PWM duty cycle (0.0-100.0)."""
        if not self.pwm:
            return
        value = max(0.0, min(100.0, value))
        self.pwm.ChangeDutyCycle(value)

    def stop(self) -> None:
        """Stop PWM and clean up GPIO."""
        if self.pwm:
            self.pwm.stop()
            GPIO.cleanup(self.pin)
            self.pwm = None


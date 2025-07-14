import RPi.GPIO as GPIO

class PWMOutput:
    def __init__(self, gpio_pin=12, frequency=1000):
        """
        Initialisiert die PWM-Ausgabe auf einem GPIO-Pin.
        :param gpio_pin: GPIO-Pin (BCM-Nummer), z.B. GPIO12 = Pin 32
        :param frequency: PWM-Frequenz in Hz
        """
        self.gpio_pin = gpio_pin
        self.frequency = frequency
        self.pwm = None

        try:
            # Warnungen von GPIO deaktivieren (z. B. bei mehrfacher Initialisierung)
            GPIO.setwarnings(False)
            # Pin-Nummerierung im BCM-Modus verwenden (nicht physikalisch)
            GPIO.setmode(GPIO.BCM)
            # Pin als Ausgang konfigurieren
            GPIO.setup(self.gpio_pin, GPIO.OUT)

            # Globales Tracking für PWM-Kanäle initialisieren, falls noch nicht vorhanden
            if not hasattr(GPIO, '_pwm_channels'):
                GPIO._pwm_channels = {}

            # Wiederverwendung einer bestehenden PWM-Instanz, falls schon vorhanden
            if self.gpio_pin in GPIO._pwm_channels:
                self.pwm = GPIO._pwm_channels[self.gpio_pin]
                print(f"[PWMOutput] PWM auf GPIO{self.gpio_pin} bereits initialisiert, wiederverwendet.")
            else:
                # Neue PWM-Instanz erstellen und starten
                self.pwm = GPIO.PWM(self.gpio_pin, self.frequency)
                self.pwm.start(0)  # Mit 0% Duty-Cycle starten
                GPIO._pwm_channels[self.gpio_pin] = self.pwm
                print(f"[PWMOutput] PWM gestartet auf GPIO{self.gpio_pin} mit {self.frequency}Hz")

        except Exception as e:
            # Fehlerausgabe bei Problemen während der Initialisierung
            print(f"[PWMOutput] Fehler bei der Initialisierung: {e}")

    def set_pwm_percent(self, channel, percent):
        """
        Setzt den PWM-Duty-Cycle (0–100%).
        Der 'channel'-Parameter wird ignoriert, da nur ein Kanal genutzt wird.
        """
        if self.pwm is None:
            return

        # Sicherstellen, dass der Wert zwischen 0 und 100 liegt
        percent = max(0.0, min(100.0, percent))
        self.pwm.ChangeDutyCycle(percent)

    def all_off(self):
        """Setzt PWM auf 0%, um die Ausgabe zu deaktivieren."""
        if self.pwm:
            self.pwm.ChangeDutyCycle(0)

    def shutdown(self):
        """
        Beendet die PWM-Ausgabe und gibt den verwendeten GPIO-Pin frei.
        Wichtig für sauberen Programmabschluss.
        """
        if self.pwm:
            # PWM stoppen
            self.pwm.stop()
            # Kanal aus globaler Tracking-Tabelle entfernen
            if hasattr(GPIO, '_pwm_channels') and self.gpio_pin in GPIO._pwm_channels:
                del GPIO._pwm_channels[self.gpio_pin]

        try:
            # GPIO-Pin bereinigen (zurücksetzen)
            GPIO.cleanup(self.gpio_pin)
            print(f"[PWMOutput] PWM gestoppt und GPIO{self.gpio_pin} bereinigt")
        except RuntimeError as e:
            # Warnung bei Fehler während der Bereinigung (z. B. mehrfacher Aufruf)
            print(f"[PWMOutput] Warnung beim GPIO-Cleanup (GPIO{self.gpio_pin}): {e}")

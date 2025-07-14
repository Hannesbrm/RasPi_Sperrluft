# controller/pid_adapter.py

from simple_pid import PID

class PIDAdapter:
    def __init__(self, kp=1.0, ki=0.0, kd=0.0, output_limits=(10, 100), sample_time=0.2):
        """
        Initialisiert den PID-Regler mit gegebenen Parametern.
        :param kp: Proportionalanteil
        :param ki: Integralanteil
        :param kd: Differentialanteil
        :param output_limits: Begrenzung des Ausgabewerts (min, max)
        :param sample_time: Abtastrate in Sekunden
        """
        self.pid = PID(kp, ki, kd, setpoint=0, output_limits=output_limits)  # Erzeuge PID-Reglerinstanz
        self.pid.sample_time = sample_time  # Setze die Abtastzeit

    def set_parameters(self, kp, ki, kd):
        """Setzt neue PID-Parameter."""
        self.pid.tunings = (kp, ki, kd)  # Aktualisiert die Reglerparameter

    def get_parameters(self):
        """Gibt die aktuellen PID-Parameter als Dictionary zurück."""
        kp, ki, kd = self.pid.tunings  # Lese aktuelle Parameter aus
        return {'kp': kp, 'ki': ki, 'kd': kd}  # Gib sie als Dictionary zurück

    def reset(self):
        """Setzt den internen Zustand zurück (z. B. Integrator)."""
        self.pid.reset()  # Rücksetzen des internen Zustands des Reglers

    def update(self, setpoint, input_value):
        """
        Führt eine PID-Berechnung durch.
        :param setpoint: Sollwert
        :param input_value: Istwert
        :return: Stellwert (float)
        """
        self.pid.setpoint = 0  # Setpoint wird intern auf 0 gesetzt, Differenz wird direkt übergeben
        return self.pid(setpoint - input_value)  # PID-Berechnung basierend auf Abweichung

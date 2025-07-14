# controller/flow_calculator.py

class FlowCalculator:
    def __init__(self):
        """
        Konstruktor der Klasse zur Berechnung des Volumenstroms.
        Es wird eine Lookup-Tabelle verwendet, die den Zusammenhang zwischen PWM-Wert (%) und Volumenstrom (m³/h) beschreibt.
        """
        self.lookup_table = {
            0: 0.0,
            10: 50.0,
            20: 75.0,
            30: 100.0,
            40: 130.0,
            50: 160.0,
            60: 180.0,
            70: 210.0,
            80: 250.0,
            90: 280.0,
            100: 340.0,
        }
        # Schlüssel der Tabelle werden sortiert gespeichert, um später einfacher darauf zugreifen zu können
        self.keys = sorted(self.lookup_table)

    def interpolate(self, low, high, value):
        """
        Führt eine lineare Interpolation zwischen zwei bekannten PWM-Werten durch, um einen geschätzten Volumenstrom zu berechnen.

        :param low: Niedriger PWM-Wert (unterer Grenzwert des Intervalls)
        :param high: Höherer PWM-Wert (oberer Grenzwert des Intervalls)
        :param value: Der PWM-Wert, für den der Volumenstrom geschätzt werden soll
        :return: Interpolierter Volumenstromwert in m³/h
        """
        low_val = self.lookup_table[low]
        high_val = self.lookup_table[high]
        ratio = (value - low) / (high - low)  # Verhältnis innerhalb des Intervalls
        return low_val + ratio * (high_val - low_val)

    def get_flow(self, pwm_value):
        """
        Bestimmt den geschätzten Volumenstrom in m³/h basierend auf dem gegebenen PWM-Wert.
        Dabei wird entweder direkt ein Wert aus der Tabelle verwendet oder eine Interpolation durchgeführt.

        :param pwm_value: PWM-Wert in Prozent (0–100)
        :return: Geschätzter Volumenstrom in m³/h
        """
        # Falls PWM-Wert kleiner als kleinstes Tabellenintervall ist
        if pwm_value <= self.keys[0]:
            return self.lookup_table[self.keys[0]]

        # Falls PWM-Wert größer als größtes Tabellenintervall ist
        if pwm_value >= self.keys[-1]:
            return self.lookup_table[self.keys[-1]]

        # Suche das Intervall, in dem der PWM-Wert liegt und führe Interpolation durch
        for low, high in zip(self.keys, self.keys[1:]):
            if low <= pwm_value <= high:
                return self.interpolate(low, high, pwm_value)

        # Sollte eigentlich nie erreicht werden – Sicherheitsrückgabe
        return 0.0

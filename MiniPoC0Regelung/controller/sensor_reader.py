# controller/sensor_reader.py

import glob  # Zum Durchsuchen von Dateipfaden verwendet

class SensorReader:
    def __init__(self):
        """
        Konstruktor: Sucht nach dem ersten verfügbaren MAX31850K-Sensor.
        Wenn kein Sensor gefunden wird, wird self.device_file auf None gesetzt.
        """
        base_path = "/sys/bus/w1/devices/"  # Pfad zu 1-Wire Geräten im Dateisystem
        device_folders = glob.glob(base_path + "3b-*")  # MAX31850K Geräte beginnen mit "3b-"

        if not device_folders:
            print("[SensorReader] Kein MAX31850K Sensor gefunden.")
            self.device_file = None  # Kein Sensor vorhanden
        else:
            self.device_file = device_folders[0] + "/w1_slave"  # Pfad zur Gerätedatei
            print(f"[SensorReader] Sensor gefunden: {self.device_file}")

    def read_temperature(self):
        """
        Liest die Temperaturdaten vom Sensor und gibt den Wert in Grad Celsius zurück.
        Falls ein Fehler auftritt oder kein Sensor vorhanden ist, wird None zurückgegeben.
        """
        if not self.device_file:
            return None  # Kein Sensor vorhanden

        try:
            with open(self.device_file, 'r') as f:
                lines = f.readlines()  # Inhalt der Sensor-Datei einlesen

            # Prüfen, ob die Daten gültig sind (CRC-Prüfung bestanden)
            if lines[0].strip()[-3:] != 'YES':
                raise ValueError("CRC-Check fehlgeschlagen")

            # Suche nach der Temperaturangabe in der zweiten Zeile
            equals_pos = lines[1].find('t=')
            if equals_pos == -1:
                raise ValueError("Kein Temperaturwert gefunden")

            temp_string = lines[1][equals_pos + 2:]  # Extrahiere Temperaturwert als String
            temperature = float(temp_string) / 1000.0  # Umrechnung in Grad Celsius
            return temperature

        except Exception as e:
            # Fehlerbehandlung und Rückgabe von None bei Problemen
            print(f"[SensorReader] Fehler beim Lesen der Temperatur: {e}")
            return None

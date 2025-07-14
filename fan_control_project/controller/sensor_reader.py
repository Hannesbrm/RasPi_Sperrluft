# controller/sensor_reader.py

"""Modul zum Auslesen von MAX31850K Temperatursensoren."""

import os
from typing import List, Dict, Optional


class SensorReader:
    def __init__(self, sensor_ids: List[str]):
        """Initialisiert den SensorReader mit den gegebenen Sensor-IDs.

        Die IDs sollten den Verzeichnisnamen der Sensoren unter
        ``/sys/bus/w1/devices`` entsprechen (z.B. ``3b-000000abcd``).
        """
        self.sensor_ids = list(sensor_ids)
        self.device_files: List[Optional[str]] = []
        base_path = "/sys/bus/w1/devices"

        for sensor_id in self.sensor_ids:
            path = os.path.join(base_path, sensor_id, "w1_slave")
            if os.path.exists(path):
                self.device_files.append(path)
            else:
                self.device_files.append(None)
                print(f"[SensorReader] Sensor {sensor_id} nicht gefunden.")

    def _read_sensor_file(self, device_file: str) -> Optional[float]:
        """Liest die Temperatur aus einer w1_slave-Datei."""
        try:
            with open(device_file, "r") as f:
                lines = f.readlines()

            if lines[0].strip()[-3:] != "YES":
                raise ValueError("CRC-Check fehlgeschlagen")

            pos = lines[1].find("t=")
            if pos == -1:
                raise ValueError("Kein Temperaturwert gefunden")

            return float(lines[1][pos + 2:]) / 1000.0
        except Exception as exc:
            print(f"[SensorReader] Fehler beim Lesen der Temperatur: {exc}")
            return None

    def read_temperature(self, sensor_index: int) -> Optional[float]:
        """Gibt die Temperatur des Sensors mit dem gegebenen Index zurück."""
        if not (0 <= sensor_index < len(self.device_files)):
            print("[SensorReader] Ungültiger Sensorindex.")
            return None

        device_file = self.device_files[sensor_index]
        if device_file is None:
            return None
        return self._read_sensor_file(device_file)

    def read_all(self) -> Dict[str, Optional[float]]:
        """Liest alle konfigurierten Sensoren aus und gibt ihre Werte zurück."""
        result: Dict[str, Optional[float]] = {}
        for idx, sensor_id in enumerate(self.sensor_ids):
            result[sensor_id] = self.read_temperature(idx)
        return result

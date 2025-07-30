# controller/sensor_reader.py

"""Modul zum Auslesen von MAX31850K Temperatursensoren."""

import os
from typing import List, Dict, Optional, Tuple

from config.logging_config import logger


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
                logger.debug("Sensor %s gefunden", sensor_id)
            else:
                self.device_files.append(None)
                logger.warning("Sensor %s nicht gefunden", sensor_id)

    def _read_sensor_file(self, device_file: str) -> Tuple[Optional[float], str]:
        """Lies die Temperatur und den Status aus einer w1_slave-Datei.

        Die Temperatur wird immer zurückgegeben, sofern sie aus der Datei
        ausgelesen werden konnte. Fehlerbits im Status führen nicht mehr dazu,
        dass ``None`` zurückgegeben wird. Nur wenn kein Temperaturwert
        vorhanden ist oder ein unerwarteter Fehler auftritt, wird ``None`` als
        Temperatur geliefert.
        """

        try:
            with open(device_file, "r") as f:
                lines = f.readlines()

            if lines[0].strip()[-3:] != "YES":
                raise ValueError("CRC-Check fehlgeschlagen")

            # Zweite Zeile: Byte-Rohdaten und Temperatur
            raw_line = lines[1].strip()
            pos = raw_line.find("t=")
            if pos == -1:
                raise ValueError("Kein Temperaturwert gefunden")

            # Bytes vor "t=" analysieren
            raw_bytes = [int(b, 16) for b in raw_line[:pos].split()]
            # Laut MAX31850K Datenblatt liegen die Fehlerbits in Byte 3 (Index 2)
            status_byte = raw_bytes[2] if len(raw_bytes) > 2 else 0

            # Temperatur immer auslesen, unabhängig vom Status
            temperature = float(raw_line[pos + 2 :]) / 1000.0

            status = "ok"
            if status_byte & 0x01:
                logger.warning("Sensorfehler: Open Circuit")
                status = "open_circuit"
            elif status_byte & 0x02:
                logger.warning("Sensorfehler: Kurzschluss gegen GND")
                status = "short_gnd"
            elif status_byte & 0x04:
                logger.warning("Sensorfehler: Kurzschluss gegen VCC")
                status = "short_vcc"

            logger.debug("Gelesen %.2f °C mit Status %s", temperature, status)
            return temperature, status
        except Exception as exc:
            logger.error("Fehler beim Lesen der Temperatur: %s", exc)
            return None, "error"

    def read_temperature(self, sensor_index: int) -> Optional[float]:
        """Gibt die Temperatur des Sensors mit dem gegebenen Index zurück."""
        if not (0 <= sensor_index < len(self.device_files)):
            logger.warning("Ungueltiger Sensorindex: %s", sensor_index)
            return None

        device_file = self.device_files[sensor_index]
        if device_file is None:
            return None

        temperature, _ = self._read_sensor_file(device_file)
        return temperature

    def read_all(self) -> Dict[str, Dict[str, Optional[float] | str]]:
        """Liest alle Sensoren aus und gibt Temperatur und Status zurück."""

        result: Dict[str, Dict[str, Optional[float] | str]] = {}
        for idx, sensor_id in enumerate(self.sensor_ids):
            device_file = self.device_files[idx]
            if device_file is None:
                result[sensor_id] = {"temperature": None, "status": "not_found"}
                logger.warning("Sensor %s nicht gefunden", sensor_id)
                continue

            temperature, status = self._read_sensor_file(device_file)
            result[sensor_id] = {"temperature": temperature, "status": status}

        logger.debug("Sensorwerte: %s", result)

        return result

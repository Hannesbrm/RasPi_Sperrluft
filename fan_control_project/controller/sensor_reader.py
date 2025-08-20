"""Module zum Auslesen von MCP9600 Temperatursensoren über I2C."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import adafruit_mcp9600

from config.logging_config import logger


class SensorReader:
    """Liest Temperaturen von MCP9600 Sensoren."""

    def __init__(
        self,
        sensor_addresses: List[str | int],
        *,
        i2c: object | None = None,
        mcp_cls: type | None = None,
    ) -> None:
        """Initialisiere den Reader mit I2C-Adressen der Sensoren.

        Die Adressen können als Integer oder als hexadezimale Strings (z.B. "0x66")
        angegeben werden. Für Tests kann ein vorbereitetes ``I2C``-Objekt und eine
        alternative ``mcp_cls`` übergeben werden.
        """

        if i2c is None:
            import board
            import busio

            i2c = busio.I2C(board.SCL, board.SDA)

        self.i2c = i2c
        self.mcp_cls = mcp_cls or adafruit_mcp9600.MCP9600
        self.sensors: List[tuple[str, int, object | None]] = []
        for addr in sensor_addresses:
            if isinstance(addr, str):
                addr_int = int(addr, 16)
                addr_str = addr
            else:
                addr_int = int(addr)
                addr_str = f"0x{addr_int:02x}"
            sensor = self._create_sensor(addr_int)
            self.sensors.append((addr_str, addr_int, sensor))
        logger.debug("Sensoradressen initialisiert: %s", [(s[0], hex(s[1])) for s in self.sensors])

    def _create_sensor(self, address: int) -> object | None:
        """Erzeuge ein MCP9600-Objekt für die Adresse."""
        try:
            return self.mcp_cls(self.i2c, address=address)
        except OSError as exc:
            logger.error("Sensor %s nicht erreichbar: %s", hex(address), exc)
            return None
        except Exception as exc:  # pragma: no cover - unerwartete Fehler
            logger.error("Fehler beim Initialisieren des Sensors %s: %s", hex(address), exc)
            return None

    def _read_sensor(self, address: int, sensor: object | None) -> Tuple[Optional[float], str]:
        """Lese eine Temperatur vom angegebenen I2C-Sensor."""
        if sensor is None:
            return None, "not_found"
        try:
            temperature = float(sensor.temperature)
            logger.debug("Gelesen %.2f °C von Sensor %s", temperature, hex(address))
            return temperature, "ok"
        except OSError as exc:
            logger.error("Sensor %s nicht erreichbar: %s", hex(address), exc)
            return None, "not_found"
        except Exception as exc:  # pragma: no cover - unerwartete Fehler
            logger.error("Fehler beim Lesen des Sensors %s: %s", hex(address), exc)
            return None, "error"

    def read_temperature(self, sensor_index: int) -> Optional[float]:
        """Gibt die Temperatur des Sensors mit dem gegebenen Index zurück."""
        if not (0 <= sensor_index < len(self.sensors)):
            logger.warning("Ungueltiger Sensorindex: %s", sensor_index)
            return None
        _, address, sensor = self.sensors[sensor_index]
        temperature, _ = self._read_sensor(address, sensor)
        return temperature

    def read_all(self) -> Dict[str, Dict[str, Optional[float] | str]]:
        """Liest alle Sensoren aus und gibt Temperatur und Status zurück."""
        result: Dict[str, Dict[str, Optional[float] | str]] = {}
        for addr_str, address, sensor in self.sensors:
            temperature, status = self._read_sensor(address, sensor)
            result[addr_str] = {"temperature": temperature, "status": status}
        logger.debug("Sensorwerte: %s", result)
        return result

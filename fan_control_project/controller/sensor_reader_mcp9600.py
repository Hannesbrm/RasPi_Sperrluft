"""Read MCP9600 sensors via I2C."""

from typing import Dict, Optional, List

import board
import busio
import adafruit_mcp9600

from config.logging_config import logger


class SensorReaderMCP9600:
    """Reader for MCP9600 thermocouple sensors."""

    def __init__(self, addresses: Optional[List[int]] = None) -> None:
        if addresses is None:
            addresses = [0x60, 0x66]
        self.addresses = list(addresses)
        self.sensors: Dict[str, Optional[adafruit_mcp9600.MCP9600]] = {}
        try:
            self.i2c = busio.I2C(board.SCL, board.SDA)
        except Exception as exc:
            logger.warning("I2C initialisierung fehlgeschlagen: %s", exc)
            self.i2c = None

        if self.i2c is not None:
            for addr in self.addresses:
                name = f"mcp_{addr:02x}"
                try:
                    sensor = adafruit_mcp9600.MCP9600(self.i2c, address=addr)
                    self.sensors[name] = sensor
                    logger.debug("MCP9600 %s initialisiert", name)
                except Exception as exc:
                    self.sensors[name] = None
                    logger.warning(
                        "MCP9600 an Adresse 0x%02X nicht initialisiert: %s", addr, exc
                    )
        else:
            for addr in self.addresses:
                name = f"mcp_{addr:02x}"
                self.sensors[name] = None

    def read_all(self) -> Dict[str, Dict[str, Optional[float] | str]]:
        """Read all configured sensors."""

        result: Dict[str, Dict[str, Optional[float] | str]] = {}
        for name, sensor in self.sensors.items():
            if sensor is None:
                result[name] = {"temperature": None, "status": "error"}
                continue
            try:
                temperature = float(sensor.temperature)
                result[name] = {"temperature": temperature, "status": "ok"}
            except Exception as exc:
                logger.warning("Fehler beim Lesen von %s: %s", name, exc)
                result[name] = {"temperature": None, "status": "error"}

        logger.debug("MCP9600 Sensorwerte: %s", result)
        return result

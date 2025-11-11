"""Module zum Auslesen von MCP9600 Temperatursensoren über I2C."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import time

import adafruit_mcp9600

from config.logging_config import logger


@dataclass
class _SensorState:
    temperature: Optional[float] = None
    ambient: Optional[float] = None
    delta: Optional[float] = None
    status: str = "not_found"
    stale_count: int = 0


class SensorReader:
    """Liest Temperaturen von MCP9600 Sensoren."""

    def __init__(
        self,
        sensor_addresses: List[str | int],
        *,
        i2c: object | None = None,
        mcp_cls: type | None = None,
        mcp_params: Dict[str, Any] | None = None,
    ) -> None:
        """Initialisiere den Reader mit I2C-Adressen der Sensoren."""

        if i2c is None:
            import board
            import busio

            i2c = busio.I2C(board.SCL, board.SDA)

        self.i2c = i2c
        self.mcp_cls = mcp_cls or adafruit_mcp9600.MCP9600
        self.config: Dict[str, Any] = {
            "type": "K",
            "filter": 0,
            "conversion": "continuous",
            "data_rate": 8,
            "retries": 2,
            "backoff_ms": 50,
            "stale_threshold_count": 5,
        }
        if mcp_params:
            self.config.update(mcp_params)
        self.config["type"] = str(self.config.get("type", "K")).upper()
        logger.info("MCP9600 Konfiguration: %s", self.config)

        self.retries = int(self.config.get("retries", 0))
        self.backoff_ms = int(self.config.get("backoff_ms", 0))
        self.stale_threshold = int(self.config.get("stale_threshold_count", 5))

        self.sensors: List[tuple[str, int, object | None]] = []
        self._states: Dict[str, _SensorState] = {}

        for addr in sensor_addresses:
            if isinstance(addr, str):
                addr_int = int(addr, 16)
                addr_str = addr
            else:
                addr_int = int(addr)
                addr_str = f"0x{addr_int:02x}"
            sensor = self._create_sensor(addr_int)
            self.sensors.append((addr_str, addr_int, sensor))
            self._states[addr_str] = _SensorState(status="not_found" if sensor is None else "ok")
        logger.debug("Sensoradressen initialisiert: %s", [(s[0], hex(s[1])) for s in self.sensors])

    def set_thermocouple_type(self, tc_type: str) -> None:
        """Update the thermocouple type and recreate sensor instances."""

        tc = str(tc_type).upper()
        if tc == self.config.get("type"):
            logger.debug("Thermoelement-Typ unveraendert: %s", tc)
            return

        logger.info("Thermoelement-Typ wechselt von %s auf %s", self.config.get("type"), tc)
        self.config["type"] = tc

        for idx, (addr_str, addr_int, _sensor) in enumerate(self.sensors):
            sensor = self._create_sensor(addr_int)
            self.sensors[idx] = (addr_str, addr_int, sensor)
            state = self._states.setdefault(addr_str, _SensorState())
            if sensor is None:
                state.status = "not_found"
                state.temperature = None
                state.ambient = None
                state.delta = None
                state.stale_count = 0
            else:
                state.status = "ok"
                state.stale_count = 0

    # ------------------------------------------------------------------
    def _apply_config(self, sensor: Any) -> None:
        """Set configured parameters on the sensor instance."""
        if sensor is None:
            return
        try:
            # type and filter are set via constructor already
            if "conversion" in self.config and hasattr(sensor, "conversion_mode"):
                sensor.conversion_mode = self.config["conversion"]
            if "data_rate" in self.config and hasattr(sensor, "sample_rate"):
                sensor.sample_rate = self.config["data_rate"]
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Fehler beim Anwenden der MCP9600-Konfiguration: %s", exc)

    def _create_sensor(self, address: int) -> object | None:
        """Erzeuge ein MCP9600-Objekt für die Adresse."""
        try:
            sensor = self.mcp_cls(
                self.i2c,
                address=address,
                tctype=self.config.get("type", "K"),
                tcfilter=int(self.config.get("filter", 0)),
            )
            self._apply_config(sensor)
            return sensor
        except OSError as exc:
            logger.error("Sensor %s nicht erreichbar: %s", hex(address), exc)
            return None
        except Exception as exc:  # pragma: no cover - unerwartete Fehler
            logger.error("Fehler beim Initialisieren des Sensors %s: %s", hex(address), exc)
            return None

    # ------------------------------------------------------------------
    def _read_sensor(self, addr_str: str, address: int, sensor: object | None) -> _SensorState:
        """Lese eine Temperatur vom angegebenen I2C-Sensor."""
        state = self._states[addr_str]
        if sensor is None:
            state.status = "not_found"
            state.temperature = state.ambient = state.delta = None
            state.stale_count = 0
            return state

        attempt = 0
        start = time.perf_counter()
        while True:
            attempt += 1
            try:
                hot = float(getattr(sensor, "temperature"))
                cold = float(getattr(sensor, "ambient_temperature", 0.0))
                delta = hot - cold
                dt_ms = int((time.perf_counter() - start) * 1000)

                prev_status = state.status
                if state.temperature == hot:
                    state.stale_count += 1
                else:
                    state.stale_count = 1
                state.temperature = hot
                state.ambient = cold
                state.delta = delta
                state.status = "ok"
                if state.stale_count >= self.stale_threshold:
                    state.status = "stale"
                extra = {
                    "sensor_addr": addr_str,
                    "attempt": attempt,
                    "dt_ms": dt_ms,
                    "status": state.status,
                    "temp_hot": hot,
                    "temp_cold": cold,
                    "delta": delta,
                }
                if state.status != prev_status:
                    logger.info("Sensor gelesen", extra=extra)
                else:
                    logger.debug("Sensor gelesen", extra=extra)
                return state
            except OSError as exc:
                err = getattr(exc, "errno", exc.args[0] if exc.args else None)
                if err in {5, 121} and attempt <= self.retries:
                    backoff = self.backoff_ms * (2 ** (attempt - 1))
                    logger.debug(
                        "I2C Fehler %s an %s, retry in %sms", err, addr_str, backoff
                    )
                    time.sleep(backoff / 1000.0)
                    continue
                logger.error(
                    "Sensor %s nicht erreichbar: %s", addr_str, exc, extra={"sensor_addr": addr_str, "attempt": attempt}
                )
                state.status = "not_found"
                state.temperature = state.ambient = state.delta = None
                state.stale_count = 0
                return state
            except Exception as exc:  # pragma: no cover - unerwartete Fehler
                logger.error(
                    "Fehler beim Lesen des Sensors %s: %s", addr_str, exc, extra={"sensor_addr": addr_str, "attempt": attempt}
                )
                state.status = "error"
                state.temperature = state.ambient = state.delta = None
                state.stale_count = 0
                return state

    # ------------------------------------------------------------------
    def read_temperature(self, sensor_index: int) -> Optional[float]:
        """Gibt die Temperatur des Sensors mit dem gegebenen Index zurück."""
        if not (0 <= sensor_index < len(self.sensors)):
            logger.warning("Ungueltiger Sensorindex: %s", sensor_index)
            return None
        addr_str, address, sensor = self.sensors[sensor_index]
        state = self._read_sensor(addr_str, address, sensor)
        return state.temperature if state.status in {"ok", "stale"} else None

    def read_all(self) -> Dict[str, Dict[str, Optional[float] | str]]:
        """Liest alle Sensoren aus und gibt Temperatur und Status zurück."""
        result: Dict[str, Dict[str, Optional[float] | str]] = {}
        for addr_str, address, sensor in self.sensors:
            state = self._read_sensor(addr_str, address, sensor)
            result[addr_str] = {
                "temperature": state.temperature,
                "ambient": state.ambient,
                "delta": state.delta,
                "status": state.status,
            }
        logger.debug("Sensorwerte: %s", result)
        return result

    def scan_bus(self) -> List[str]:
        """Scan the I2C bus and return found addresses as hex strings."""
        try:
            addrs = getattr(self.i2c, "scan", lambda: [])()
            return [f"0x{a:02x}" for a in addrs]
        except Exception as exc:  # pragma: no cover - bus scan is best-effort
            logger.error("I2C-Scan fehlgeschlagen: %s", exc)
            return []

    def health(self) -> Dict[str, Dict[str, Optional[float] | str]]:
        """Return the last known sensor states."""
        return {
            addr: {
                "temperature": st.temperature,
                "ambient": st.ambient,
                "delta": st.delta,
                "status": st.status,
                "stale_count": st.stale_count,
            }
            for addr, st in self._states.items()
        }

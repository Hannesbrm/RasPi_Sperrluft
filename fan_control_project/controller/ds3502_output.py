"""DS3502-based fan output controller."""
from __future__ import annotations

import time
from dataclasses import dataclass

try:  # pragma: no cover - hardware only
    import smbus2
    _HAS_I2C = True
except Exception:  # pragma: no cover
    smbus2 = None  # type: ignore
    _HAS_I2C = False

from config.logging_config import logger


@dataclass
class DS3502Config:
    address: int = 0x28
    invert: bool = False
    wiper_min: int = 0
    wiper_max: int = 127
    slew_rate_pct_per_s: float = 0.0
    startup_percent: float = 0.0
    safe_low_on_fault: bool = True


class FanDS3502Controller:
    """Control the fan via an Adafruit DS3502 digipot."""

    def __init__(self, config: DS3502Config | None = None) -> None:
        self.cfg = config or DS3502Config()
        self.last_percent = self.cfg.startup_percent
        self.last_update = time.monotonic()
        self.available = False
        self.bus = None
        if _HAS_I2C:
            try:
                self.bus = smbus2.SMBus(1)
                self.bus.read_byte(self.cfg.address)
                self.available = True
            except Exception:  # pragma: no cover - hardware error
                logger.error(
                    "DS3502 nicht erreichbar", extra={"actuator": "ds3502", "addr": hex(self.cfg.address)}
                )
        logger.info(
            "DS3502 initialisiert", extra={
                "actuator": "ds3502",
                "addr": hex(self.cfg.address),
                "output_pct": self.last_percent,
                "wiper": self._percent_to_wiper(self.last_percent),
                "slew_applied": False,
            },
        )
        if self.available:
            self._write_wiper(self.last_percent)

    # ----------------------------- internal helpers -----------------
    def _percent_to_wiper(self, percent: float) -> int:
        pct = max(0.0, min(100.0, percent))
        if self.cfg.invert:
            pct = 100.0 - pct
        span = self.cfg.wiper_max - self.cfg.wiper_min
        wiper = self.cfg.wiper_min + int(round(pct / 100.0 * span))
        return max(self.cfg.wiper_min, min(self.cfg.wiper_max, wiper))

    def _write_wiper(self, percent: float) -> None:
        wiper = self._percent_to_wiper(percent)
        if self.available and self.bus:
            try:
                self.bus.write_byte_data(self.cfg.address, 0x00, wiper)
            except Exception:  # pragma: no cover - hardware error
                logger.error(
                    "DS3502 Write-Fehler",
                    extra={"actuator": "ds3502", "addr": hex(self.cfg.address)},
                )
                if self.cfg.safe_low_on_fault:
                    wiper = self._percent_to_wiper(0.0)
                    try:
                        self.bus.write_byte_data(self.cfg.address, 0x00, wiper)
                    except Exception:
                        pass
        logger.debug(
            "DS3502 Wiper gesetzt",
            extra={
                "actuator": "ds3502",
                "addr": hex(self.cfg.address),
                "output_pct": percent,
                "wiper": wiper,
                "slew_applied": False,
                "dt_ms": 0,
            },
        )

    # ----------------------------- public API -----------------------
    def set_output(self, percent: float) -> None:
        now = time.monotonic()
        dt = now - self.last_update
        target = max(0.0, min(100.0, percent))
        slew_applied = False
        if self.cfg.slew_rate_pct_per_s > 0:
            max_delta = self.cfg.slew_rate_pct_per_s * dt
            delta = target - self.last_percent
            if abs(delta) > max_delta:
                slew_applied = True
                target = self.last_percent + max_delta if delta > 0 else self.last_percent - max_delta
        self.last_percent = target
        self.last_update = now
        wiper = self._percent_to_wiper(target)
        if self.available:
            self._write_wiper(target)
        else:
            logger.debug(
                "DS3502 Dummy-Ausgabe",
                extra={
                    "actuator": "ds3502",
                    "addr": hex(self.cfg.address),
                    "output_pct": target,
                    "wiper": wiper,
                    "slew_applied": slew_applied,
                    "dt_ms": int(dt * 1000),
                },
            )

    def stop(self) -> None:
        self.set_output(0.0)

    def save_as_default(self) -> None:  # pragma: no cover - hardware only
        if self.available and self.bus:
            try:
                self.bus.write_byte_data(self.cfg.address, 0x40, self._percent_to_wiper(self.last_percent))
            except Exception:
                logger.error(
                    "DS3502 EEPROM-Write fehlgeschlagen",
                    extra={"actuator": "ds3502", "addr": hex(self.cfg.address)},
                )

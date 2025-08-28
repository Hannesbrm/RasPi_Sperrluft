"""DS3502-based fan output controller."""
from __future__ import annotations

import errno
import threading
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
    address: int | str = 0x28
    invert: bool = False
    wiper_min: int = 2
    wiper_max: int = 125
    slew_rate_pct_per_s: float = 0.0
    startup_percent: float = 0.0
    safe_low_on_fault: bool = True


class FanDS3502Controller:
    """Control the fan via an Adafruit DS3502 digipot."""

    def __init__(self, config: DS3502Config | None = None) -> None:
        self.cfg = config or DS3502Config()
        # allow hex strings or ints
        if isinstance(self.cfg.address, str):
            try:
                self.cfg.address = int(self.cfg.address, 0)
            except ValueError:
                self.cfg.address = int(self.cfg.address, 16)
        self.last_percent = self.cfg.startup_percent
        self.last_update = time.monotonic()
        self.available = False
        self.bus = None
        self._lock = threading.Lock()
        self._last_wiper: int | None = None
        if _HAS_I2C:
            try:
                self.bus = smbus2.SMBus(1)
                # light presence check via register read
                self.bus.read_byte_data(self.cfg.address, 0x00)
                # set MODE=WR-only to avoid EEPROM writes
                self.bus.write_byte_data(self.cfg.address, 0x02, 0x80)
                self.available = True
            except Exception:  # pragma: no cover - hardware error
                logger.error(
                    "DS3502 nicht erreichbar",
                    extra={"actuator": "ds3502", "addr": hex(int(self.cfg.address))},
                )
        logger.info(
            "DS3502 initialisiert",
            extra={
                "actuator": "ds3502",
                "addr": hex(int(self.cfg.address)),
                "output_pct": self.last_percent,
                "wiper": self._percent_to_wiper(self.last_percent),
                "slew_applied": False,
            },
        )
        if self.available:
            self._write_wiper(self.last_percent, False, 0)

    # ----------------------------- internal helpers -----------------
    def _percent_to_wiper(self, percent: float) -> int:
        pct = max(0.0, min(100.0, percent))
        if self.cfg.invert:
            pct = 100.0 - pct
        span = self.cfg.wiper_max - self.cfg.wiper_min
        wiper = self.cfg.wiper_min + int(round(pct / 100.0 * span))
        wiper = max(self.cfg.wiper_min, min(self.cfg.wiper_max, wiper))
        return max(0, min(127, wiper))

    def _write_wiper(self, percent: float, slew_applied: bool, dt_ms: int) -> None:
        wiper = self._percent_to_wiper(percent)
        if not (self.available and self.bus):
            return
        if self._last_wiper == wiper:
            return
        attempt = 0
        start = time.monotonic()
        with self._lock:
            while True:
                attempt += 1
                try:
                    self.bus.write_byte_data(self.cfg.address, 0x00, wiper)
                    self._last_wiper = wiper
                    elapsed = int((time.monotonic() - start) * 1000)
                    logger.debug(
                        "DS3502 Wiper gesetzt",
                        extra={
                            "actuator": "ds3502",
                            "addr": hex(self.cfg.address),
                            "reg": 0x00,
                            "wiper": wiper,
                            "attempt": attempt,
                            "errno": 0,
                            "output_pct": percent,
                            "slew_applied": slew_applied,
                            "dt_ms": dt_ms,
                            "duration_ms": elapsed,
                        },
                    )
                    return
                except OSError as exc:  # pragma: no cover - hardware error
                    err = exc.errno or 0
                    elapsed = int((time.monotonic() - start) * 1000)
                    logger.warning(
                        "DS3502 Write-Fehler",
                        extra={
                            "actuator": "ds3502",
                            "addr": hex(self.cfg.address),
                            "reg": 0x00,
                            "wiper": wiper,
                            "attempt": attempt,
                            "errno": err,
                            "output_pct": percent,
                            "slew_applied": slew_applied,
                            "dt_ms": dt_ms,
                            "duration_ms": elapsed,
                        },
                    )
                    if err not in (errno.EREMOTEIO, errno.EIO) or attempt >= 3:
                        if self.cfg.safe_low_on_fault:
                            time.sleep(0.01)
                            try:
                                self.bus.write_byte_data(self.cfg.address, 0x00, self._percent_to_wiper(0.0))
                            except Exception:
                                pass
                        return
                    time.sleep(0.002 * (2 ** (attempt - 1)))

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
        dt_ms = int(dt * 1000)
        if self.available:
            self._write_wiper(target, slew_applied, dt_ms)
        else:
            logger.debug(
                "DS3502 Dummy-Ausgabe",
                extra={
                    "actuator": "ds3502",
                    "addr": hex(self.cfg.address),
                    "reg": 0x00,
                    "wiper": wiper,
                    "attempt": 0,
                    "errno": 0,
                    "output_pct": target,
                    "slew_applied": slew_applied,
                    "dt_ms": dt_ms,
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

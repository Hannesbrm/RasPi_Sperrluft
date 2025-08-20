import json
import logging
import os
from collections import deque
from typing import Callable

__all__ = ["logger", "log_buffer", "set_log_callback"]


class JsonFormatter(logging.Formatter):
    """Format log records as JSON strings."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401 - simple override
        data: dict[str, object] = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname.lower(),
            "name": record.name,
            "message": record.getMessage(),
        }
        for key in (
            "sensor_addr",
            "attempt",
            "dt_ms",
            "status",
            "temp_hot",
            "temp_cold",
            "delta",
        ):
            if hasattr(record, key):
                data[key] = getattr(record, key)
        return json.dumps(data)


level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=level)

logger = logging.getLogger("fan_control")

log_buffer: deque[dict[str, object]] = deque(maxlen=200)


_log_callback: "Callable[[dict[str, object]], None] | None" = None


def set_log_callback(cb: "Callable[[dict[str, object]], None] | None") -> None:
    """Register a callback that is invoked for each new log entry."""
    global _log_callback
    _log_callback = cb


class WebLogHandler(logging.Handler):
    """Handler that stores logs in a deque for web display."""

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        try:
            entry = json.loads(msg)
        except json.JSONDecodeError:
            entry = {"level": record.levelname.lower(), "message": msg}
        log_buffer.append(entry)
        if _log_callback:
            _log_callback(entry)


_json_formatter = JsonFormatter()
for handler in logging.getLogger().handlers:
    handler.setFormatter(_json_formatter)

_web_handler = WebLogHandler()
_web_handler.setFormatter(_json_formatter)
logger.addHandler(_web_handler)

import logging
from collections import deque

__all__ = ["logger", "log_buffer"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("fan_control")

log_buffer: deque[dict[str, str]] = deque(maxlen=200)


class WebLogHandler(logging.Handler):
    """Handler that stores logs in a deque for web display."""

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        entry = {"level": record.levelname.lower(), "message": msg}
        log_buffer.append(entry)


_web_handler = WebLogHandler()
_web_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(_web_handler)

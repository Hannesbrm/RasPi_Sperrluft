import os
import yaml
from typing import Any, Dict

from .logging_config import logger

CONFIG_YAML_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")

DEFAULT_YAML: Dict[str, Any] = {
    "sensor_type": "max31850",
    "sensor_ids": {},
    "sensor_addresses": [0x60],
}


def load_hardware_config() -> Dict[str, Any]:
    """Load config.yaml for sensor selection."""
    if not os.path.exists(CONFIG_YAML_PATH):
        try:
            with open(CONFIG_YAML_PATH, "w", encoding="utf-8") as f:
                yaml.safe_dump(DEFAULT_YAML, f)
            logger.info("Neue config.yaml erstellt unter %s", CONFIG_YAML_PATH)
        except OSError as exc:
            logger.error("config.yaml konnte nicht erstellt werden: %s", exc)
    try:
        with open(CONFIG_YAML_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        logger.debug("Hardware-Konfiguration geladen: %s", data)
        return data
    except Exception as exc:
        logger.error("config.yaml konnte nicht geladen werden: %s", exc)
        return {}

import os
import yaml
from typing import Any, Dict, List

from .logging_config import logger

CONFIG_YAML_PATH = os.path.join(os.path.dirname(__file__), "hardware_config.yaml")

DEFAULT_YAML: Dict[str, Any] = {
    "sensor_type": "max31850",
    "sensor_ids": {},
    "sensor_addresses": [],
}


def _format_addresses_for_dump(addresses: List[int] | List[str]) -> List[str]:
    """Return a list of addresses formatted as hex strings."""
    formatted: List[str] = []
    for addr in addresses:
        try:
            value = int(str(addr), 0)
            formatted.append(f"0x{value:02x}")
        except Exception:
            formatted.append(str(addr))
    return formatted


def _save_yaml(data: Dict[str, Any]) -> None:
    """Write the configuration to disk with nicely formatted addresses."""
    dump_data = data.copy()
    addrs = dump_data.get("sensor_addresses", [])
    if isinstance(addrs, list):
        dump_data["sensor_addresses"] = _format_addresses_for_dump(addrs)
    with open(CONFIG_YAML_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(dump_data, f, sort_keys=False)


def load_hardware_config() -> Dict[str, Any]:
    """Load the YAML configuration for sensor selection."""

    if not os.path.exists(CONFIG_YAML_PATH):
        try:
            _save_yaml(DEFAULT_YAML)
            logger.info("Neue hardware_config.yaml erstellt unter %s", CONFIG_YAML_PATH)
        except OSError as exc:
            logger.error("%s konnte nicht erstellt werden: %s", CONFIG_YAML_PATH, exc)

    try:
        with open(CONFIG_YAML_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception as exc:
        logger.error("%s konnte nicht geladen werden: %s", CONFIG_YAML_PATH, exc)
        data = {}

    changed = False
    for key, default in DEFAULT_YAML.items():
        if key not in data:
            data[key] = default
            changed = True

    # Normalize addresses to integers for internal use
    addresses = data.get("sensor_addresses", [])
    if not isinstance(addresses, list):
        addresses = []
        changed = True
    int_addrs: List[int] = []
    for addr in addresses:
        try:
            int_addrs.append(int(str(addr), 0))
        except Exception:
            logger.warning("Ungueltige Adresse %s in %s", addr, CONFIG_YAML_PATH)
    data["sensor_addresses"] = int_addrs

    if changed:
        logger.info("Hardware-Konfiguration aktualisiert: %s", data)
    else:
        logger.debug("Hardware-Konfiguration geladen: %s", data)

    # Always write back to ensure consistent formatting
    _save_yaml(data)
    return data

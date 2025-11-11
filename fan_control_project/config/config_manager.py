import json
import os
from typing import Any, Dict

from config.logging_config import logger

from models.system_state import SystemState

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "settings.json")

DEFAULT_CONFIG: Dict[str, Any] = {
    "setpoint": 0.0,
    "alarm_threshold": 0.0,
    "manual_percent": 0.0,
    "alarm_percent": 100.0,
    "ds3502": {
        "address": "0x28",
        "invert": False,
        "wiper_min": 2,
        "wiper_max": 125,
        "slew_rate_pct_per_s": 30,
        "startup_percent": 0,
        "safe_low_on_fault": True,
    },
    "kp": 1.0,
    "ki": 0.1,
    "kd": 0.0,
    "postrun_seconds": 30.0,
    "swap_sensors": False,
    # I2C sensor addresses as hex strings
    "sensor_addresses": ["0x66", "0x67"],
    # Default configuration for the MCP9600 sensors
    "mcp9600": {
        "type": "K",
        "filter": 0,
        "conversion": "continuous",
        "data_rate": 8,
        "retries": 2,
        "backoff_ms": 50,
        "stale_threshold_count": 5,
    },
}


def _ensure_file_exists() -> None:
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        logger.info("Neue Konfigurationsdatei erstellt unter %s", CONFIG_PATH)


def load_config() -> Dict[str, Any]:
    """Load the configuration file and return its contents."""
    _ensure_file_exists()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)
        logger.debug("Konfiguration geladen: %s", data)
    except (OSError, json.JSONDecodeError):
        data = DEFAULT_CONFIG.copy()
        logger.warning("Konfiguration konnte nicht geladen werden, Standardwerte verwendet")

    changed = False
    for key, default in DEFAULT_CONFIG.items():
        if key not in data:
            data[key] = default
            changed = True
        elif isinstance(default, dict):
            current = data.get(key, {})
            if not isinstance(current, dict):
                data[key] = default
                changed = True
            else:
                for sub_key, sub_val in default.items():
                    if sub_key not in current:
                        current[sub_key] = sub_val
                        changed = True

    if changed:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info("Konfiguration aktualisiert: %s", data)

    return data


def save_config(state: SystemState) -> None:
    """Persist selected values from the given state to the config file."""
    data = load_config()
    data["setpoint"] = state.setpoint
    data["alarm_threshold"] = state.alarm_threshold
    data["manual_percent"] = state.manual_percent
    if hasattr(state, "alarm_percent"):
        data["alarm_percent"] = state.alarm_percent
    if hasattr(state, "kp"):
        data["kp"] = state.kp
    if hasattr(state, "ki"):
        data["ki"] = state.ki
    if hasattr(state, "kd"):
        data["kd"] = state.kd
    if hasattr(state, "postrun_seconds"):
        data["postrun_seconds"] = state.postrun_seconds
    if hasattr(state, "swap_sensors"):
        data["swap_sensors"] = state.swap_sensors
    if hasattr(state, "wiper_min"):
        ds_cfg = data.get("ds3502", {})
        ds_cfg["wiper_min"] = int(state.wiper_min)
        data["ds3502"] = ds_cfg
    if hasattr(state, "thermocouple_type"):
        mcp_cfg = data.get("mcp9600", {})
        if not isinstance(mcp_cfg, dict):
            mcp_cfg = {}
        mcp_cfg["type"] = str(state.thermocouple_type).upper()
        data["mcp9600"] = mcp_cfg
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info("Konfiguration gespeichert: %s", data)

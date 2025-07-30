import json
import os
from typing import Any, Dict

from config.logging_config import logger

from models.system_state import SystemState

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "settings.json")

DEFAULT_CONFIG: Dict[str, Any] = {
    "setpoint": 0.0,
    "alarm_threshold": 0.0,
    "manual_pwm": 0.0,
    "alarm_pwm": 100.0,
    "min_pwm": 20.0,
    "pwm_pin": 12,
    "kp": 1.0,
    "ki": 0.1,
    "kd": 0.0,
    "postrun_seconds": 30.0,
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
    data["manual_pwm"] = state.manual_pwm
    if hasattr(state, "alarm_pwm"):
        data["alarm_pwm"] = state.alarm_pwm
    if hasattr(state, "min_pwm"):
        data["min_pwm"] = state.min_pwm
    if hasattr(state, "kp"):
        data["kp"] = state.kp
    if hasattr(state, "ki"):
        data["ki"] = state.ki
    if hasattr(state, "kd"):
        data["kd"] = state.kd
    if hasattr(state, "postrun_seconds"):
        data["postrun_seconds"] = state.postrun_seconds
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info("Konfiguration gespeichert: %s", data)

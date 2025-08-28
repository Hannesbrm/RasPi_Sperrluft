from __future__ import annotations

"""Simple Flask server exposing live fan data via Socket.IO."""

from threading import Event
from typing import Any, Callable, Dict
import os
import time

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

from config.logging_config import logger, log_buffer, set_log_callback

from models.system_state import SystemState, Mode
from config import save_config
from controller.pid_controller import PIDController
from controller.sensor_reader import SensorReader
from controller.ds3502_output import FanDS3502Controller

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
)
app.config["SECRET_KEY"] = "secret"

# Flask-SocketIO setup using threading async mode (works without eventlet)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")


def _emit_log(entry: Dict[str, Any]) -> None:
    """Forward log entries to connected web clients."""
    socketio.emit("log_entry", entry)


set_log_callback(_emit_log)

# Global state object that would normally be updated by a control loop
state = SystemState()

# Reference to the PID controller (set by app.py)
pid_controller: PIDController | None = None
sensor_reader: SensorReader | None = None
actuator: FanDS3502Controller | None = None

# Event used to stop the background thread when the app shuts down
_stop_event = Event()


def register_state_handler(
    event_name: str, state_attr: str, cast_func: Callable[[Any], Any] = float
) -> None:
    """Register a simple Socket.IO handler that updates ``state`` attributes."""

    default = False if cast_func is bool else 0

    @socketio.on(event_name)
    def _handler(data: Dict[str, Any]) -> None:
        value = cast_func(data.get("value", default))
        setattr(state, state_attr, value)
        save_config(state)
        logger.info("%s geaendert auf %s", state_attr, value)

def _broadcast_state() -> None:
    """Send the current system state to all connected clients periodically."""
    while not _stop_event.is_set():
        socketio.emit("state_update", state.as_dict())
        socketio.sleep(1)


@socketio.on("connect")
def handle_connect() -> None:
    """Send initial state when a client connects."""
    logger.info("Client verbunden")
    emit("state_update", state.as_dict())


# Simple state update handlers
register_state_handler("set_setpoint", "setpoint")
register_state_handler("set_manual_percent", "manual_percent")
register_state_handler("set_alarm_percent", "alarm_percent")
register_state_handler("set_alarm_threshold", "alarm_threshold")
register_state_handler("set_swap_sensors", "swap_sensors", bool)
register_state_handler("set_postrun_seconds", "postrun_seconds")


@socketio.on("set_wiper_min")
def handle_set_wiper_min(data: Dict[str, Any]) -> None:
    value = int(data.get("value", state.wiper_min))
    state.wiper_min = value
    save_config(state)
    if actuator is not None:
        actuator.cfg.wiper_min = value
        actuator.set_output(actuator.last_percent)
    logger.info("wiper_min geaendert auf %s", value)


@socketio.on("set_mode")
def handle_set_mode(data: Dict[str, Any]) -> None:
    mode = data.get("mode")
    if mode in ("auto", "manual"):
        state.mode = Mode(mode)
        logger.info("Modus geaendert auf %s", mode)


@socketio.on("set_pid_params")
def handle_set_pid_params(data: Dict[str, Any]) -> None:
    """Update PID controller parameters."""
    kp = float(data.get("kp", state.kp))
    ki = float(data.get("ki", state.ki))
    kd = float(data.get("kd", state.kd))
    state.kp = kp
    state.ki = ki
    state.kd = kd
    if pid_controller is not None:
        pid_controller.pid.tunings = (kp, ki, kd)
    save_config(state)
    logger.info(
        "PID-Parameter geaendert: kp=%s ki=%s kd=%s",
        kp,
        ki,
        kd,
    )


@socketio.on("request_logs")
def handle_request_logs() -> None:
    """Send the current log buffer to the requesting client."""
    emit("logs_update", list(log_buffer))


@socketio.on("scan_i2c")
def handle_scan_i2c() -> None:
    """Trigger an I2C bus scan and return the result."""
    if sensor_reader is None:
        logger.warning("I2C-Scan angefordert, aber kein SensorReader vorhanden")
        emit("scan_result", [])
        return
    logger.info("Starte I2C-Scan")
    addrs = sensor_reader.scan_bus()
    logger.info("I2C-Scan abgeschlossen: %s", addrs)
    emit("scan_result", addrs)


@socketio.on("test_measure")
def handle_test_measure() -> None:
    """Perform a one-off measurement and return raw data."""
    if sensor_reader is None:
        logger.warning("Testmessung angefordert, aber kein SensorReader vorhanden")
        emit("test_measure_result", {})
        return
    logger.info("Starte Testmessung")
    data = sensor_reader.read_all()
    logger.info("Testmessung Ergebnis: %s", data)
    emit("test_measure_result", data)


@socketio.on("request_reboot")
def handle_request_reboot() -> None:
    """Handle a reboot request from the client."""
    ip = request.remote_addr or ""
    if ip and not ip.startswith("192.168."):
        logger.warning("Reboot request denied from IP %s", ip)
        emit("reboot_ack", {"status": "denied"})
        return

    emit("reboot_ack", {"status": "ok"})

    def _delayed_reboot() -> None:
        time.sleep(1)
        os.system("sudo reboot")

    socketio.start_background_task(_delayed_reboot)


@app.route("/")
def index() -> str:
    """Serve the main page."""
    return render_template("index.html")


def main() -> None:
    """Entry point for running the server."""
    logger.info("Starte Webserver")
    socketio.start_background_task(_broadcast_state)
    try:
        socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)
    finally:
        _stop_event.set()
        logger.info("Webserver gestoppt")


if __name__ == "__main__":
    main()

from __future__ import annotations

"""Simple Flask server exposing live fan data via Socket.IO."""

from threading import Event
from typing import Any, Dict

from flask import Flask, render_template
from flask_socketio import SocketIO, emit

from models.system_state import SystemState, Mode
from config import save_config
from controller.pid_controller import PIDController

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
)
app.config["SECRET_KEY"] = "secret"

# Flask-SocketIO setup using threading async mode (works without eventlet)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Global state object that would normally be updated by a control loop
state = SystemState()

# Reference to the PID controller (set by app.py)
pid_controller: PIDController | None = None

# Event used to stop the background thread when the app shuts down
_stop_event = Event()

def _broadcast_state() -> None:
    """Send the current system state to all connected clients periodically."""
    while not _stop_event.is_set():
        socketio.emit("state_update", state.to_dict())
        socketio.sleep(1)


@socketio.on("connect")
def handle_connect() -> None:
    """Send initial state when a client connects."""
    emit("state_update", state.to_dict())


@socketio.on("set_setpoint")
def handle_set_setpoint(data: Dict[str, Any]) -> None:
    value = float(data.get("value", 0))
    state.setpoint = value
    save_config(state)


@socketio.on("set_mode")
def handle_set_mode(data: Dict[str, Any]) -> None:
    mode = data.get("mode")
    if mode in ("auto", "manual"):
        state.mode = Mode(mode)


@socketio.on("set_manual_pwm")
def handle_set_manual_pwm(data: Dict[str, Any]) -> None:
    value = float(data.get("value", 0))
    state.manual_pwm = value
    save_config(state)


@socketio.on("set_alarm_threshold")
def handle_set_alarm_threshold(data: Dict[str, Any]) -> None:
    """Update the alarm temperature threshold."""
    value = float(data.get("value", 0))
    state.alarm_threshold = value
    save_config(state)


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


@app.route("/")
def index() -> str:
    """Serve the main page."""
    return render_template("index.html")


def main() -> None:
    """Entry point for running the server."""
    socketio.start_background_task(_broadcast_state)
    try:
        socketio.run(app, host="0.0.0.0", port=5000)
    finally:
        _stop_event.set()


if __name__ == "__main__":
    main()

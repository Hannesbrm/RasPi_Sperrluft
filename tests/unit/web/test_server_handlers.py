"""Tests for web server handlers and routes."""

from web import server
from models.system_state import Mode
from config.logging_config import log_buffer


def test_set_setpoint_updates_state(socketio_client, state, no_save_config):
    socketio_client.emit("set_setpoint", {"value": 35})
    socketio_client.get_received()
    assert state.setpoint == 35


def test_index_route(app_client, no_save_config):
    resp = app_client.get("/")
    assert resp.status_code == 200
    assert b"<html" in resp.data


def test_set_mode_handler(socketio_client, state):
    socketio_client.emit("set_mode", {"mode": "manual"})
    socketio_client.get_received()
    assert state.mode is Mode.MANUAL


def test_set_pid_params_handler(socketio_client, state, no_save_config, monkeypatch):
    class DummyPID:
        def __init__(self):
            self.pid = type("P", (), {"tunings": None})()

    server.pid_controller = DummyPID()
    socketio_client.emit("set_pid_params", {"kp": 2, "ki": 3, "kd": 4})
    socketio_client.get_received()
    assert state.kp == 2 and server.pid_controller.pid.tunings == (2.0, 3.0, 4.0)
    server.pid_controller = None


def test_request_logs_handler(socketio_client):
    log_buffer.clear()
    log_buffer.append({"message": "entry", "level": "info"})
    socketio_client.emit("request_logs")
    received = socketio_client.get_received()
    assert any(p["name"] == "logs_update" and p["args"][0] == [{"message": "entry", "level": "info"}] for p in received)


def test_request_reboot_denied(monkeypatch):
    emitted = {}
    monkeypatch.setattr(server, "emit", lambda event, data: emitted.update({event: data}))
    monkeypatch.setattr(server, "request", type("Req", (), {"remote_addr": "10.0.0.1"})())
    server.handle_request_reboot()
    assert emitted["reboot_ack"]["status"] == "denied"


def test_request_reboot_allowed(monkeypatch):
    emitted = {}
    monkeypatch.setattr(server, "emit", lambda e, d: emitted.update({e: d}))
    monkeypatch.setattr(server, "request", type("Req", (), {"remote_addr": "192.168.0.5"})())
    cmd = []
    monkeypatch.setattr(server.os, "system", lambda c: cmd.append(c))
    monkeypatch.setattr(server.time, "sleep", lambda s: None)
    monkeypatch.setattr(server.socketio, "start_background_task", lambda f: f())
    server.handle_request_reboot()
    assert emitted["reboot_ack"] == {"status": "ok"}
    assert cmd == ["sudo reboot"]


def test_broadcast_state_emits_once(monkeypatch, state):
    emitted = []
    ev = server.Event()
    monkeypatch.setattr(server, "_stop_event", ev)
    monkeypatch.setattr(server.socketio, "emit", lambda e, d: emitted.append((e, d)))
    monkeypatch.setattr(server.socketio, "sleep", lambda s: ev.set())
    server._broadcast_state()
    assert emitted and emitted[0][0] == "state_update"


def test_main_runs_and_stops(monkeypatch, state):
    ev = server.Event()
    monkeypatch.setattr(server, "_stop_event", ev)
    monkeypatch.setattr(server.socketio, "start_background_task", lambda f: None)
    monkeypatch.setattr(server.socketio, "run", lambda *a, **k: None)
    server.main()
    assert ev.is_set()

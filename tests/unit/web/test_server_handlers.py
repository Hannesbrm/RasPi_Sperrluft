"""Tests for web server handlers and routes."""

from web import server
from config import config_manager


def test_set_setpoint_updates_state(socketio_client, state, monkeypatch):
    monkeypatch.setattr(config_manager, "save_config", lambda s: None)
    socketio_client.emit("set_setpoint", {"value": 35})
    socketio_client.get_received()
    assert state.setpoint == 35


def test_index_route(app_client, monkeypatch):
    monkeypatch.setattr(config_manager, "save_config", lambda s: None)
    resp = app_client.get("/")
    assert resp.status_code == 200
    assert b"<html" in resp.data

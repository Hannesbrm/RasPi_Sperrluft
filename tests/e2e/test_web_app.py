"""End-to-end tests using the Flask and Socket.IO stack."""


def test_state_update_on_connect(socketio_client):
    received = socketio_client.get_received()
    assert any(packet["name"] == "state_update" for packet in received)


def test_set_mode_event(socketio_client, state):
    socketio_client.emit("set_mode", {"mode": "manual"})
    socketio_client.get_received()
    assert state.mode.value == "manual"


def test_set_pid_params_event(socketio_client, state, no_save_config):
    from web import server

    class DummyPID:
        def __init__(self):
            self.pid = type("P", (), {"tunings": None})()

    server.pid_controller = DummyPID()
    socketio_client.emit("set_pid_params", {"kp": 5, "ki": 6, "kd": 7})
    socketio_client.get_received()
    assert state.kp == 5
    assert server.pid_controller.pid.tunings == (5.0, 6.0, 7.0)
    server.pid_controller = None

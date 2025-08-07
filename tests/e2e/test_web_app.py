"""End-to-end tests using the Flask and Socket.IO stack."""


def test_state_update_on_connect(socketio_client):
    received = socketio_client.get_received()
    assert any(packet["name"] == "state_update" for packet in received)

"""Tests for the dummy SensorReader implementation."""

from controller import sensor_reader_dummy as dummy


def test_dummy_reader_returns_distinct_values():
    reader = dummy.SensorReader(["id1", "id2"])
    assert reader.read_temperature(0) == 25.0
    assert reader.read_temperature(1) == 26.0
    assert reader._read_sensor_file("ignored") == 25.0
    data = reader.read_all()
    assert data["id1"]["temperature"] == 25.0
    assert data["id2"]["status"] == "ok"


def test_dummy_reader_invalid_index():
    reader = dummy.SensorReader(["id1"])
    assert reader.read_temperature(5) is None

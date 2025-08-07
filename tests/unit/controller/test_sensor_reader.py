"""Tests for the sensor_reader module."""

from pathlib import Path

from controller.sensor_reader import SensorReader


def _create_sensor(tmp_path: Path, sensor_id: str, temperature: float) -> None:
    sensor_dir = tmp_path / sensor_id
    sensor_dir.mkdir()
    content = (
        "00 00 00 00 00 00 00 00 00 00 : crc=00 YES\n"
        f"00 00 00 00 00 00 00 00 00 00 t={int(temperature * 1000)}\n"
    )
    (sensor_dir / "w1_slave").write_text(content)


def test_read_temperature(tmp_path: Path) -> None:
    _create_sensor(tmp_path, "3b-000000000001", 21.5)
    reader = SensorReader(["3b-000000000001"], base_path=tmp_path)
    assert reader.read_temperature(0) == 21.5


def test_read_all_missing_sensor(tmp_path: Path) -> None:
    _create_sensor(tmp_path, "3b-000000000001", 21.5)
    reader = SensorReader(["3b-000000000001", "3b-does-not-exist"], base_path=tmp_path)
    result = reader.read_all()
    assert result["3b-000000000001"]["temperature"] == 21.5
    assert result["3b-does-not-exist"]["temperature"] is None
    assert result["3b-does-not-exist"]["status"] == "not_found"
